"""
ArXiv cs.AI 论文采集
使用官方 Atom API（完全免费，无需 Key）
只取过去7天内提交、摘要包含应用/产品方向关键词的论文
（过滤掉纯数学/基础理论，保留与投资赛道相关的）
"""

import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ARXIV_API = "http://export.arxiv.org/api/query"

# 关注的子分类：AI、ML、CV、CL（NLP）、RO（机器人）
CATEGORIES = ["cs.AI", "cs.LG", "cs.CV", "cs.CL", "cs.RO"]

# 应用方向关键词（过滤纯理论论文）
APPLICATION_KEYWORDS = [
    "agent", "llm", "large language", "multimodal", "robotics",
    "autonomous", "code generation", "medical", "drug discovery",
    "protein", "clinical", "finance", "trading", "recommendation",
    "retrieval", "rag", "tool use", "benchmark", "evaluation",
    "deployment", "inference", "efficient", "distillation",
    "alignment", "safety", "reward", "rlhf", "fine-tuning"
]

NS = "{http://www.w3.org/2005/Atom}"


def fetch() -> list[dict]:
    """
    采集 ArXiv 近7天的应用方向 AI 论文
    返回标准化信号列表
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = []
    seen_urls = set()

    for cat in CATEGORIES:
        params = {
            "search_query": f"cat:{cat}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 30,
            "start": 0
        }
        try:
            resp = requests.get(ARXIV_API, params=params, timeout=15)
            resp.raise_for_status()
            entries = _parse_feed(resp.text)

            for entry in entries:
                url = entry.get("source_url", "")
                if url in seen_urls:
                    continue

                try:
                    pub_date = datetime.fromisoformat(
                        entry["published_at"].replace("Z", "+00:00")
                    )
                    if pub_date < cutoff:
                        continue
                except Exception:
                    continue

                if not _is_application_relevant(entry):
                    continue

                seen_urls.add(url)
                signals.append(entry)

            time.sleep(3)  # ArXiv 要求请求间隔 ≥ 3秒
        except Exception as e:
            print(f"[ArXiv] cat={cat} 采集失败: {e}")
            continue

    print(f"[ArXiv] 采集完成，共 {len(signals)} 条")
    return signals


def _parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    results = []
    for entry in root.findall(f"{NS}entry"):
        try:
            title = entry.find(f"{NS}title").text.strip().replace("\n", " ")
            abstract = entry.find(f"{NS}summary").text.strip().replace("\n", " ")
            published = entry.find(f"{NS}published").text.strip()
            url = entry.find(f"{NS}id").text.strip()

            authors = [
                a.find(f"{NS}name").text
                for a in entry.findall(f"{NS}author")
                if a.find(f"{NS}name") is not None
            ]

            # 截断摘要（不存全文）
            short_abstract = abstract[:400] + ("..." if len(abstract) > 400 else "")

            results.append({
                "source": "arxiv",
                "source_url": url,
                "title": title,
                "description": short_abstract,
                "published_at": published,
                "metadata": {
                    "authors": authors[:5],  # 最多5位作者
                    "abstract_length": len(abstract),
                }
            })
        except Exception:
            continue
    return results


def _is_application_relevant(entry: dict) -> bool:
    text = f"{entry['title']} {entry['description']}".lower()
    return any(kw in text for kw in APPLICATION_KEYWORDS)
