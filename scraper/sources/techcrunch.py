"""
TechCrunch RSS 采集
过滤过去7天内的 AI 相关文章
"""

import feedparser
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
]

AI_KEYWORDS = [
    "ai", "llm", "gpt", "openai", "anthropic", "google deepmind",
    "machine learning", "deep learning", "neural network",
    "generative", "foundation model", "large language",
    "robotics", "autonomous", "computer vision", "diffusion",
    "claude", "gemini", "llama", "mistral", "agent", "copilot"
]


def fetch() -> list[dict]:
    """
    采集 TechCrunch RSS 中的 AI 相关文章
    返回标准化信号列表
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = []
    seen_urls = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                url = entry.get("link", "")
                if url in seen_urls:
                    continue

                # 解析发布时间
                try:
                    pub_date = parsedate_to_datetime(entry.get("published", ""))
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    if pub_date < cutoff:
                        continue
                except Exception:
                    continue

                if not _is_ai_related(entry):
                    continue

                seen_urls.add(url)
                signals.append(_normalize(entry, pub_date))

            time.sleep(1)
        except Exception as e:
            print(f"[TechCrunch] feed={feed_url} 采集失败: {e}")
            continue

    print(f"[TechCrunch] 采集完成，共 {len(signals)} 条")
    return signals


def _is_ai_related(entry: dict) -> bool:
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _normalize(entry: dict, pub_date: datetime) -> dict:
    # 提取摘要（去掉 HTML 标签）
    summary = entry.get("summary", "")
    if "<" in summary:
        import re
        summary = re.sub(r"<[^>]+>", "", summary).strip()
    summary = summary[:400]  # 截断，不存全文

    return {
        "source": "techcrunch",
        "source_url": entry.get("link", ""),
        "title": entry.get("title", ""),
        "description": summary,
        "published_at": pub_date.isoformat(),
        "metadata": {
            "author": entry.get("author", ""),
            "tags": [t.get("term", "") for t in entry.get("tags", [])],
        }
    }
