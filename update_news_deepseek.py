#!/usr/bin/env python3
"""
NexusIntel 新闻自动更新脚本 v2
多源抓取 + 分类 + GPT-5.2 分析 + Gmail/Telegram 推送
"""

import os
import json
import random
import re
import smtplib
import requests
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

from openai import OpenAI

# ============== 配置 ==============
# LLM API (bobdong.cn - OpenAI 兼容)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://bobdong.cn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-5.2")

# 新闻源 API
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# 通知：Gmail SMTP
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_TO = os.environ.get("GMAIL_TO", "wangjoy569@gmail.com")

# 通知：Telegram（备用）
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

OUTPUT_PATH = "public/data.json"
TARGET_COUNT = 15

# 分类配置
CATEGORIES = {
    "macro": {"label": "宏观经济", "target": 3},
    "tech": {"label": "科技", "target": 3},
    "crypto": {"label": "加密货币", "target": 2},
    "geopolitics": {"label": "地缘政治", "target": 2},
    "china": {"label": "中国/亚太", "target": 3},
    "market": {"label": "市场动态", "target": 2},
}

# Unsplash 图片关键词池（按分类）
IMAGE_KEYWORDS = {
    "macro": ["stock market trading", "federal reserve", "inflation economy"],
    "tech": ["AI artificial intelligence", "semiconductor chip", "data center"],
    "crypto": ["cryptocurrency", "blockchain technology", "bitcoin"],
    "geopolitics": ["satellite space", "cybersecurity", "nuclear fusion"],
    "china": ["shanghai skyline", "asian market", "technology china"],
    "market": ["wall street", "stock exchange", "financial chart"],
}


# ============== 新闻源：GNews API ==============
class GNewsSource:
    """GNews API - 免费层 100 req/day，支持多语言"""
    BASE_URL = "https://gnews.io/api/v4"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, lang: str = "en", max_results: int = 5) -> List[Dict[str, str]]:
        if not self.api_key:
            return []
        try:
            resp = requests.get(f"{self.BASE_URL}/search", params={
                "q": query, "lang": lang, "max": max_results, "apikey": self.api_key,
            }, timeout=15)
            resp.raise_for_status()
            return [
                {
                    "title": a["title"],
                    "description": a.get("description", ""),
                    "url": a["url"],
                    "source": a.get("source", {}).get("name", "GNews"),
                }
                for a in resp.json().get("articles", [])
            ]
        except Exception as e:
            print(f"  [GNews] search '{query}' failed: {e}")
            return []

    def top_headlines(self, category: str = "general", lang: str = "en", max_results: int = 5) -> List[Dict[str, str]]:
        if not self.api_key:
            return []
        try:
            resp = requests.get(f"{self.BASE_URL}/top-headlines", params={
                "category": category, "lang": lang, "max": max_results, "apikey": self.api_key,
            }, timeout=15)
            resp.raise_for_status()
            return [
                {
                    "title": a["title"],
                    "description": a.get("description", ""),
                    "url": a["url"],
                    "source": a.get("source", {}).get("name", "GNews"),
                }
                for a in resp.json().get("articles", [])
            ]
        except Exception as e:
            print(f"  [GNews] top_headlines '{category}' failed: {e}")
            return []


# ============== 新闻源：Finnhub（金融新闻）==============
class FinnhubSource:
    """Finnhub API - 免费层 60 req/min"""
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def general_news(self, category: str = "general") -> List[Dict[str, str]]:
        if not self.api_key:
            return []
        try:
            resp = requests.get(f"{self.BASE_URL}/news", params={
                "category": category, "token": self.api_key,
            }, timeout=15)
            resp.raise_for_status()
            return [
                {
                    "title": a["headline"],
                    "description": a.get("summary", "")[:300],
                    "url": a["url"],
                    "source": a.get("source", "Finnhub"),
                }
                for a in resp.json()[:10]
            ]
        except Exception as e:
            print(f"  [Finnhub] failed: {e}")
            return []


