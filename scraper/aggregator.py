"""
赛道聚合器
将评分后的信号聚合为赛道维度的数据
生成首页展示所需的 tracks.json
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone


def aggregate_tracks(signals: list[dict]) -> list[dict]:
    """
    输入：评分后的信号列表
    输出：按赛道聚合的赛道数据列表（用于首页雷达）
    """
    track_signals = defaultdict(list)
    for s in signals:
        track = s.get("track")
        if track:
            track_signals[track].append(s)

    tracks = []
    for track_name, track_sigs in track_signals.items():
        if not track_sigs:
            continue

        track_score = _compute_track_score(track_sigs)
        top_signals = _get_top_signals(track_sigs, n=5)

        tracks.append({
            "name": track_name,
            "score": track_score,
            "project_count": len(track_sigs),
            "top_signals": top_signals,
            "trend": _compute_trend(track_sigs),
            "signal_type_dist": _signal_type_distribution(track_sigs),
        })

    # 按赛道分数降序排列
    tracks.sort(key=lambda x: x["score"], reverse=True)
    return tracks


def _compute_track_score(signals: list[dict]) -> float:
    """
    赛道综合热度分（归一化到 8.0-10.0 区间）

    = 近7天入榜项目数 × 0.4
    + 项目平均分       × 0.4
    + 跨源提及频率     × 0.2
    → 归一化
    """
    count = len(signals)
    avg_score = sum(s.get("score_final", 0) for s in signals) / count if count else 0

    # 计算信源多样性（出现几个不同信源）
    sources = set(s.get("source", "") for s in signals)
    source_diversity = len(sources)

    # 原始综合分
    raw = (
        min(count, 20) / 20 * 0.4 +    # 项目数量，上限20
        min(avg_score, 10) / 10 * 0.4 + # 平均分
        min(source_diversity, 4) / 4 * 0.2  # 信源多样性
    )  # 0-1

    # 归一化到 8.0-10.0
    track_score = 8.0 + raw * 2.0
    return round(track_score, 1)


def _get_top_signals(signals: list[dict], n: int = 5) -> list[dict]:
    """返回评分最高的 n 条信号的精简信息"""
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
    """
    简单趋势判断：对比近3天 vs 3-7天前的信号数量
    返回 'up' / 'stable' / 'down'
    """
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=3)

    recent_count = 0
    older_count = 0

    for s in signals:
        try:
            pub = datetime.fromisoformat(
                s["published_at"].replace("Z", "+00:00")
            )
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
