#!/usr/bin/env python3
"""
NexusIntel 新闻自动更新脚本
每日抓取财经/科技新闻，使用 Gemini API 进行深度分析，生成 data.json
"""

import os
import json
import random
import requests
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv 
import google.generativeai as genai

# ============== 配置 ==============
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OUTPUT_PATH = "public/data.json"
NEWS_COUNT = 10  # 生成新闻数量

# Unsplash 图片关键词池（财经/科技主题）
IMAGE_KEYWORDS = [
    "quantum computing", "cryptocurrency", "satellite space", 
    "nuclear fusion", "AI artificial intelligence", "cybersecurity",
    "renewable energy", "stock market trading", "blockchain technology",
    "biotechnology", "climate change", "semiconductor chip",
    "autonomous vehicle", "5G network", "data center"
]

# ============== 新闻源抓取 ==============
class NewsSource:
    """新闻源抓取器（支持多种来源）"""
    
    @staticmethod
    def fetch_from_newsapi(count: int = 10) -> List[Dict[str, str]]:
        """
        使用 NewsAPI 抓取新闻（需要 API Key）
        替代方案：可以用免费的 RSS feed
        """
        try:
            api_key = os.environ.get("NEWS_API_KEY", "")
            if not api_key:
                print("⚠️  NEWS_API_KEY 未设置，使用模拟数据")
                return NewsSource._generate_mock_news(count)
            
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": api_key,
                "category": "business,technology",
                "language": "en",
                "pageSize": count
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get("articles", [])[:count]:
                articles.append({
                    "title": article.get("title", "Untitled"),
                    "description": article.get("description", "No description"),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown")
                })
            
            return articles
            
        except Exception as e:
            print(f"❌ NewsAPI 抓取失败: {e}")
            return NewsSource._generate_mock_news(count)
    
    @staticmethod
    def fetch_from_rss() -> List[Dict[str, str]]:
        """
        从 RSS Feed 抓取（免费方案）
        推荐源：Bloomberg, Reuters, TechCrunch
        """
        try:
            import feedparser
            
            feeds = [
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://www.reuters.com/rssFeed/businessNews",
                "https://techcrunch.com/feed/"
            ]
            
            articles = []
            for feed_url in feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:3]:  # 每个源取3条
                        articles.append({
                            "title": entry.get("title", "Untitled"),
                            "description": entry.get("summary", "No description"),
                            "url": entry.get("link", ""),
                            "source": feed.feed.get("title", "Unknown")
                        })
                except Exception as e:
                    print(f"⚠️  RSS 源抓取失败 ({feed_url}): {e}")
                    continue
            
            return articles[:NEWS_COUNT]
            
        except ImportError:
            print("⚠️  feedparser 未安装，使用模拟数据")
            return NewsSource._generate_mock_news(NEWS_COUNT)
        except Exception as e:
            print(f"❌ RSS 抓取失败: {e}")
            return NewsSource._generate_mock_news(NEWS_COUNT)
    
    @staticmethod
    def _generate_mock_news(count: int) -> List[Dict[str, str]]:
        """生成模拟新闻数据（用于测试或 API 失败时）"""
        mock_topics = [
            ("Quantum Computing Breakthrough in EU Labs", "European scientists achieve quantum supremacy milestone"),
            ("Lithium Cartel Forms in South America", "Argentina, Bolivia, Chile restrict lithium exports"),
            ("BRICS Nations Launch Gold-Backed Digital Currency", "New monetary system challenges USD dominance"),
            ("AI Regulation Summit Reaches Global Consensus", "UN passes first binding AGI safety framework"),
            ("Cybersecurity Crisis Hits Major Chip Foundry", "TSMC production halted after ransomware attack"),
            ("Deep Sea Mining Rights Approved by UN", "ISA opens Clarion-Clipperton Zone for extraction"),
            ("Commercial Fusion Reactor Exceeds Q-Value 10", "ITER announces breakthrough in net energy gain"),
            ("Antarctic Treaty Expires Amid Military Buildup", "Three powers establish missile-capable bases"),
            ("Smart City IoT Network Breached by Hackers", "Seoul infrastructure paralyzed by zero-day exploit"),
            ("Supreme Court Rules Gene Sequences Patentable", "CRISPR patents spark bioethics controversy")
        ]
        
        return [
            {
                "title": topic[0],
                "description": topic[1],
                "url": "https://example.com",
                "source": "Mock Source"
            }
            for topic in random.sample(mock_topics, min(count, len(mock_topics)))
        ]


