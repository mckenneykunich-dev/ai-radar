"""
微信公众号采集
通过 RSSHub + 搜狗微信索引获取指定公众号文章
免费方案，无需 API Key
"""

import feedparser
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import quote

# RSSHub 公共实例（按优先级排序，主用第一个，失败后依次尝试）
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://hub.slarker.me",
]

# 目标公众号名单（由用户提供）
WECHAT_ACCOUNTS = [
    "量子位",
    "Z Potentials",
    "海外独角兽",
    "硅星人Pro",
    "DeepTech深科技",
    "机器之心",
    "新智元",
    "极客公园",
]

# AI 相关关键词（用于二次过滤）
AI_KEYWORDS = [
    "ai", "人工智能", "大模型", "llm", "gpt", "claude", "gemini",
    "机器学习", "深度学习", "神经网络", "算法", "智能", "自动驾驶",
    "具身", "机器人", "agent", "rag", "推理", "训练", "推断",
    "融资", "投资", "创业", "独角兽", "上市", "估值",
]


def fetch() -> List[dict]:
    """
    采集所有目标公众号的最新文章
    返回标准化信号列表
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = []
    failed = []

    for account in WECHAT_ACCOUNTS:
        result = _fetch_account(account, cutoff)
        if result is not None:
            signals.extend(result)
            print(f"  [WeChat] {account}: {len(result)} 条")
        else:
            failed.append(account)
        time.sleep(1.5)  # 避免触发限速

    if failed:
        print(f"  [WeChat] 采集失败的账号: {', '.join(failed)}")

    print(f"[WeChat] 采集完成，共 {len(signals)} 条")
    return signals


def _fetch_account(account: str, cutoff: datetime) -> Optional[List[dict]]:
    """
    尝试从多个 RSSHub 实例获取指定公众号的 RSS
    """
    encoded = quote(account)

    for base_url in RSSHUB_INSTANCES:
        feed_url = f"{base_url}/wechat/sogou/{encoded}"
        try:
            feed = feedparser.parse(feed_url)

            # feedparser 不抛异常，通过 bozo 字段判断是否解析成功
            if feed.bozo and not feed.entries:
                continue
            if not feed.entries:
                continue

            items = []
            for entry in feed.entries:
                published_at = _parse_date(entry)
                if published_at and published_at < cutoff:
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", "")[:500]
                url = entry.get("link", "")

                if not url or not title:
                    continue

                # 二次过滤：确保内容与 AI/科技相关
                text = f"{title} {summary}".lower()
                if not any(kw in text for kw in AI_KEYWORDS):
                    continue

                items.append({
                    "source": "wechat",
                    "source_url": url,
                    "title": title,
                    "description": summary,
                    "published_at": published_at.isoformat() if published_at else datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "account_name": account,
                    }
                })

            return items  # 成功则直接返回，不再尝试其他实例

        except Exception as e:
            print(f"  [WeChat] {account} @ {base_url} 失败: {e}")
            continue

    return None  # 所有实例均失败


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
