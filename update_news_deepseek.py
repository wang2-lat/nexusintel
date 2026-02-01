#!/usr/bin/env python3
"""
NexusIntel 新闻自动更新脚本（DeepSeek 版本）
"""

import os
import json
import random
import requests
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI

# ============== 配置 ==============
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
OUTPUT_PATH = "public/data.json"
NEWS_COUNT = 10

# Unsplash 图片关键词池
IMAGE_KEYWORDS = [
    "quantum computing", "cryptocurrency", "satellite space", 
    "nuclear fusion", "AI artificial intelligence", "cybersecurity",
    "renewable energy", "stock market trading", "blockchain technology",
    "biotechnology", "climate change", "semiconductor chip",
    "autonomous vehicle", "5G network", "data center"
]

# ============== 新闻源抓取 ==============
class NewsSource:
    @staticmethod
    def fetch_from_rss() -> List[Dict[str, str]]:
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
                    for entry in feed.entries[:3]:
                        articles.append({
                            "title": entry.get("title", "Untitled"),
                            "description": entry.get("summary", "No description"),
                            "url": entry.get("link", ""),
                            "source": feed.feed.get("title", "Unknown")
                        })
                except Exception as e:
                    print(f"⚠️  RSS 源抓取失败: {e}")
                    continue
            
            return articles[:NEWS_COUNT]
            
        except:
            return NewsSource._generate_mock_news(NEWS_COUNT)
    
    @staticmethod
    def _generate_mock_news(count: int) -> List[Dict[str, str]]:
        mock_topics = [
            ("Quantum Computing Breakthrough in EU", "European scientists achieve quantum supremacy"),
            ("Lithium Cartel Forms in South America", "Argentina, Bolivia, Chile restrict lithium exports"),
            ("AI Regulation Summit Reaches Consensus", "UN passes first binding AGI framework"),
            ("Cybersecurity Crisis at Chip Foundry", "TSMC production halted by ransomware"),
            ("Deep Sea Mining Rights Approved", "ISA opens zone for extraction"),
            ("Commercial Fusion Exceeds Q-Value 10", "ITER announces breakthrough"),
            ("Antarctic Treaty Expires", "Military buildup reported"),
            ("Smart City System Breached", "Seoul infrastructure paralyzed"),
            ("Gene Sequences Now Patentable", "Supreme Court ruling sparks controversy"),
            ("Flying Taxi Route Approved", "FAA certifies first autonomous eVTOL")
        ]
        
        return [
            {"title": t[0], "description": t[1], "url": "https://example.com", "source": "Mock"}
            for t in random.sample(mock_topics, min(count, len(mock_topics)))
        ]

# ============== DeepSeek AI 分析器 ==============
class DeepSeekAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def analyze_batch(self, articles: List[Dict[str, str]], lang: str = "en") -> List[Dict[str, Any]]:
        prompt = self._build_analysis_prompt(articles, lang)
        
        try:
            print(f"🤖 正在调用 DeepSeek API 分析 {len(articles)} 条新闻...")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是 NEXUS-9，顶级金融情报分析系统。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            
            result_text = response.choices[0].message.content
            
            # 提取 JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            data = json.loads(result_text.strip())
            
            # 添加图片和 ID
            for i, item in enumerate(data):
                item["id"] = f"NEX-{8820 + i}"
                item["image"] = self._get_unsplash_image(IMAGE_KEYWORDS[i % len(IMAGE_KEYWORDS)])
            
            print(f"✅ 成功生成 {len(data)} 条情报数据")
            return data
            
        except Exception as e:
            print(f"❌ DeepSeek API 调用失败: {e}")
            return []
    
    def _build_analysis_prompt(self, articles: List[Dict[str, str]], lang: str) -> str:
        lang_map = {"zh": "中文（简体）", "en": "English", "es": "Español"}
        target_lang = lang_map.get(lang, "English")
        
        news_list = "\n".join([
            f"{i+1}. {article['title']} - {article['description']}"
            for i, article in enumerate(articles)
        ])
        
        prompt = f"""你是 NEXUS-9 金融情报分析系统。分析以下新闻并生成 JSON 格式报告。

📰 新闻列表：
{news_list}

🎯 任务：
1. 为每条新闻生成完整的情报对象
2. 使用 {target_lang} 语言
3. 直接返回 JSON 数组，不要任何解释

📋 JSON 结构（每条新闻必须包含）：
```json
[
  {{
    "title": "简短标题（15字内）",
    "fullTitle": "完整标题（25字内）",
    "classification": "TOP SECRET | CONFIDENTIAL | RESTRICTED | UNCLASSIFIED",
    "impactLevel": "CRITICAL | HIGH | MEDIUM | INFO",
    "summary": "3-4句话摘要",
    "relations": [
      {{"label": "实体名称", "type": "entity | tech | risk | resource", "desc": "简短描述"}}
    ],
    "analysis": {{
      "strategic": ["战略分析1", "战略分析2"]
    }},
    "investment": {{
      "action": "LONG | SHORT",
      "asset": "具体标的",
      "risk": "HIGH | MEDIUM | LOW",
      "thesis": "投资逻辑"
    }},
    "confidence": 85
  }}
]
```

⚠️ 约束：
- relations: 3-5个
- strategic: 必须2条
- confidence: 80-98
- 所有文本用 {target_lang}

直接输出 JSON：
"""
        return prompt
    
    @staticmethod
    def _get_unsplash_image(keyword: str) -> str:
        keyword_encoded = keyword.replace(" ", "%20")
        return f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1700000000000)}?q=80&w=800&auto=format&fit=crop&keyword={keyword_encoded}"

# ============== 主函数 ==============
def main():
    print("=" * 60)
    print("🔮 NEXUS INTEL 新闻自动更新系统（DeepSeek 版）")
    print("=" * 60)
    
    if not DEEPSEEK_API_KEY:
        print("❌ 错误：DEEPSEEK_API_KEY 未设置")
        print("💡 运行：export DEEPSEEK_API_KEY='your_key_here'")
        return
    
    print("\n📡 抓取新闻源...")
    articles = NewsSource.fetch_from_rss()
    
    if not articles:
        print("❌ 无法获取新闻")
        return
    
    print(f"✅ 成功获取 {len(articles)} 条新闻")
    
    analyzer = DeepSeekAnalyzer(DEEPSEEK_API_KEY)
    
    all_data = {}
    for lang in ["zh", "en", "es"]:
        print(f"\n🌐 生成 {lang} 语言数据...")
        lang_data = analyzer.analyze_batch(articles, lang)
        all_data[lang] = lang_data
    
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
    else:
        print("\n❌ 数据生成失败")
    
    print("\n" + "=" * 60)
    print("✨ 更新完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
