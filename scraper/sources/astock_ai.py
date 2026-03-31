"""
A股 AI 上市公司动态采集
通过 AkShare 获取重点 AI 上市公司近期公告与新闻
免费方案，无需 API Key
"""

import time
from datetime import datetime, timedelta, timezone
from typing import List

# A股重点 AI 相关上市公司（股票代码 + 公司名）
AI_COMPANIES = [
    ("002230", "科大讯飞"),
    ("688256", "寒武纪"),
    ("002415", "海康威视"),
    ("603019", "中科曙光"),
    ("000977", "浪潮信息"),
    ("688111", "金山办公"),
    ("688088", "虹软科技"),
    ("688327", "云从科技"),
    ("300033", "同花顺"),
    ("600588", "用友网络"),
    ("002410", "广联达"),
    ("688008", "澜起科技"),
    ("688099", "晶晨股份"),
    ("300496", "中科星图"),
    ("688081", "兆易创新"),
]

# AI 相关关键词（用于新闻过滤）
AI_KEYWORDS = [
    "人工智能", "ai", "大模型", "llm", "智能", "算法", "深度学习",
    "机器学习", "语言模型", "生成式", "神经网络", "数字化", "自动化",
    "agent", "推理芯片", "gpu", "npu", "算力", "云计算",
]


def fetch() -> List[dict]:
    """
    采集重点 AI 上市公司的近期新闻动态
    返回标准化信号列表
    """
    try:
        import akshare as ak
    except ImportError:
        print("[A股] AkShare 未安装，跳过。请运行: pip3 install akshare")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    signals = []
    seen_urls = set()

    for code, name in AI_COMPANIES:
        try:
            # 获取该股票的近期新闻（东方财富数据）
            df = ak.stock_news_em(symbol=code)

            if df is None or df.empty:
                continue

            for _, row in df.iterrows():
                # 字段：关键词 / 新闻标题 / 新闻内容 / 发布时间 / 新闻来源 / 新闻链接
                title = str(row.get("新闻标题", ""))
                content = str(row.get("新闻内容", ""))[:400]
                pub_date_str = str(row.get("发布时间", ""))
                url = str(row.get("新闻链接", ""))
                source_name = str(row.get("新闻来源", ""))

                if not title or not url or url in seen_urls:
                    continue

                # 时间过滤
                try:
                    pub_dt = datetime.strptime(pub_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass

                # AI 相关性过滤
                text = f"{title} {content}".lower()
                if not any(kw in text for kw in AI_KEYWORDS):
                    continue

                seen_urls.add(url)
                signals.append({
                    "source": "astock",
                    "source_url": url,
                    "title": f"[{name}] {title}",
                    "description": content,
                    "published_at": pub_date_str,
                    "metadata": {
                        "company_name": name,
                        "stock_code": code,
                        "news_source": source_name,
                    }
                })

            time.sleep(0.5)  # 控制请求频率

        except Exception as e:
            print(f"  [A股] {name}({code}) 采集失败: {e}")
            continue

    print(f"[A股] 采集完成，共 {len(signals)} 条（覆盖 {len(AI_COMPANIES)} 家公司）")
    return signals