# ============== 新闻源：可靠 RSS ==============
class RSSSource:
    """经过验证的免费 RSS 源"""

    FEEDS = {
        "macro": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        ],
        "tech": [
            "https://techcrunch.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "https://www.theverge.com/rss/index.xml",
        ],
        "crypto": [
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
        ],
        "geopolitics": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        ],
        "china": [
            "https://www.36kr.com/feed",
            "https://rsshub.app/36kr/newsflashes",
            "https://rsshub.app/cls/telegraph",
            "https://rsshub.app/wallstreetcn/live/global",
        ],
        "market": [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        ],
    }

    @staticmethod
    def fetch(category: str, max_per_feed: int = 3) -> List[Dict[str, str]]:
        try:
            import feedparser
        except ImportError:
            print("  [RSS] feedparser not installed")
            return []

        feeds = RSSSource.FEEDS.get(category, [])
        articles = []

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:max_per_feed]:
                    title = entry.get("title", "")
                    if not title:
                        continue
                    desc = entry.get("summary", entry.get("description", ""))
                    desc = re.sub(r"<[^>]+>", "", desc)[:300]
                    articles.append({
                        "title": title,
                        "description": desc,
                        "url": entry.get("link", ""),
                        "source": feed.feed.get("title", feed_url.split("/")[2]),
                    })
            except Exception as e:
                print(f"  [RSS] {feed_url[:50]}... failed: {e}")
                continue

        return articles


# ============== 多源聚合器 ==============
class NewsAggregator:
    """聚合多个新闻源，按分类抓取，去重"""

    GNEWS_QUERIES = {
        "macro": ["inflation economy 2026", "federal reserve interest rate", "GDP growth recession"],
        "tech": ["artificial intelligence breakthrough", "semiconductor shortage", "tech IPO 2026"],
        "crypto": ["bitcoin ethereum price", "crypto regulation SEC"],
        "geopolitics": ["war conflict sanctions", "trade war tariff"],
        "china": ["中国经济 政策", "科技公司 监管"],
        "market": ["stock market rally crash", "earnings report surprise"],
    }

    def __init__(self):
        self.gnews = GNewsSource(GNEWS_API_KEY)
        self.finnhub = FinnhubSource(FINNHUB_API_KEY)
        self.seen_titles: set = set()

    def _dedup(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
        result = []
        for a in articles:
            key = a["title"].lower().strip()[:60]
            if key not in self.seen_titles:
                self.seen_titles.add(key)
                result.append(a)
        return result

    def fetch_category(self, category: str, target: int) -> List[Dict[str, str]]:
        all_articles: List[Dict[str, str]] = []

        # 1. RSS（免费无限量）
        print(f"  [{category}] RSS...")
        rss = RSSSource.fetch(category)
        all_articles.extend(rss)
        print(f"  [{category}] RSS: {len(rss)} 条")

        # 2. GNews API（如配置了）
        if GNEWS_API_KEY and len(self._dedup(list(all_articles))) < target:
            queries = self.GNEWS_QUERIES.get(category, [])
            if queries:
                query = random.choice(queries)
                lang = "zh" if category == "china" else "en"
                print(f"  [{category}] GNews: '{query}'...")
                gnews = self.gnews.search(query, lang=lang, max_results=3)
                all_articles.extend(gnews)
                print(f"  [{category}] GNews: {len(gnews)} 条")

        # 3. Finnhub（仅金融类）
        if FINNHUB_API_KEY and category in ("macro", "market") and len(self._dedup(list(all_articles))) < target:
            print(f"  [{category}] Finnhub...")
            fh = self.finnhub.general_news()
            all_articles.extend(fh)
            print(f"  [{category}] Finnhub: {len(fh)} 条")

        deduped = self._dedup(all_articles)
        return deduped[:target]

    def fetch_all(self) -> List[Dict[str, Any]]:
        result = []
        for cat, cfg in CATEGORIES.items():
            print(f"\n📰 [{cfg['label']}]")
            articles = self.fetch_category(cat, cfg["target"])
            for a in articles:
                a["category"] = cat
                a["category_label"] = cfg["label"]
            result.extend(articles)
            print(f"  => {len(articles)} 条")

        print(f"\n📊 总计: {len(result)} 条新闻")
        return result


# ============== LLM 分析器（OpenAI 兼容）==============
class LLMAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_batch(self, articles: List[Dict[str, Any]], lang: str = "en") -> List[Dict[str, Any]]:
        if not articles:
            return []

        prompt = self._build_prompt(articles, lang)
        try:
            print(f"  🤖 {self.model} 分析 {len(articles)} 条 ({lang})...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是 NEXUS-9，顶级金融情报分析系统。严格按要求输出 JSON。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=12000,
            )

            result_text = response.choices[0].message.content
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            data = json.loads(result_text.strip())

            for i, item in enumerate(data):
                cat = articles[i]["category"] if i < len(articles) else "market"
                item["id"] = f"NEX-{random.randint(1000, 9999)}"
                item["category"] = cat
                item["category_label"] = articles[i].get("category_label", "") if i < len(articles) else ""
                keywords = IMAGE_KEYWORDS.get(cat, IMAGE_KEYWORDS["market"])
                item["image"] = self._get_unsplash_image(random.choice(keywords))

            print(f"  ✅ {len(data)} 条情报 ({lang})")
            return data

        except Exception as e:
            print(f"  ❌ LLM 失败 ({lang}): {e}")
            return []

    def _build_prompt(self, articles: List[Dict[str, Any]], lang: str) -> str:
        lang_map = {"zh": "中文（简体）", "en": "English", "es": "Español"}
        target_lang = lang_map.get(lang, "English")

        news_list = "\n".join([
            f"{i+1}. [{a.get('category_label', '')}] {a['title']} - {a['description'][:150]}"
            for i, a in enumerate(articles)
        ])

        return f"""你是 NEXUS-9 金融情报分析系统。分析以下新闻并生成 JSON 格式报告。

📰 新闻列表（共 {len(articles)} 条）：
{news_list}

🎯 任务：为每条新闻生成情报对象，使用 {target_lang}，直接返回 JSON 数组。

📋 JSON 结构：
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

⚠️ 约束：relations 3-5个，strategic 2条，confidence 80-98，数组长度 = {len(articles)}，语言 {target_lang}

直接输出 JSON：
"""

    @staticmethod
    def _get_unsplash_image(keyword: str) -> str:
        keyword_encoded = keyword.replace(" ", "%20")
        return f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1700000000000)}?q=80&w=800&auto=format&fit=crop&keyword={keyword_encoded}"


