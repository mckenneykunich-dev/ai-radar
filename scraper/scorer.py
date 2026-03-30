"""
LLM 评分管道
每条信号调用 Kimi (Moonshot AI) 一次，完成：
  1. 赛道分类
  2. 三维度质量评分（0-1分 × 3）
  3. 一句话中文摘要（≤80字）
  4. 团队来源判断
  5. 信号类型判断
同时计算规则侧评分（信号强度 + 时间衰减）
"""

import json
import os
import time
import math
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from openai import OpenAI

TRACKS = [
    "AI助理", "AI Coding", "AI视频", "AI医疗", "AI金融",
    "AI营销", "AI工业", "AI安全", "AI硬件", "AI4S",
    "具身智能", "自动驾驶", "基础模型", "AI基础设施"
]

SIGNAL_TYPES = [
    "funding", "product_launch", "research",
    "market_trend", "company_news", "regulatory"
]

SCORING_PROMPT = """你是一位专注于AI赛道的投资分析师。请分析以下内容并返回严格的JSON格式结果。

内容信息：
来源平台：{source}
标题：{title}
描述：{description}

请返回以下JSON（不要返回任何其他内容，不要加markdown代码块）：
{{
  "track": "从以下选项中选择最匹配的赛道，如果不属于AI相关内容或投资价值极低则返回null。选项：{tracks}",
  "signal_type": "从以下选项中选择最匹配的信号类型：{signal_types}",
  "entity_name": "核心主体名称（项目名/产品名/公司名），尽量简短，如无明确主体则提取最相关名词",
  "quality": {{
    "novelty": 0.0,
    "market_potential": 0.0,
    "strategic_value": 0.0
  }},
  "summary_zh": "一句话中文摘要，不超过80字，说明是什么、有何价值",
  "team_origin": "chinese 或 non-chinese 或 unknown"
}}

quality 三个字段各0-1分（0.1为单位），评分标准：
- novelty：技术/产品是否提出新方法、新范式（1.0=颠覆性，0.5=有改进，0.1=跟风）
- market_potential：是否有真实市场需求和付费意愿（1.0=已有大规模商业化，0.5=需求明确，0.1=概念验证）
- strategic_value：对所在赛道格局的影响程度（1.0=赛道定义者，0.5=重要玩家，0.1=边缘项目）"""