# ============== Gemini AI 分析器 ==============
class GeminiAnalyzer:
    """使用 Gemini API 进行新闻深度分析"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_batch(self, articles: List[Dict[str, str]], lang: str = "en") -> List[Dict[str, Any]]:
        """
        批量分析新闻，生成符合前端数据结构的 JSON
        
        Args:
            articles: 新闻列表
            lang: 目标语言 (zh/en/es)
        
        Returns:
            符合前端格式的数据列表
        """
        
        # 构建精确的 Prompt
        prompt = self._build_analysis_prompt(articles, lang)
        
        try:
            print(f"🤖 正在调用 Gemini API 分析 {len(articles)} 条新闻...")
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8000,
                )
            )
            
            # 提取 JSON（处理 Markdown 代码块）
            result_text = response.text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            data = json.loads(result_text.strip())
            
            # 添加图片 URL 和唯一 ID
            for i, item in enumerate(data):
                item["id"] = f"NEX-{8820 + i}"
                item["image"] = self._get_unsplash_image(IMAGE_KEYWORDS[i % len(IMAGE_KEYWORDS)])
            
            print(f"✅ 成功生成 {len(data)} 条情报数据")
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            print(f"原始响应: {response.text[:500]}...")
            return []
        except Exception as e:
            print(f"❌ Gemini API 调用失败: {e}")
            return []
    
    def _build_analysis_prompt(self, articles: List[Dict[str, str]], lang: str) -> str:
        """构建 Gemini 分析 Prompt"""
        
        # 语言映射
        lang_map = {
            "zh": "中文（简体）",
            "en": "English",
            "es": "Español"
        }
        target_lang = lang_map.get(lang, "English")
        
        # 新闻列表格式化
        news_list = "\n".join([
            f"{i+1}. {article['title']} - {article['description']}"
            for i, article in enumerate(articles)
        ])
        
        prompt = f"""你是 NEXUS-9，一个顶级金融情报分析系统。请分析以下新闻并生成**严格符合 JSON 格式**的情报报告。

📰 **今日新闻列表**：
{news_list}

🎯 **任务要求**：
1. 为每条新闻生成一个完整的情报对象
2. 使用 {target_lang} 语言输出所有文本字段
3. 必须严格遵守以下 JSON 结构（不可遗漏任何字段）
4. 直接返回 JSON 数组，不要添加任何解释性文字

📋 **严格的 JSON 结构模板**（每条新闻必须包含以下所有字段）：

```json
[
  {{
    "title": "简短标题（15字内）",
    "fullTitle": "完整详细标题（25字内）",
    "classification": "TOP SECRET | CONFIDENTIAL | RESTRICTED | UNCLASSIFIED",
    "impactLevel": "CRITICAL | HIGH | MEDIUM | INFO",
    "summary": "3-4句话的情报摘要，描述事件核心、影响和背景",
    "relations": [
      {{
        "label": "相关实体名称（如公司/国家/技术）",
        "type": "entity | tech | risk | resource",
        "desc": "简短描述（10字内）"
      }}
    ],
    "analysis": {{
      "strategic": [
        "战略分析要点1（20-30字）",
        "战略分析要点2（20-30字）"
      ]
    }},
    "investment": {{
      "action": "LONG | SHORT",
      "asset": "具体标的（如股票代码/资产类别）",
      "risk": "HIGH | MEDIUM | LOW",
      "thesis": "投资逻辑（30-50字）"
    }},
    "confidence": 85
  }}
]
```

⚠️ **关键约束**：
- `relations` 数组：每条新闻至少3个、最多5个关联实体
- `analysis.strategic` 数组：必须包含2条战略分析
- `confidence` 值：必须是 80-98 之间的整数
- 所有文本使用 {target_lang} 语言
- 不要包含 `image` 和 `id` 字段（这些由脚本自动添加）

🚀 **现在开始分析，直接输出 JSON 数组**：
"""
        return prompt
    
    @staticmethod
    def _get_unsplash_image(keyword: str) -> str:
        """生成 Unsplash 图片 URL"""
        keyword_encoded = keyword.replace(" ", "%20")
        return f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1700000000000)}?q=80&w=800&auto=format&fit=crop&ixlib=rb-4.0.3&keyword={keyword_encoded}"


# ============== 主函数 ==============
def main():
    """主执行流程"""
    print("=" * 60)
    print("🔮 NEXUS INTEL 新闻自动更新系统")
    print("=" * 60)
    
    # 1. 检查 API Key
    if not GEMINI_API_KEY:
        print("❌ 错误：GEMINI_API_KEY 环境变量未设置")
        print("💡 请运行：export GEMINI_API_KEY='your_api_key_here'")
        return
    
    # 2. 抓取新闻
    print("\n📡 抓取新闻源...")
    articles = NewsSource.fetch_from_rss()  # 优先使用 RSS（免费）
    
    if not articles:
        print("❌ 无法获取新闻，使用模拟数据")
        articles = NewsSource._generate_mock_news(NEWS_COUNT)
    
    print(f"✅ 成功获取 {len(articles)} 条新闻")
    
    # 3. AI 分析
    analyzer = GeminiAnalyzer(GEMINI_API_KEY)
    
    # 生成三种语言的数据
    all_data = {}
    for lang in ["zh", "en", "es"]:
        print(f"\n🌐 生成 {lang} 语言数据...")
        lang_data = analyzer.analyze_batch(articles, lang)
        all_data[lang] = lang_data
    
    # 4. 保存 JSON
    if any(all_data.values()):
        os.makedirs("public", exist_ok=True)
        
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "languages": all_data
        }
        
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 数据已保存到 {OUTPUT_PATH}")
        print(f"📊 统计：")
        for lang, data in all_data.items():
            print(f"   - {lang}: {len(data)} 条")
    else:
        print("\n❌ 所有语言数据生成失败")
    
    print("\n" + "=" * 60)
    print("✨ 更新完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