# ============== Telegram 推送 ==============
class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)

    def send(self, articles: List[Dict[str, Any]]) -> bool:
        if not self.enabled:
            print("⚠️  Telegram 未配置，跳过推送")
            return False

        by_cat: Dict[str, List] = {}
        for a in articles:
            cat = a.get("category_label", "其他")
            by_cat.setdefault(cat, []).append(a)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [f"🔮 *NEXUS INTEL 日报* | {now}", f"📊 共 {len(articles)} 条情报", ""]

        for cat, items in by_cat.items():
            lines.append(f"*── {cat} ──*")
            for item in items:
                impact = item.get("impactLevel", "INFO")
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "INFO": "🔵"}.get(impact, "⚪")
                title = item.get("fullTitle", item.get("title", ""))
                action = item.get("investment", {}).get("action", "")
                asset = item.get("investment", {}).get("asset", "")
                invest = f" → {action} {asset}" if action else ""
                lines.append(f"  {icon} {title}{invest}")
            lines.append("")

        message = "\n".join(lines)

        try:
            for i in range(0, len(message), 4000):
                chunk = message[i:i + 4000]
                resp = requests.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": chunk,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    print(f"  ⚠️  Telegram 失败: {resp.text[:200]}")
                    return False

            print("✅ Telegram 推送成功")
            return True
        except Exception as e:
            print(f"❌ Telegram 推送失败: {e}")
            return False