def score_signals(raw_signals: List[dict], api_key: str) -> List[dict]:
    """
    对原始信号列表进行 LLM 评分
    返回带完整评分信息的信号列表
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1"
    )
    scored = []

    for i, signal in enumerate(raw_signals):
        print(f"[Scorer] 处理 {i+1}/{len(raw_signals)}: {signal['title'][:50]}")
        try:
            llm_result = _call_llm(client, signal)
            if llm_result is None or llm_result.get("track") is None:
                # 非 AI 相关，跳过
                continue

            score_raw, score_final = _calculate_score(signal, llm_result)

            scored.append({
                # 来源信息
                "source": signal["source"],
                "source_url": signal["source_url"],
                "published_at": signal["published_at"],
                # LLM 输出
                "entity_name": llm_result.get("entity_name", signal["title"][:50]),
                "track": llm_result["track"],
                "signal_type": llm_result.get("signal_type", "company_news"),
                "summary_zh": llm_result.get("summary_zh", ""),
                "team_origin": llm_result.get("team_origin", "unknown"),
                # 评分
                "score_raw": score_raw,
                "score_final": score_final,
                "quality": llm_result.get("quality", {}),
                # 原始元数据
                "metadata": signal.get("metadata", {}),
            })

            time.sleep(0.3)  # 避免触发速率限制

        except Exception as e:
            print(f"[Scorer] 评分失败: {e}")
            continue

    print(f"[Scorer] 评分完成，{len(raw_signals)} 条 → {len(scored)} 条入库")
    return scored


def _call_llm(client: OpenAI, signal: dict) -> Optional[dict]:
    """调用 Kimi moonshot-v1-8k 进行评分，带重试"""
    prompt = SCORING_PROMPT.format(
        source=signal["source"],
        title=signal["title"][:300],
        description=signal["description"][:500],
        tracks="、".join(TRACKS),
        signal_types="、".join(SIGNAL_TYPES),
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="moonshot-v1-8k",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.choices[0].message.content.strip()

            # 清理可能的 markdown 代码块
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            print(f"[Scorer] JSON 解析失败 (attempt {attempt+1}): {e}")
            time.sleep(1)
        except Exception as e:
            err_str = str(e)
            if "rate_limit" in err_str.lower() or "429" in err_str:
                print("[Scorer] 速率限制，等待60秒...")
                time.sleep(60)
            else:
                print(f"[Scorer] LLM 调用失败 (attempt {attempt+1}): {e}")
                time.sleep(2)

    return None


def _calculate_score(signal: dict, llm_result: dict) -> Tuple[float, float]:
    """
    计算信号原始分和衰减后最终分

    原始分 = 信号强度（0-7）+ 内容质量（0-3）= 0-10
    最终分 = 原始分 × 时间衰减系数
    """
    # --- 信号强度（规则侧）---
    platform_score = _platform_score(signal)          # 0-3
    cross_source_bonus = 0                             # 主流程中处理跨源加分
    funding_bonus = _funding_bonus(signal, llm_result) # 0-2
    signal_strength = min(platform_score + cross_source_bonus + funding_bonus, 7)

    # --- 内容质量（LLM侧）---
    quality = llm_result.get("quality", {})
    content_quality = (
        quality.get("novelty", 0) +
        quality.get("market_potential", 0) +
        quality.get("strategic_value", 0)
    )  # 0-3

    score_raw = round(signal_strength + content_quality, 1)

    # --- 时间衰减 ---
    try:
        pub_str = signal["published_at"].replace("Z", "+00:00")
        pub_dt = datetime.fromisoformat(pub_str)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        days = max(0, (datetime.now(timezone.utc) - pub_dt).days)
    except Exception:
        days = 3  # 无法解析时间，默认3天

    decay = 1 / math.pow(days + 1, 0.5)
    score_final = round(score_raw * decay, 1)

    return score_raw, score_final


def _platform_score(signal: dict) -> float:
    """根据平台热度指标计算 0-3 分"""
    meta = signal.get("metadata", {})
    source = signal.get("source", "")

    if source == "github":
        stars = meta.get("stars", 0)
        return min(3.0, math.log10(max(stars, 1)) * 1.0)

    elif source == "hackernews":
        hn_score = meta.get("hn_score", 0)
        return min(3.0, math.log10(max(hn_score, 1)) * 1.3)

    elif source == "techcrunch":
        return 1.5

    elif source == "arxiv":
        return 1.0

    return 1.0


def _funding_bonus(signal: dict, llm_result: dict) -> float:
    """融资信号额外加分 0-2 分"""
    if llm_result.get("signal_type") != "funding":
        return 0

    meta = signal.get("metadata", {})
    amount = meta.get("funding_amount", 0)
    if not amount:
        return 0.5  # 有融资事件但金额未知，给 0.5

    if amount >= 10000:   # 万元单位，1亿=10000万
        return 2.0
    elif amount >= 1000:
        return 1.0
    else:
        return 0.5


def apply_cross_source_bonus(signals: list) -> list:
    """
    对同一实体在多个信源出现的情况给予加分
    在 main.py 中对全部信号处理完后调用
    """
    from collections import defaultdict
    entity_count = defaultdict(int)

    for s in signals:
        name = s.get("entity_name", "").lower().strip()
        if name:
            entity_count[name] += 1

    for s in signals:
        name = s.get("entity_name", "").lower().strip()
        count = entity_count.get(name, 1)
        bonus = min((count - 1) * 0.5, 2.0)
        s["score_raw"] = round(s["score_raw"] + bonus, 1)
        s["score_final"] = round(s["score_final"] + bonus * 0.8, 1)

    return signals
