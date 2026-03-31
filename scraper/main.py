"""
主调度器
每次运行流程：
  1. 从各信源采集原始信号
  2. 去重（按 source_url）
  3. LLM 评分 + 分类 + 摘要
  4. 跨源加分
  5. 赛道聚合（含 LLM 赛道摘要 + source_breakdown）
  6. 写出 data/signals.json 和 data/tracks.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env（本地开发时使用，GitHub Actions 使用环境变量）
load_dotenv()

# 项目根目录
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def main():
    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        print("错误：未找到 KIMI_API_KEY 环境变量")
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN")  # 可选，提升速率限制

    print("=" * 50)
    print(f"AI Radar 数据采集开始 - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    # ── 步骤 1：采集 ──────────────────────────────
    raw_signals = []

    print("\n[1/5] 采集各信源数据...")

    from scraper.sources import github_trending, hackernews, techcrunch, arxiv_ai
    from scraper.sources import kr36, wechat_rss, astock_ai

    sources = [
        ("GitHub",      github_trending.fetch, {"github_token": github_token}),
        ("HackerNews",  hackernews.fetch,       {}),
        ("TechCrunch",  techcrunch.fetch,        {}),
        ("ArXiv",       arxiv_ai.fetch,          {}),
        ("36氪",        kr36.fetch,              {}),
        ("微信公众号",  wechat_rss.fetch,        {}),
        ("A股AI动态",   astock_ai.fetch,         {}),
    ]

    for source_name, fetch_fn, kwargs in sources:
        try:
            results = fetch_fn(**kwargs)
            raw_signals.extend(results)
            print(f"  ✓ {source_name}: {len(results)} 条")
        except Exception as e:
            print(f"  ✗ {source_name} 采集失败: {e}")

    print(f"\n  采集总计: {len(raw_signals)} 条原始信号")

    # ── 步骤 2：去重 ──────────────────────────────
    print("\n[2/5] 去重...")
    seen_urls = set()
    deduped = []
    for s in raw_signals:
        url = s.get("source_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(s)

    print(f"  去重后: {len(deduped)} 条")

    # ── 步骤 3：LLM 评分 ──────────────────────────
    print(f"\n[3/5] LLM 评分（共 {len(deduped)} 条）...")
    from scraper.scorer import score_signals
    scored_signals = score_signals(deduped, api_key)

    # ── 步骤 4：跨源加分 ──────────────────────────
    print("\n[4/5] 跨源加分...")
    from scraper.scorer import apply_cross_source_bonus
    scored_signals = apply_cross_source_bonus(scored_signals)

    # 按最终分数降序排列
    scored_signals.sort(key=lambda x: x.get("score_final", 0), reverse=True)

    # ── 步骤 5：赛道聚合 ──────────────────────────
    print("\n[5/5] 赛道聚合（含 LLM 摘要生成）...")
    from scraper.aggregator import aggregate_tracks
    tracks = aggregate_tracks(scored_signals, api_key=api_key)

    # ── 写出 JSON ─────────────────────────────────
    generated_at = datetime.now(timezone.utc).isoformat()

    signals_output = {
        "generated_at": generated_at,
        "total": len(scored_signals),
        "signals": scored_signals
    }

    tracks_output = {
        "generated_at": generated_at,
        "total": len(tracks),
        "tracks": tracks
    }

    signals_path = DATA_DIR / "signals.json"
    tracks_path = DATA_DIR / "tracks.json"

    with open(signals_path, "w", encoding="utf-8") as f:
        json.dump(signals_output, f, ensure_ascii=False, indent=2)

    with open(tracks_path, "w", encoding="utf-8") as f:
        json.dump(tracks_output, f, ensure_ascii=False, indent=2)

    # ── 统计摘要 ──────────────────────────────────
    print("\n" + "=" * 50)
    print("采集完成")
    print(f"  信号总数: {len(scored_signals)}")
    print(f"  覆盖赛道: {len(tracks)}")
    print(f"  输出文件: {signals_path}")
    print(f"           {tracks_path}")

    if tracks:
        print("\n  赛道热度 Top 5:")
        for t in tracks[:5]:
            trend_icon = {"up": "↑", "down": "↓", "stable": "→"}.get(t["trend"], "→")
            print(f"    {trend_icon} {t['name']}: {t['score']} ({t['project_count']} 条信号)")

    print("=" * 50)


if __name__ == "__main__":
    main()
