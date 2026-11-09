"""
毫秒级本地正则黑名单过滤器（Pre-LLM Filter）。

在进入卖家主页采集、图片下载和大模型分析之前，先用本地正则对商品标题/描述
做一次一票否决。命中任意黑名单词条的商品会直接生成一条 rejected 分析结果，
不再消耗任何 LLM Token，也不会触发推送。

可通过环境变量控制：
- PRE_LLM_FILTER_ENABLED=true|false
- PRE_LLM_FILTER_EXTRA_KEYWORDS=词1,词2,词3
"""
from __future__ import annotations

import os
import re
from typing import Iterable, Optional


BLACKLIST_GROUPS: dict[str, tuple[str, ...]] = {
    "引流回收话术": (
        "回收",
        "高价收",
        "置换",
        "以旧换新",
        "估价",
        "看图询价",
        "价格勿拍",
        "标价虚拟",
        "仅展示",
        "同行勿扰",
        "主页有惊喜",
        "加微",
        "V信",
    ),
    "整机贩子话术": (
        "整机出售",
        "支持定制",
        "全新组装",
        "网吧淘汰大批",
        "量大从优",
        "鲁大师跑分",
        "吃鸡神机",
    ),
    "假配件陷阱": (
        "仅盒子",
        "空盒",
        "包装盒",
        "散热器外壳",
        "坏卡",
        "亮机卡",
        "尸体",
        "点不亮",
        "出租",
        "定金",
    ),
}

TEXT_FIELDS = (
    "商品标题",
    "商品描述",
    "商品详情",
    "宝贝描述",
    "描述",
    "title",
    "desc",
    "description",
)

_COMPILED_GROUPS: dict[str, tuple[re.Pattern[str], ...]] = {
    group: tuple(re.compile(re.escape(word), re.IGNORECASE) for word in words)
    for group, words in BLACKLIST_GROUPS.items()
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def _extra_keywords() -> tuple[str, ...]:
    raw = os.getenv("PRE_LLM_FILTER_EXTRA_KEYWORDS", "")
    return tuple(
        item.strip()
        for item in re.split(r"[,，\n]+", raw)
        if item.strip()
    )


def _compile_extra() -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(re.escape(word), re.IGNORECASE) for word in _extra_keywords())


def collect_product_text(record: dict) -> str:
    """从最终记录中提取所有可能包含标题/描述的文本。"""
    item = record.get("商品信息") or {}
    fragments: list[str] = []
    if isinstance(item, dict):
        for field in TEXT_FIELDS:
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                fragments.append(value.strip())
    return "\n".join(fragments)


def _match_group(
    text: str,
    patterns: Iterable[re.Pattern[str]],
) -> list[str]:
    hits: list[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            hits.append(match.group(0))
    return hits


def evaluate_pre_llm_filter(
    record: dict,
    *,
    enabled: Optional[bool] = None,
) -> Optional[dict]:
    """
    返回 None 表示放行；返回 dict 表示命中黑名单，直接作为 ai_analysis 落盘。

    结果结构同时兼容项目现有的 AI 结果字段（is_recommended / reason /
    risk_tags / criteria_analysis），并额外携带 filter_hit 等调试字段。
    """
    if enabled is None:
        enabled = _env_bool("PRE_LLM_FILTER_ENABLED", True)
    if not enabled:
        return None

    text = collect_product_text(record)
    if not text:
        return None

    matched: list[tuple[str, str]] = []
    for group, patterns in _COMPILED_GROUPS.items():
        for word in _match_group(text, patterns):
            matched.append((group, word))
    for pattern in _compile_extra():
        match = pattern.search(text)
        if match:
            matched.append(("自定义扩展", match.group(0)))

    if not matched:
        return None

    seen: set[tuple[str, str]] = set()
    keywords: list[str] = []
    groups: list[str] = []
    for group, word in matched:
        key = (group, word.lower())
        if key in seen:
            continue
        seen.add(key)
        if word not in keywords:
            keywords.append(word)
        if group not in groups:
            groups.append(group)

    keyword_text = "、".join(keywords[:10])
    group_text = "、".join(groups)
    reason = f"[奸商/引流贴拦截] 命中{group_text}黑名单词：{keyword_text}"

    return {
        "prompt_version": "pre-llm-filter-v1",
        "analysis_source": "pre_llm_filter",
        "is_recommended": False,
        "score": 0,
        "seller_type": "职业奸商",
        "warranty_status": "不明",
        "bargain_level": "溢价坑",
        "reason": reason,
        "risk_tags": ["pre_llm_blacklist", *groups],
        "criteria_analysis": {
            "seller_type": {
                "status": "FAIL",
                "persona": "职业奸商",
                "comment": reason,
                "analysis_details": {
                    "filter_groups": groups,
                    "filter_keywords": keywords,
                },
            },
            "price_check": {
                "status": "SKIPPED",
                "comment": "本地黑名单已一票否决，未调用大模型。",
            },
        },
        "filter_hit": True,
        "filter_groups": groups,
        "filter_keywords": keywords,
    }
