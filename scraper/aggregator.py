"""
赛道聚合器
将评分后的信号聚合为赛道维度的数据
生成首页展示所需的 tracks.json，包含：
  - 赛道综合评分、趋势
  - LLM 生成的赛道摘要
  - 按信源分组的 source_breakdown（用于详情页）
"""

import time
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

SOURCE_DISPLAY_NAMES = {
    "github": "GitHub",
    "hackernews": "Hacker News",
    "techcrunch": "TechCrunch",
    "arxiv": "ArXiv",
    "36kr": "36氪",
    "wechat": "微信公众号",
    "astock": "A股AI动态",
}

TRACK_SUMMARY_PROMPT = """你是AI投资分析师。基于以下{track}赛道的多信源信号，用约100字生成投资视角摘要。
需说明：①赛道核心演进方向 ②主要驱动力 ③投资机会判断。

代表性信号摘要：
{signal_samples}

直接返回摘要文字，不加任何前缀或标点符号开头。"""

SOURCE_SUMMARY_PROMPT = """你是AI投资分析师。基于{source}平台关于"{track}"赛道的以下信号，写100-150字分析。
需包含：核心技术突破点、产业化进展特征、关键分化因素。

信号列表：
{signal_list}

直接返回分析文字，不加任何前缀。"""


def aggregate_tracks(signals: list[dict], api_key: str = None) -> list[dict]:
    """
    输入：评分后的信号列表
    输出：按赛道聚合的赛道数据列表（包含 summary_zh 和 source_breakdown）
    """
    client = None
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
        except Exception as e:
            print(f"[Aggregator] LLM 客户端初始化失败: {e}")

    # 按赛道分组
    track_signals = defaultdict(list)
    for s in signals:
        track = s.get("track")
        if track:
            track_signals[track].append(s)

    tracks = []
    total_tracks = len(track_signals)

    for idx, (track_name, track_sigs) in enumerate(track_signals.items()):
        if not track_sigs:
            continue

        print(f"[Aggregator] 聚合赛道 {idx+1}/{total_tracks}: {track_name} ({len(track_sigs)} 条信号)")

        track_score = _compute_track_score(track_sigs)
        top_signals = _get_top_signals(track_sigs, n=5)

        # 构建 source_breakdown（含 LLM 摘要）
        source_breakdown = _build_source_breakdown(track_sigs, track_name, client)

        # 生成赛道级 LLM 摘要
        summary_zh = ""
        if client:
            summary_zh = _generate_track_summary(client, track_name, track_sigs)

        tracks.append({
            "name": track_name,
            "score": track_score,
            "project_count": len(track_sigs),
            "top_signals": top_signals,
            "trend": _compute_trend(track_sigs),
            "signal_type_dist": _signal_type_distribution(track_sigs),
            "summary_zh": summary_zh,
            "source_breakdown": source_breakdown,
        })

    # 按赛道分数降序排列
    tracks.sort(key=lambda x: x["score"], reverse=True)
    return tracks


def _build_source_breakdown(track_sigs: list[dict], track_name: str, client) -> dict:
    """
    构建该赛道的 source_breakdown 结构：
    {
      "source_key": {
        "score": X.X,          # 该信源对该赛道的平均评分
        "display_name": "...", # 信源显示名
        "summary": "...",      # LLM 生成的信源解读
        "signals": [...]       # 该信源下属于该赛道的信号列表（精简）
      }
    }
    """
    # 按信源分组
    by_source = defaultdict(list)
    for s in track_sigs:
        src = s.get("source", "unknown")
        by_source[src].append(s)

    breakdown = {}
    for source_key, sigs in by_source.items():
        # 按分数降序排列
        sigs_sorted = sorted(sigs, key=lambda x: x.get("score_final", 0), reverse=True)

        # 计算该信源对该赛道的平均分
        avg_score = sum(s.get("score_final", 0) for s in sigs) / len(sigs)
        source_score = round(min(max(avg_score, 0), 10), 1)

        # 生成该信源的 LLM 解读
        source_summary = ""
        if client and len(sigs) >= 1:
            source_summary = _generate_source_summary(
                client, SOURCE_DISPLAY_NAMES.get(source_key, source_key), track_name, sigs
            )

        # 精简信号字段（保留详情页所需）
        signal_list = [
            {
                "entity_name": s.get("entity_name", ""),
                "source_url": s.get("source_url", ""),
                "summary_zh": s.get("summary_zh", ""),
                "score_final": s.get("score_final", 0),
                "signal_type": s.get("signal_type", ""),
                "team_origin": s.get("team_origin", "unknown"),
                "published_at": s.get("published_at", ""),
                "metadata": s.get("metadata", {}),
            }
            for s in sigs_sorted
        ]

        breakdown[source_key] = {
            "score": source_score,
            "display_name": SOURCE_DISPLAY_NAMES.get(source_key, source_key),
            "summary": source_summary,
            "signals": signal_list,
        }

    # 按 source_score 降序排列（转为有序 dict）
    breakdown_sorted = dict(
        sorted(breakdown.items(), key=lambda x: x[1]["score"], reverse=True)
    )
    return breakdown_sorted