# ============== Gmail 推送 ==============
class GmailNotifier:
    def __init__(self, address: str, app_password: str, to: str):
        self.address = address
        self.app_password = app_password
        self.to = to
        self.enabled = bool(address and app_password)

    def send(self, articles: List[Dict[str, Any]]) -> bool:
        if not self.enabled:
            print("⚠️  Gmail 未配置，跳过邮件推送")
            return False

        by_cat: Dict[str, List] = {}
        for a in articles:
            cat = a.get("category_label", "其他")
            by_cat.setdefault(cat, []).append(a)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # HTML 邮件
        html_parts = [
            "<div style='font-family: -apple-system, Arial, sans-serif; max-width: 700px; margin: 0 auto;'>",
            f"<h1 style='color: #1a1a2e;'>NEXUS INTEL 日报</h1>",
            f"<p style='color: #666;'>{now} | 共 {len(articles)} 条情报</p>",
            "<hr style='border: 1px solid #eee;'>",
        ]

        impact_colors = {
            "CRITICAL": "#dc3545", "HIGH": "#fd7e14",
            "MEDIUM": "#ffc107", "INFO": "#0d6efd",
        }

        for cat, items in by_cat.items():
            html_parts.append(f"<h2 style='color: #333; border-left: 4px solid #667eea; padding-left: 12px;'>{cat}</h2>")
            for item in items:
                impact = item.get("impactLevel", "INFO")
                color = impact_colors.get(impact, "#6c757d")
                title = item.get("fullTitle", item.get("title", ""))
                summary = item.get("summary", "")
                action = item.get("investment", {}).get("action", "")
                asset = item.get("investment", {}).get("asset", "")
                risk = item.get("investment", {}).get("risk", "")
                thesis = item.get("investment", {}).get("thesis", "")

                html_parts.append(f"""
                <div style='margin: 16px 0; padding: 16px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid {color};'>
                    <div style='font-size: 11px; color: {color}; font-weight: bold; text-transform: uppercase;'>{impact}</div>
                    <div style='font-size: 16px; font-weight: 600; margin: 4px 0;'>{title}</div>
                    <div style='color: #555; font-size: 14px; line-height: 1.5;'>{summary}</div>
                    {"<div style='margin-top: 8px; padding: 8px; background: #e8f4fd; border-radius: 4px; font-size: 13px;'>"
                     f"<b>{action}</b> {asset} | Risk: {risk}<br/><i>{thesis}</i></div>" if action else ""}
                </div>""")

        html_parts.append("</div>")
        html_body = "\n".join(html_parts)

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"NEXUS INTEL | {now} | {len(articles)} 条情报"
            msg["From"] = self.address
            msg["To"] = self.to
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.address, self.app_password)
                server.send_message(msg)

            print("✅ Gmail 推送成功")
            return True
        except Exception as e:
            print(f"❌ Gmail 推送失败: {e}")
            return False


# ============== 主函数 ==============
def main():
    print("=" * 60)
    print(f"🔮 NEXUS INTEL v2 — {LLM_MODEL} + 多源 + 推送")
    print(f"📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    if not LLM_API_KEY:
        print("❌ LLM_API_KEY 未设置")
        return

    # 1. 多源抓取
    print("\n📡 Step 1: 多源新闻抓取")
    aggregator = NewsAggregator()
    articles = aggregator.fetch_all()

    if not articles:
        print("❌ 无法获取任何新闻")
        return

    # 2. LLM 多语言分析
    print(f"\n🧠 Step 2: {LLM_MODEL} AI 分析")
    analyzer = LLMAnalyzer(LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)

    all_data: Dict[str, List] = {}
    for lang in ["zh", "en", "es"]:
        print(f"\n🌐 生成 {lang} 数据...")
        all_data[lang] = analyzer.analyze_batch(articles, lang)

    if not any(all_data.values()):
        print("❌ 所有语言分析失败")
        return

    # 3. 保存
    print("\n💾 Step 3: 保存数据")
    os.makedirs("public", exist_ok=True)

    cat_stats = {}
    for a in articles:
        cat = a.get("category_label", "未分类")
        cat_stats[cat] = cat_stats.get(cat, 0) + 1

    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2.0",
        "total_articles": len(articles),
        "categories": cat_stats,
        "sources_used": {
            "gnews": bool(GNEWS_API_KEY),
            "finnhub": bool(FINNHUB_API_KEY),
            "rss": True,
        },
        "languages": all_data,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存 {OUTPUT_PATH}")
    print(f"   分类: {cat_stats}")

    # 4. 推送通知
    print("\n📲 Step 4: 推送通知")
    zh_data = all_data.get("zh", [])
    if not zh_data:
        print("⚠️  中文数据为空，跳过推送")
    else:
        # Gmail 优先
        gmail = GmailNotifier(GMAIL_ADDRESS, GMAIL_APP_PASSWORD, GMAIL_TO)
        if gmail.enabled:
            gmail.send(zh_data)
        # Telegram 备用
        telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        if telegram.enabled:
            telegram.send(zh_data)

    print("\n" + "=" * 60)
    print(f"✨ 完成！{len(articles)} 条情报，{len(cat_stats)} 个板块")
    print("=" * 60)


if __name__ == "__main__":
    main()
