"""
GitHub 数据采集
使用 GitHub Search API 找出过去7天内新增 star 最多的 AI 相关项目
不需要 API Key（未认证限额60次/小时，已足够）
"""

import requests
import time
from datetime import datetime, timedelta, timezone

AI_TOPICS = [
    "llm", "large-language-model", "ai-agent", "generative-ai",
    "machine-learning", "deep-learning", "computer-vision",
    "natural-language-processing", "reinforcement-learning",
    "diffusion-model", "transformer", "rag", "vector-database"
]

AI_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "mistral", "llama",
    "agent", "rag", "embedding", "diffusion", "transformer",
    "multimodal", "vision", "copilot", "autopilot", "robotics"
]


def fetch(github_token: str = None) -> list[dict]:
    """
    采集过去7天 GitHub 上 AI 相关的高增长项目
    返回标准化信号列表
    """
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    signals = []
    seen_urls = set()

    for topic in AI_TOPICS[:6]:  # 每次只取前6个 topic，控制请求量
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"topic:{topic} created:>{since} stars:>50",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for repo in data.get("items", []):
                repo_url = repo["html_url"]
                if repo_url in seen_urls:
                    continue
                seen_urls.add(repo_url)
                signals.append(_normalize(repo))
            time.sleep(1.2)  # 避免触发速率限制
        except Exception as e:
            print(f"[GitHub] topic={topic} 采集失败: {e}")
            continue

    # 补充：按关键词搜索过去7天创建、star > 100 的项目
    for kw in AI_KEYWORDS[:5]:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"{kw} in:name,description created:>{since} stars:>100",
            "sort": "stars",
            "order": "desc",
            "per_page": 5
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for repo in data.get("items", []):
                repo_url = repo["html_url"]
                if repo_url in seen_urls:
                    continue
                seen_urls.add(repo_url)
                signals.append(_normalize(repo))
            time.sleep(1.2)
        except Exception as e:
            print(f"[GitHub] keyword={kw} 采集失败: {e}")
            continue

    print(f"[GitHub] 采集完成，共 {len(signals)} 条")
    return signals


def _normalize(repo: dict) -> dict:
    """将 GitHub API 返回的 repo 对象转换为标准信号格式"""
    return {
        "source": "github",
        "source_url": repo["html_url"],
        "title": repo["full_name"],
        "description": repo.get("description") or "",
        "published_at": repo.get("created_at", ""),
        "metadata": {
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", []),
            "watchers": repo.get("watchers_count", 0),
        }
    }