def _generate_track_summary(client, track_name: str, signals: list[dict]) -> str:
    """调用 Kimi 生成赛道级投资摘要（约100字）"""
    # 取分数最高的 8 条信号的摘要作为上下文
    top = sorted(signals, key=lambda x: x.get("score_final", 0), reverse=True)[:8]
    signal_samples = "\n".join(
        f"- [{s.get('source','')}] {s.get('summary_zh','')}" for s in top if s.get("summary_zh")
    )
    if not signal_samples:
        return ""

    prompt = TRACK_SUMMARY_PROMPT.format(
        track=track_name,
        signal_samples=signal_samples
    )
    return _call_llm_text(client, prompt, max_tokens=200)


def _generate_source_summary(client, source_display: str, track_name: str, signals: list[dict]) -> str:
    """调用 Kimi 生成信源对赛道的解读摘要（100-150字）"""
    top = sorted(signals, key=lambda x: x.get("score_final", 0), reverse=True)[:6]
    signal_list = "\n".join(
        f"- {s.get('entity_name','')}：{s.get('summary_zh','')}" for s in top if s.get("summary_zh")
    )
    if not signal_list:
        return ""

    prompt = SOURCE_SUMMARY_PROMPT.format(
        source=source_display,
        track=track_name,
        signal_list=signal_list
    )
    return _call_llm_text(client, prompt, max_tokens=300)


def _call_llm_text(client, prompt: str, max_tokens: int = 300) -> str:
    """通用 LLM 文本生成，带重试和速率限制处理"""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="moonshot-v1-8k",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content.strip()
            time.sleep(0.3)
            return text
        except Exception as e:
            err_str = str(e)
            if "rate_limit" in err_str.lower() or "429" in err_str:
                print("[Aggregator] 速率限制，等待60秒...")
                time.sleep(60)
            else:
                print(f"[Aggregator] LLM 调用失败 (attempt {attempt+1}): {e}")
                time.sleep(2)
    return ""


def _compute_track_score(signals: list[dict]) -> float:
    """
    赛道综合热度分（归一化到 8.0-10.0 区间）
    = 近7天入榜项目数 × 0.4
    + 项目平均分       × 0.4
    + 跨源提及频率     × 0.2
    """
    count = len(signals)
    avg_score = sum(s.get("score_final", 0) for s in signals) / count if count else 0
    sources = set(s.get("source", "") for s in signals)
    source_diversity = len(sources)

    raw = (
        min(count, 20) / 20 * 0.4 +
        min(avg_score, 10) / 10 * 0.4 +
        min(source_diversity, 4) / 4 * 0.2
    )
    return round(8.0 + raw * 2.0, 1)


def _get_top_signals(signals: list[dict], n: int = 5) -> list[dict]:
    """返回评分最高的 n 条信号的精简信息（用于首页卡片预览）"""
    sorted_sigs = sorted(signals, key=lambda x: x.get("score_final", 0), reverse=True)
    return [
        {
            "entity_name": s.get("entity_name", ""),
            "source": s.get("source", ""),
            "source_url": s.get("source_url", ""),
            "summary_zh": s.get("summary_zh", ""),
            "score_final": s.get("score_final", 0),
            "signal_type": s.get("signal_type", ""),
            "team_origin": s.get("team_origin", "unknown"),
        }
        for s in sorted_sigs[:n]
    ]


def _compute_trend(signals: list[dict]) -> str:
    """比较近3天 vs 3-7天前的信号量，返回 'up'/'stable'/'down'"""
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=3)

    recent_count = 0
    older_count = 0

    for s in signals:
        try:
            pub = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= recent_cutoff:
                recent_count += 1
            else:
                older_count += 1
        except Exception:
            continue

    if older_count == 0:
        return "up" if recent_count > 0 else "stable"

    ratio = recent_count / older_count
    if ratio > 1.3:
        return "up"
    elif ratio < 0.7:
        return "down"
    return "stable"


def _signal_type_distribution(signals: list[dict]) -> dict:
    """统计各信号类型的数量分布"""
    dist = defaultdict(int)
    for s in signals:
        st = s.get("signal_type", "company_news")
        dist[st] += 1
    return dict(dist)
