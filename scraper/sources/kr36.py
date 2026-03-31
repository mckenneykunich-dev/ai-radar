"""
36氪 数据采集
通过 RSS Feed 获取融资动态 + AI 相关报道
免费方案，无需 API Key
"""

import feedparser
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

# 36氪 RSS 订阅地址
FEEDS = [
    "https://36kr.com/feed",                          # 全站主 Feed
    "https://36kr.com/information/funding/feed",       # 专项：融资新闻（如有效）
]

# AI 相关关键词
AI_KEYWORDS = [
    "人工智能", "ai", "大模型", "llm", "gpt", "机器学习", "深度学习",
    "自动驾驶", "具身智能", "机器人", "算法", "智能", "agent",
    "多模态", "语言模型", "生成式", "数字员工", "ai agent",
]

# 融资相关关键词（提升信号强度识别）
FUNDING_KEYWORDS = [
    "融资", "投资", "轮", "估值", "上市", "ipo", "并购", "收购",
    "天使", "pre-a", "a轮", "b轮", "c轮", "d轮", "战略融资",
]


def fetch() -> List[dict]:
    """
    采集 36氪 AI + 融资相关文章
    返回标准化信号列表
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = []
    seen_urls = set()

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                print(f"  [36氪] {feed_url} 解析失败")
                continue

            for entry in feed.entries:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", "")[:500]
                published_at = _parse_date(entry)

                if published_at and published_at < cutoff:
                    continue

                # 过滤：AI 或融资相关
                text = f"{title} {summary}".lower()
                is_ai = any(kw in text for kw in AI_KEYWORDS)
                is_funding = any(kw in text for kw in FUNDING_KEYWORDS)

                if not (is_ai or is_funding):
                    continue

                seen_urls.add(url)
                signals.append({
                    "source": "36kr",
                    "source_url": url,
                    "title": title,
                    "description": summary,
                    "published_at": published_at.isoformat() if published_at else datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "is_funding_news": is_funding,
                    }
                })

            time.sleep(1.0)

        except Exception as e:
            print(f"  [36氪] {feed_url} 采集失败: {e}")
            continue

    print(f"[36氪] 采集完成，共 {len(signals)} 条")
    return signals


def _parse_date(entry) -> Optional[datetime]:
    """解析 feedparser entry 的发布时间"""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None
