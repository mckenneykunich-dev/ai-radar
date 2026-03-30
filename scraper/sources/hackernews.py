"""
Hacker News 数据采集
使用官方 Firebase REST API（完全免费，无需 Key）
过滤出过去7天内的 AI 相关热帖
"""

import requests
import time
from datetime import datetime, timedelta, timezone

HN_API = "https://hacker-news.firebaseio.com/v0"

AI_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "llama", "mistral",
    "ai ", " ai", "machine learning", "deep learning",
    "neural", "transformer", "diffusion", "stable diffusion",
    "openai", "anthropic", "agent", "rag", "embedding",
    "copilot", "robotics", "autonomous", "multimodal",
    "fine-tuning", "finetuning", "foundation model",
    "large language", "generative", "inference", "gpu"
]

MIN_SCORE = 100  # 只取高热度帖子


def fetch() -> list[dict]:
    """
    采集 HN Top Stories 中的 AI 相关帖子
    返回标准化信号列表
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_ts = int(cutoff.timestamp())

    try:
        resp = requests.get(f"{HN_API}/topstories.json", timeout=10)
        resp.raise_for_status()
        story_ids = resp.json()[:300]  # 取前300条
    except Exception as e:
        print(f"[HackerNews] 获取 top stories 失败: {e}")
        return []

    signals = []
    for story_id in story_ids:
        try:
            resp = requests.get(f"{HN_API}/item/{story_id}.json", timeout=8)
            resp.raise_for_status()
            item = resp.json()
            if not item:
                continue

            # 过滤：时间、分数、AI相关性
            if item.get("time", 0) < cutoff_ts:
                continue
            if item.get("score", 0) < MIN_SCORE:
                continue
            if not _is_ai_related(item):
                continue

            signals.append(_normalize(item))
            time.sleep(0.05)
        except Exception as e:
            print(f"[HackerNews] item={story_id} 获取失败: {e}")
            continue

    print(f"[HackerNews] 采集完成，共 {len(signals)} 条")
    return signals


def _is_ai_related(item: dict) -> bool:
    """判断帖子是否与 AI 相关"""
    text = f"{item.get('title', '')} {item.get('url', '')}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _normalize(item: dict) -> dict:
    """将 HN item 转换为标准信号格式"""
    published_at = datetime.fromtimestamp(
        item.get("time", 0), tz=timezone.utc
    ).isoformat()

    return {
        "source": "hackernews",
        "source_url": item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}",
        "title": item.get("title", ""),
        "description": "",
        "published_at": published_at,
        "metadata": {
            "hn_score": item.get("score", 0),
            "comments": item.get("descendants", 0),
            "hn_id": item.get("id"),
        }
    }
