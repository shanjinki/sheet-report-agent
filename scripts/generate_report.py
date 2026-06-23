#!/usr/bin/env python3
"""Generate a self-contained HTML business report from a spreadsheet.

This baseline generator is deterministic so agents can reliably start from a
solid report, then refine the narrative and styling for a specific user.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - user environment guard
    raise SystemExit(
        "Missing dependency: pandas. Install with `pip install pandas openpyxl`."
    ) from exc


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_table import build_profile, read_table  # noqa: E402


STYLE_THEMES = {
    "command-center": {
        "name": "Command Center",
        "body_class": "theme-command",
        "stage": "dark",
        "accent": "#38bdf8",
    },
    "boardroom-light": {
        "name": "Boardroom Light",
        "body_class": "theme-light",
        "stage": "light",
        "accent": "#1d4ed8",
    },
    "retail-pulse": {
        "name": "Retail Pulse",
        "body_class": "theme-retail",
        "stage": "light",
        "accent": "#f97316",
    },
    "ops-ledger": {
        "name": "Ops Ledger",
        "body_class": "theme-ledger",
        "stage": "dark",
        "accent": "#34d399",
    },
    "editorial-brief": {
        "name": "Editorial Brief",
        "body_class": "theme-editorial",
        "stage": "light",
        "accent": "#9f6b44",
    },
    "data-studio": {
        "name": "Data Studio",
        "body_class": "theme-studio",
        "stage": "dark",
        "accent": "#8b5cf6",
    },
}


STATUS_RULES = [
    ("discarded", ["废弃", "discard", "cancel", "取消", "作废", "closed-wontfix"]),
    ("paused", ["暂停", "paused", "挂起", "suspend"]),
    ("released", ["已发布", "released", "done", "已上线", "完成", "closed"]),
    ("backlog", ["backlog", "待排期", "待办", "未开始"]),
    ("tech_review", ["技术评审", "technical review", "tech review"]),
    ("prd_review", ["prd评审", "prd review", "产品评审"]),
    ("scheduled", ["已排期", "scheduled", "计划中"]),
    ("implementation", ["实现中", "开发中", "in implementation", "doing"]),
    ("testing", ["已提测", "ready for test", "sit", "uat", "测试"]),
    ("ready_release", ["待发布", "ready for release"]),
]


FUNNEL_ORDER = [
    ("backlog", "Backlog/待排期", "#fbbf24", "等待排期的需求积压"),
    ("tech_review", "技术评审", "#38bdf8", "正在技术评审阶段"),
    ("prd_review", "PRD评审", "#818cf8", "PRD 或方案评审中"),
    ("scheduled", "已排期", "#c084fc", "已进入计划"),
    ("implementation", "实现中", "#22d3ee", "开发实现中"),
    ("testing", "测试验证", "#2dd4bf", "已提测、SIT 或 UAT"),
    ("ready_release", "待发布", "#f472b6", "等待上线发布"),
    ("paused", "暂停", "#a78bfa", "暂时搁置"),
    ("released", "已发布", "#34d399", "已完成并上线"),
]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 1)


def compact_number(value: float | int | str | None) -> str:
    """Format a number with 万/亿 abbreviation. Handles str input safely."""
    if value is None:
        return "-"
    try:
        if isinstance(value, str):
            value = float(value)
        value = float(value)
    except (TypeError, ValueError):
        return "-"
    if math.isnan(value) or math.isinf(value):
        return "-"
    if abs(value) >= 100000000:
        return f"{value / 100000000:.1f}亿"
    if abs(value) >= 10000:
        return f"{value / 10000:.1f}万"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.1f}"
    return f"{int(value):,}"


def normalized_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def find_col(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {col: normalized_text(col) for col in columns}
    alias_norm = [normalized_text(alias) for alias in aliases]
    for alias in alias_norm:
        for col, norm in normalized.items():
            if norm == alias:
                return col
    for col, norm in normalized.items():
        if any(alias in norm or norm in alias for alias in alias_norm):
            return col
    return None


def classify_status(value: Any) -> str:
    text = normalized_text(value)
    for group, keys in STATUS_RULES:
        if any(normalized_text(key) in text for key in keys):
            return group
    return "other"


def owner_tokens(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = re.split(r"[,，、/;；\s]+", text)
    return [p for p in parts if p and p.lower() not in {"nan", "none"}]


def health_for_rate(rate: float) -> str:
    if rate >= 50:
        return "green"
    if rate >= 25:
        return "amber"
    return "red"


def read_any_table(input_path: Path, sheet: str | None = None):
    table = read_table(input_path, sheet)
    return table.frame, table


def infer_default_style(domain: str) -> str:
    if domain == "devops-demand-pool":
        return "command-center"
    if domain in {"ecommerce-orders", "ecommerce-reviews"}:
        return "retail-pulse"
    if domain == "erp-inventory":
        return "ops-ledger"
    if domain in {"survey-feedback", "hr-attendance"}:
        return "editorial-brief"
    if domain in {"finance-expense", "crm-pipeline", "support-tickets"}:
        return "boardroom-light"
    return "data-studio"


def make_kpi(label: str, value: str, sub: str, tone: str = "blue") -> dict[str, str]:
    return {"label": label, "value": value, "sub": sub, "tone": tone}


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "-", "--"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    multiplier = 1.0
    if "亿" in text:
        multiplier = 100000000.0
    elif "万" in text:
        multiplier = 10000.0
    cleaned = re.sub(r"[,\s￥¥$%元人民币亿万]", "", text)
    if not cleaned or cleaned in {"-", "."}:
        return None
    try:
        number = float(cleaned) * multiplier
    except ValueError:
        return None
    return -number if negative else number


def numeric_series(frame: "pd.DataFrame", col: str | None) -> "pd.Series":
    if not col or col not in frame:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[col].map(parse_number), errors="coerce")


def ratio_percent_series(frame: "pd.DataFrame", col: str | None) -> "pd.Series":
    series = numeric_series(frame, col)
    clean = series.dropna()
    if clean.empty:
        return series
    # Ratio exports may be 0.42 or 42%. Normalize both to percentage points.
    if clean.abs().quantile(0.95) <= 1.5:
        return series * 100
    return series


def find_metric_col(
    columns: list[str], aliases: list[str], exclude_tokens: list[str] | None = None
) -> str | None:
    exclude = [normalized_text(token) for token in (exclude_tokens or [])]
    candidates = [col for col in columns if not any(token in normalized_text(col) for token in exclude)]
    return find_col(candidates, aliases)


def period_sort_key(value: Any) -> tuple[int, int, str]:
    text = str(value or "").strip()
    normalized = text.replace(" ", "")
    match = re.search(r"(20\d{2})[年\-_/\.]*[Qq]([1-4])", normalized)
    if not match:
        match = re.search(r"(20\d{2})年?第?([1-4])季", normalized)
    if match:
        return (int(match.group(1)), int(match.group(2)), text)
    match = re.search(r"(20\d{2})[-_/年\.](\d{1,2})", normalized)
    if match:
        month = max(1, min(12, int(match.group(2))))
        return (int(match.group(1)), (month - 1) // 3 + 1, text)
    parsed = pd.to_datetime(pd.Series([text]), errors="coerce").iloc[0]
    if not pd.isna(parsed):
        return (int(parsed.year), int((parsed.month - 1) // 3 + 1), text)
    return (9999, 9, text)


def safe_rate(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 1)


def format_rate(value: float | None, suffix: str = "%") -> str:
    if value is None or math.isnan(value):
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}{suffix}"


def risk_text_level(value: Any) -> str:
    text = normalized_text(value)
    if not text:
        return ""
    if any(token in text for token in ["高", "high", "严重", "critical", "red"]):
        return "high"
    if any(token in text for token in ["中", "medium", "moderate", "amber", "黄"]):
        return "medium"
    if any(token in text for token in ["低", "low", "green", "绿"]):
        return "low"
    return ""


def requirement_focus(requirement: str) -> list[str]:
    text = normalized_text(requirement)
    mapping = [
        ("绩效回顾", ["绩效", "经营", "表现", "performance"]),
        ("趋势变化", ["趋势", "季度", "月度", "同比", "环比", "trend"]),
        ("风险评估", ["风险", "异常", "预警", "risk"]),
        ("行动规划", ["行动", "建议", "规划", "next", "action"]),
        ("管理层汇报", ["管理层", "汇报", "复盘", "brief"]),
    ]
    focus = [label for label, keys in mapping if any(key in text for key in keys)]
    return focus or ["经营概览", "风险提示", "行动建议"]


def parse_datetime_series(frame: "pd.DataFrame", col: str | None) -> "pd.Series":
    if not col or col not in frame:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(frame[col], errors="coerce")


def text_series(frame: "pd.DataFrame", col: str | None, default: str = "未识别") -> "pd.Series":
    if not col or col not in frame:
        return pd.Series([default] * len(frame), index=frame.index)
    return frame[col].fillna(default).astype(str).str.strip().replace("", default)


def value_counts_rows(series: "pd.Series", total: int, limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for name, count in series.fillna("未识别").astype(str).value_counts().head(limit).items():
        rows.append({"name": str(name), "value": int(count), "share": pct(int(count), total)})
    return rows


def amount_mix_rows(
    frame: "pd.DataFrame", group_col: str | None, amount_col: str | None, limit: int = 8
) -> list[dict[str, Any]]:
    if not group_col or group_col not in frame:
        return []
    working = pd.DataFrame(
        {
            "group": text_series(frame, group_col, "未分类"),
            "amount": numeric_series(frame, amount_col) if amount_col else pd.Series([1] * len(frame)),
        }
    ).dropna(subset=["amount"])
    if working.empty:
        return []
    grouped = working.groupby("group")["amount"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    total = float(grouped["sum"].sum())
    rows = []
    for name, row in grouped.head(limit).iterrows():
        rows.append(
            {
                "name": str(name),
                "value": round(float(row["sum"]), 2),
                "share": pct(float(row["sum"]), total),
                "detail": f"{int(row['count'])} 条记录",
            }
        )
    return rows


def time_trend_rows(
    frame: "pd.DataFrame", date_col: str | None, value_col: str | None = None, limit: int = 12
) -> list[dict[str, Any]]:
    dates = parse_datetime_series(frame, date_col)
    if dates.dropna().empty:
        return []
    values = numeric_series(frame, value_col) if value_col else pd.Series([1] * len(frame), index=frame.index)
    trend_frame = pd.DataFrame({"date": dates, "value": values}).dropna()
    if trend_frame.empty:
        return []
    grouped = (
        trend_frame.set_index("date")
        .groupby(pd.Grouper(freq="ME"))["value"]
        .agg(["sum", "count"])
        .dropna()
        .tail(limit)
    )
    rows = []
    for date, row in grouped.iterrows():
        rows.append(
            {
                "name": date.strftime("%Y-%m"),
                "value": round(float(row["sum"]), 2),
                "share": 0,
                "detail": f"{int(row['count'])} 条记录",
            }
        )
    return rows


def table_section(title: str, columns: list[dict[str, str]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"kind": "table", "title": title, "columns": columns, "rows": rows}


def bars_section(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"kind": "bars", "title": title, "rows": rows}


def cards_section(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"kind": "cards", "title": title, "rows": rows}


def build_devops_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    """Generate a domain-specific report for DevOps demand pool data."""
    # Empty DataFrame protection
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "DevOps需求池")

    columns = list(frame.columns)
    status_col = find_col(columns, ["状态", "status"])
    category_col = find_col(columns, ["一级分类", "业务线", "模块", "系统", "需求分类"])
    subcategory_col = find_col(columns, ["二级分类", "三级分类", "业务专项", "专题"])
    special_col = find_col(columns, ["业务专项", "专项", "专题", "父工作项"])
    owner_col = find_col(columns, ["经办人", "负责人", "assignee", "owner"])
    priority_col = find_col(columns, ["优先级", "priority", "业务优先级"])
    title_col = find_col(columns, ["标题", "需求标题", "summary", "name"])
    planned_col = find_col(columns, ["预计上线", "预计结束", "计划完成"])
    created_col = find_col(columns, ["创建时间", "提出时间"])

    working = frame.copy()
    if status_col:
        working["_status_group"] = working[status_col].map(classify_status)
    else:
        working["_status_group"] = "other"
    active = working[working["_status_group"] != "discarded"].copy()
    effective = len(active)

    counts = Counter(active["_status_group"])
    released = counts["released"]
    backlog = counts["backlog"]
    paused = counts["paused"]
    in_progress = max(effective - released - backlog - paused, 0)
    total_rows = len(working)
    discarded = total_rows - effective

    kpis = [
        make_kpi("有效需求", compact_number(effective), f"源数据 {total_rows} 条，剔除废弃 {discarded} 条", "blue"),
        make_kpi("已发布", compact_number(released), f"发布率 {pct(released, effective)}%", "green"),
        make_kpi("Backlog 积压", compact_number(backlog), f"占有效需求 {pct(backlog, effective)}%", "orange"),
        make_kpi("进行中", compact_number(in_progress), "评审、排期、开发、测试、待发布", "cyan"),
        make_kpi("暂停", compact_number(paused), f"占有效需求 {pct(paused, effective)}%", "red"),
    ]

    category_stats = []
    if category_col:
        for name, group in active.groupby(active[category_col].fillna("未分类")):
            status_counts = Counter(group["_status_group"])
            total = len(group)
            rate = pct(status_counts["released"], total)
            owners = top_owner_list(group, owner_col, 3)
            category_stats.append(
                {
                    "name": str(name) or "未分类",
                    "total": total,
                    "released": status_counts["released"],
                    "backlog": status_counts["backlog"],
                    "paused": status_counts["paused"],
                    "in_progress": max(
                        total
                        - status_counts["released"]
                        - status_counts["backlog"]
                        - status_counts["paused"],
                        0,
                    ),
                    "rate": rate,
                    "backlog_rate": pct(status_counts["backlog"], total),
                    "health": health_for_rate(rate),
                    "owners": owners,
                }
            )
    category_stats.sort(key=lambda item: (item["rate"], -item["total"]))

    special_stats = []
    special_source = special_col or subcategory_col or category_col
    if special_source:
        grouped_cols = [category_col, special_source] if category_col and category_col != special_source else [special_source]
        for keys, group in active.groupby(grouped_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = ("", keys)
            cat_name = str(keys[0] or "未分类") if len(keys) > 1 else ""
            special_name = str(keys[-1] or "无专项")
            total = len(group)
            if total < 3:
                continue
            status_counts = Counter(group["_status_group"])
            rate = pct(status_counts["released"], total)
            special_stats.append(
                {
                    "category": cat_name,
                    "name": special_name,
                    "total": total,
                    "released": status_counts["released"],
                    "backlog": status_counts["backlog"],
                    "tech_review": status_counts["tech_review"],
                    "paused": status_counts["paused"],
                    "rate": rate,
                    "health": health_for_rate(rate),
                    "owners": top_owner_list(group, owner_col, 4),
                    "items": sample_items(group, title_col, owner_col, 8),
                }
            )
    special_stats.sort(key=lambda item: (item["rate"], -item["total"]))

    funnel = []
    for key, label, color, desc in FUNNEL_ORDER:
        val = counts[key]
        if val or key in {"backlog", "released"}:
            funnel.append(
                {
                    "key": key,
                    "label": label,
                    "value": val,
                    "share": pct(val, effective),
                    "color": color,
                    "desc": desc,
                }
            )

    significant_categories = [
        cat
        for cat in category_stats
        if cat["total"] >= max(20, effective * 0.03)
        and str(cat["name"]).strip() not in {"未分类", "nan", "None", ""}
    ]
    category_focus = significant_categories or category_stats
    top_risk_category = category_focus[0] if category_focus else None
    top_backlog_category = max(category_focus, key=lambda x: x["backlog"], default=None)
    best_category = max(category_focus, key=lambda x: x["rate"], default=None)
    risky_specials = [
        item
        for item in special_stats
        if item["total"] >= 5 and (item["rate"] < 25 or item["backlog"] / max(item["total"], 1) >= 0.6)
    ][:6]

    owner_counts = Counter()
    if owner_col:
        for value in active[owner_col].dropna():
            owner_counts.update(owner_tokens(value))
    top_owners = [{"name": name, "count": count} for name, count in owner_counts.most_common(8)]

    insights = []
    if top_risk_category:
        insights.append(
            f"{top_risk_category['name']}发布率仅 {top_risk_category['rate']}%，在主要分类中风险最高，"
            f"其中 Backlog {top_risk_category['backlog']} 条。"
        )
    if top_backlog_category:
        insights.append(
            f"{top_backlog_category['name']}积压量最高，共 {top_backlog_category['backlog']} 条 Backlog，"
            f"占该分类 {top_backlog_category['backlog_rate']}%。"
        )
    if best_category:
        insights.append(
            f"{best_category['name']}发布率 {best_category['rate']}%，可作为节奏和协作方式的参考样本。"
        )
    if backlog / max(effective, 1) >= 0.35:
        insights.append(
            f"整体 Backlog 占比 {pct(backlog, effective)}%，已经接近或超过三分之一，建议做优先级重排和需求池清理。"
        )
    if counts["tech_review"] >= max(10, effective * 0.05):
        insights.append(
            f"技术评审阶段有 {counts['tech_review']} 条，建议集中协调评审资源，避免评审成为交付瓶颈。"
        )
    while len(insights) < 3:
        insights.append("当前数据已形成可汇报的需求池视图，建议结合业务优先级进一步确认资源投入顺序。")

    risks = build_devops_risks(
        category_stats,
        significant_categories,
        risky_specials,
        top_owners,
        priority_col,
        active,
        special_source,
        status_counts=counts,
        effective=effective,
    )

    assumptions = [
        f"状态字段：{status_col or '未识别'}",
        f"分类字段：{category_col or '未识别'}",
        f"专项字段：{special_source or '未识别'}",
        f"负责人字段：{owner_col or '未识别'}",
    ]
    if planned_col:
        assumptions.append(f"计划日期字段：{planned_col}")
    if created_col:
        assumptions.append(f"创建/提出日期字段：{created_col}")

    return {
        "domain": "devops-demand-pool",
        "title": title or "需求池全景分析报告",
        "subtitle": requirement or "从原始需求明细自动生成的管理层汇报材料",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:5],
        "funnel": funnel,
        "categories": category_stats,
        "specials": special_stats[:24],
        "risks": risks,
        "top_owners": top_owners,
        "assumptions": assumptions,
        "sample_items": sample_items(active, title_col, owner_col, 10),
        "profile": profile,
    }


def top_owner_list(group: "pd.DataFrame", owner_col: str | None, limit: int) -> list[str]:
    if not owner_col or owner_col not in group:
        return []
    counter: Counter[str] = Counter()
    for value in group[owner_col].dropna():
        counter.update(owner_tokens(value))
    return [name for name, _ in counter.most_common(limit)]


def sample_items(
    group: "pd.DataFrame", title_col: str | None, owner_col: str | None, limit: int
) -> list[dict[str, str]]:
    items = []
    if group.empty:
        return items
    focus = group[group["_status_group"].isin(["backlog", "tech_review", "prd_review", "implementation", "testing"])]
    if focus.empty:
        focus = group
    for _, row in focus.head(limit).iterrows():
        items.append(
            {
                "title": str(row.get(title_col, "未命名事项"))[:120] if title_col else "未命名事项",
                "owner": str(row.get(owner_col, ""))[:60] if owner_col else "",
                "status": str(row.get("_status_group", "")),
            }
        )
    return items


def build_devops_risks(
    category_stats: list[dict[str, Any]],
    significant_categories: list[dict[str, Any]],
    risky_specials: list[dict[str, Any]],
    top_owners: list[dict[str, Any]],
    priority_col: str | None,
    active: "pd.DataFrame",
    special_col: str | None,
    status_counts: Counter,
    effective: int,
) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for cat in (significant_categories or category_stats)[:4]:
        if cat["health"] == "red" or cat["backlog_rate"] >= 45:
            risks.append(
                {
                    "level": "high" if cat["health"] == "red" else "medium",
                    "title": f"{cat['name']}交付健康度偏低",
                    "detail": f"总量 {cat['total']} 条，发布率 {cat['rate']}%，Backlog {cat['backlog']} 条。",
                    "action": "安排专项评审，先清理高优先级积压，再决定延期、拆分或暂停。",
                }
            )
    uncategorized = next((cat for cat in category_stats if str(cat["name"]).strip() == "未分类"), None)
    if uncategorized and uncategorized["total"]:
        risks.append(
            {
                "level": "low",
                "title": "未分类需求需要补齐",
                "detail": f"未分类 {uncategorized['total']} 条，其中 Backlog {uncategorized['backlog']} 条。",
                "action": "先补齐一级分类，再进入正式资源和交付复盘口径。",
            }
        )
    for special in risky_specials[:4]:
        risks.append(
            {
                "level": "medium",
                "title": f"{special['name']}专项需治理",
                "detail": f"总量 {special['total']} 条，发布率 {special['rate']}%，Backlog {special['backlog']} 条。",
                "action": "明确负责人、时间表和是否继续投入，避免专项长期挂账。",
            }
        )
    if top_owners:
        busiest = top_owners[0]
        if busiest["count"] >= max(10, effective * 0.05):
            risks.append(
                {
                    "level": "medium",
                    "title": "负责人负载集中",
                    "detail": f"{busiest['name']}关联 {busiest['count']} 条事项，存在响应瓶颈风险。",
                    "action": "复核其真实工作量，并将低优先级事项分流或延期。",
                }
            )
    if priority_col and priority_col in active:
        missing_priority = int(
            active[priority_col].astype(str).str.strip().isin(["", "无", "nan", "None"]).sum()
        )
        if missing_priority:
            risks.append(
                {
                    "level": "medium",
                    "title": "优先级治理需要补齐",
                    "detail": f"{missing_priority} 条有效需求缺少明确业务优先级。",
                    "action": "要求业务侧补充优先级，作为排期和资源分配依据。",
                }
            )
    if special_col and special_col in active:
        missing_special = int(
            active[special_col].astype(str).str.strip().isin(["", "无", "nan", "None"]).sum()
        )
        if missing_special >= max(10, effective * 0.1):
            risks.append(
                {
                    "level": "low",
                    "title": "专项归属不清",
                    "detail": f"{missing_special} 条记录未归入明确专项，影响复盘和资源归因。",
                    "action": "补齐专项标签，至少覆盖高优先级和进行中事项。",
                }
            )
    if status_counts["tech_review"] >= max(10, effective * 0.05):
        risks.append(
            {
                "level": "medium",
                "title": "评审阶段可能形成瓶颈",
                "detail": f"技术评审中 {status_counts['tech_review']} 条。",
                "action": "集中安排评审会，明确一次性通过标准和需补充材料。",
            }
        )
    return risks[:8]


def build_ecommerce_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    """Generate a domain-specific report for ecommerce order data."""
    columns = list(frame.columns)
    rows = len(frame)

    # Detect columns
    date_col = find_col(columns, ["日期", "下单时间", "订单日期", "date", "创建时间"])
    amount_col = find_col(columns, ["金额", "gmv", "支付金额", "销售额", "实付金额", "订单金额"])
    quantity_col = find_col(columns, ["数量", "件数", "销量", "quantity"])
    category_col = find_col(columns, ["品类", "分类", "商品类目", "category", "一级分类"])
    channel_col = find_col(columns, ["渠道", "平台", "channel", "销售平台", "店铺"])
    status_col = find_col(columns, ["状态", "订单状态", "status", "是否退款"])
    product_col = find_col(columns, ["商品名称", "商品", "product", "SKU", "货号"])
    customer_col = find_col(columns, ["客户", "用户", "customer", "买家", "会员"])

    # Clean numeric columns
    numeric_frame = frame.copy()
    if amount_col:
        numeric_frame[amount_col] = pd.to_numeric(numeric_frame[amount_col], errors="coerce")
    if quantity_col:
        numeric_frame[quantity_col] = pd.to_numeric(numeric_frame[quantity_col], errors="coerce")

    # Calculate KPIs
    total_gmv = 0.0
    if amount_col:
        total_gmv = float(numeric_frame[amount_col].dropna().sum())
    total_orders = rows
    avg_order_value = total_gmv / total_orders if total_orders else 0

    # Return rate
    returned_orders = 0
    return_rate = 0.0
    if status_col:
        status_norm = numeric_frame[status_col].astype(str).str.lower()
        returned_orders = int(status_norm.str.contains("退款|退货|refund|return|取消", na=False).sum())
        return_rate = pct(returned_orders, total_orders)
    elif amount_col:
        # Heuristic: negative amounts are returns
        returned_orders = int((numeric_frame[amount_col] < 0).sum())
        return_rate = pct(returned_orders, total_orders)

    kpis = [
        make_kpi("总GMV", compact_number(total_gmv), f"{total_orders} 单", "blue"),
        make_kpi("客单价", compact_number(avg_order_value), "平均订单金额", "green"),
        make_kpi("订单数", compact_number(total_orders), "总成交订单", "orange"),
        make_kpi("退货率", f"{return_rate}%", f"{returned_orders} 单退货", "red"),
    ]

    # GMV trend by date
    gmv_trend = []
    if date_col and amount_col:
        try:
            numeric_frame[date_col] = pd.to_datetime(numeric_frame[date_col], errors="coerce")
            trend = numeric_frame.dropna(subset=[date_col, amount_col])
            if not trend.empty:
                trend = trend.set_index(date_col)
                daily = trend.groupby(pd.Grouper(freq="D"))[amount_col].agg(["sum", "count"]).dropna()
                for date, row in daily.tail(14).iterrows():
                    gmv_trend.append({
                        "period": date.strftime("%m/%d"),
                        "gmv": round(float(row["sum"]), 2),
                        "orders": int(row["count"]),
                    })
        except Exception:
            pass

    # Category contribution
    category_contribution = []
    if category_col and amount_col:
        cat_gmv = numeric_frame.dropna(subset=[amount_col]).groupby(numeric_frame[category_col].fillna("未分类"))[amount_col].agg(["sum", "count"])
        cat_gmv = cat_gmv.sort_values("sum", ascending=False)
        for cat, row in cat_gmv.head(8).iterrows():
            category_contribution.append({
                "name": str(cat),
                "gmv": round(float(row["sum"]), 2),
                "share": pct(float(row["sum"]), total_gmv),
                "orders": int(row["count"]),
            })

    # Channel contribution
    channel_contribution = []
    if channel_col and amount_col:
        ch_gmv = numeric_frame.dropna(subset=[amount_col]).groupby(numeric_frame[channel_col].fillna("未分类"))[amount_col].agg(["sum", "count"])
        ch_gmv = ch_gmv.sort_values("sum", ascending=False)
        for ch, row in ch_gmv.head(8).iterrows():
            channel_contribution.append({
                "name": str(ch),
                "gmv": round(float(row["sum"]), 2),
                "share": pct(float(row["sum"]), total_gmv),
                "orders": int(row["count"]),
            })

    # Insights
    insights = []
    if category_contribution:
        top_cat = category_contribution[0]
        insights.append(
            f"「{top_cat['name']}」贡献 GMV {compact_number(top_cat['gmv'])}，"
            f"占比 {top_cat['share']}%，是核心品类。"
        )
    if channel_contribution:
        top_ch = channel_contribution[0]
        insights.append(
            f"「{top_ch['name']}」是最大销售渠道，GMV {compact_number(top_ch['gmv'])}，"
            f"占比 {top_ch['share']}%。"
        )
    if return_rate >= 10:
        insights.append(f"退货率 {return_rate}%，高于行业常规水平，需关注商品质量或描述准确性。")
    elif return_rate > 0:
        insights.append(f"退货率 {return_rate}%，处于可控范围。")
    if gmv_trend and len(gmv_trend) >= 3:
        recent_gmv = sum(d["gmv"] for d in gmv_trend[-3:]) / 3
        earlier_gmv = sum(d["gmv"] for d in gmv_trend[:3]) / 3 if len(gmv_trend) >= 6 else None
        if earlier_gmv and recent_gmv < earlier_gmv * 0.8:
            insights.append("近 3 日 GMV 均值较前期下滑超过 20%，需关注流量或转化异常。")
        elif earlier_gmv and recent_gmv > earlier_gmv * 1.2:
            insights.append("近 3 日 GMV 均值较前期增长超过 20%，销售势头良好。")
    while len(insights) < 3:
        insights.append("建议结合品类、渠道、退货率三维交叉分析，识别增长机会和风险点。")

    # Risks
    risks = []
    if return_rate >= 15:
        risks.append({
            "level": "high",
            "title": "退货率偏高",
            "detail": f"当前退货率 {return_rate}%，可能影响利润和评分。",
            "action": "核查主要退货原因，优化商品描述、尺码指南或质检流程。",
        })
    if category_contribution and category_contribution[0]["share"] >= 60:
        risks.append({
            "level": "medium",
            "title": "品类集中度过高",
            "detail": f"「{category_contribution[0]['name']}」占比 {category_contribution[0]['share']}%，依赖单一品类风险高。",
            "action": "评估品类多元化策略，降低单一品类波动对整体 GMV 的影响。",
        })
    if channel_contribution and channel_contribution[0]["share"] >= 60:
        risks.append({
            "level": "medium",
            "title": "渠道集中度过高",
            "detail": f"「{channel_contribution[0]['name']}」占比 {channel_contribution[0]['share']}%，渠道风险集中。",
            "action": "拓展多渠道布局，降低对单一平台的依赖。",
        })
    if not risks:
        risks.append({
            "level": "low",
            "title": "数据质量检查",
            "detail": "建议确认金额、日期、品类字段准确无误，避免分析偏差。",
            "action": "检查异常订单（金额为负、日期缺失等）并在分析前清洗。",
        })

    assumptions = [
        f"金额字段：{amount_col or '未识别'}",
        f"日期字段：{date_col or '未识别'}",
        f"品类字段：{category_col or '未识别'}",
        f"渠道字段：{channel_col or '未识别'}",
        f"状态/退货字段：{status_col or '未识别'}",
    ]

    return {
        "domain": "ecommerce-orders",
        "title": title or "电商订单经营分析报告",
        "subtitle": requirement or "从订单明细自动生成的经营分析汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:5],
        "risks": risks[:8],
        "assumptions": assumptions,
        "gmv_trend": gmv_trend,
        "category_contribution": category_contribution,
        "channel_contribution": channel_contribution,
        "return_rate": return_rate,
        "returned_orders": returned_orders,
        "total_gmv": total_gmv,
        "avg_order_value": avg_order_value,
        "profile": profile,
    }


def build_finance_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    """Generate a management-ready finance/performance report."""
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "财务经营")

    columns = list(frame.columns)
    rows = len(frame)
    focus = requirement_focus(requirement)

    entity_col = find_col(
        columns,
        ["公司名称", "公司", "主体", "部门", "事业部", "项目", "门店", "区域", "供应商", "客户"],
    )
    period_col = find_col(columns, ["季度", "月份", "月度", "期间", "报告期", "年月", "日期", "时间"])
    revenue_col = find_metric_col(columns, ["营收", "营业收入", "收入", "销售额", "revenue"])
    profit_col = find_metric_col(
        columns,
        ["净利润", "利润总额", "营业利润", "利润", "profit"],
        exclude_tokens=["率", "margin"],
    )
    gross_margin_col = find_col(columns, ["毛利率", "净利率", "利润率", "gross margin", "margin"])
    rd_col = find_col(columns, ["研发投入", "研发费用", "研发", "r&d"])
    debt_col = find_col(columns, ["资产负债率", "负债率", "debt ratio", "debt"])
    risk_col = find_col(columns, ["风险等级", "风险", "risk"])
    budget_col = find_metric_col(columns, ["预算", "预算金额", "budget"])
    actual_col = find_metric_col(columns, ["实际", "实际金额", "actual"])
    variance_col = find_metric_col(columns, ["差异", "偏差", "variance"])
    status_col = find_col(columns, ["状态", "审批状态", "付款状态", "status"])
    category_col = find_col(columns, ["科目", "费用类型", "项目", "部门", "业务线", "公司名称", "公司"])

    working = frame.copy()
    working["_entity"] = (
        working[entity_col].fillna("未识别主体").astype(str).str.strip() if entity_col else "整体"
    )
    working["_period"] = (
        working[period_col].fillna("未识别期间").astype(str).str.strip() if period_col else "整体"
    )
    working["_revenue"] = numeric_series(working, revenue_col)
    working["_profit"] = numeric_series(working, profit_col)
    working["_gross_margin_pct"] = ratio_percent_series(working, gross_margin_col)
    working["_rd"] = numeric_series(working, rd_col)
    working["_debt_pct"] = ratio_percent_series(working, debt_col)
    working["_budget"] = numeric_series(working, budget_col)
    working["_actual"] = numeric_series(working, actual_col)
    working["_variance"] = numeric_series(working, variance_col)
    if variance_col is None and budget_col and actual_col:
        working["_variance"] = working["_actual"] - working["_budget"]
    working["_risk_level"] = working[risk_col].map(risk_text_level) if risk_col else ""

    primary_amount_col = "_revenue"
    primary_amount_label = "营收"
    if working["_revenue"].dropna().empty:
        if not working["_actual"].dropna().empty:
            primary_amount_col = "_actual"
            primary_amount_label = "实际金额"
        elif not working["_profit"].dropna().empty:
            primary_amount_col = "_profit"
            primary_amount_label = "利润"
        else:
            primary_amount_col = ""

    periods = sorted(
        [p for p in working["_period"].dropna().astype(str).unique().tolist() if p and p != "nan"],
        key=period_sort_key,
    )
    period_trend: list[dict[str, Any]] = []
    if period_col and periods:
        for period in periods:
            group = working[working["_period"].astype(str) == period]
            item = {
                "period": period,
                "records": int(len(group)),
                "revenue": round(float(group["_revenue"].sum(skipna=True)), 2)
                if group["_revenue"].notna().any()
                else None,
                "profit": round(float(group["_profit"].sum(skipna=True)), 2)
                if group["_profit"].notna().any()
                else None,
                "gross_margin": round(float(group["_gross_margin_pct"].mean(skipna=True)), 1)
                if group["_gross_margin_pct"].notna().any()
                else None,
                "rd": round(float(group["_rd"].sum(skipna=True)), 2)
                if group["_rd"].notna().any()
                else None,
                "debt": round(float(group["_debt_pct"].mean(skipna=True)), 1)
                if group["_debt_pct"].notna().any()
                else None,
                "high_risk": int((group["_risk_level"] == "high").sum()),
                "losses": int((group["_profit"] < 0).sum()) if group["_profit"].notna().any() else 0,
            }
            period_trend.append(item)

    latest = period_trend[-1] if period_trend else {}
    previous = period_trend[-2] if len(period_trend) >= 2 else {}
    revenue_growth = safe_rate(latest.get("revenue"), previous.get("revenue")) if latest else None
    profit_growth = safe_rate(latest.get("profit"), previous.get("profit")) if latest else None

    total_revenue = float(working["_revenue"].sum(skipna=True)) if working["_revenue"].notna().any() else None
    total_profit = float(working["_profit"].sum(skipna=True)) if working["_profit"].notna().any() else None
    total_actual = float(working["_actual"].sum(skipna=True)) if working["_actual"].notna().any() else None
    total_budget = float(working["_budget"].sum(skipna=True)) if working["_budget"].notna().any() else None
    total_variance = (
        float(working["_variance"].sum(skipna=True)) if working["_variance"].notna().any() else None
    )
    entities = int(working["_entity"].nunique(dropna=True))
    high_risk_count = int((working["_risk_level"] == "high").sum())
    medium_risk_count = int((working["_risk_level"] == "medium").sum())
    loss_count = int((working["_profit"] < 0).sum()) if working["_profit"].notna().any() else 0
    high_debt_count = int((working["_debt_pct"] >= 70).sum()) if working["_debt_pct"].notna().any() else 0

    kpis = [
        make_kpi("记录数", compact_number(rows), f"{entities} 个主体，{len(periods) or 1} 个期间", "blue"),
    ]
    if total_revenue is not None:
        kpis.append(
            make_kpi(
                "累计营收",
                compact_number(total_revenue),
                f"最近一期 {compact_number(latest.get('revenue')) if latest else '-'}，环比 {format_rate(revenue_growth)}",
                "green",
            )
        )
    if total_profit is not None:
        margin = pct(total_profit, total_revenue) if total_revenue else 0
        kpis.append(
            make_kpi(
                "累计净利润",
                compact_number(total_profit),
                f"整体净利率 {margin}%；亏损记录 {loss_count} 条",
                "orange" if total_profit >= 0 else "red",
            )
        )
    if total_budget is not None or total_variance is not None:
        variance_rate = pct(total_variance or 0, total_budget or 0) if total_budget else 0
        kpis.append(
            make_kpi(
                "预算差异",
                compact_number(total_variance),
                f"预算 {compact_number(total_budget)}，实际 {compact_number(total_actual)}，差异率 {variance_rate}%",
                "red" if abs(variance_rate) >= 10 else "cyan",
            )
        )
    if working["_debt_pct"].notna().any() or risk_col:
        kpis.append(
            make_kpi(
                "风险暴露",
                f"{high_risk_count}高/{medium_risk_count}中",
                f"资产负债率>=70%：{high_debt_count} 条",
                "red" if high_risk_count or high_debt_count else "cyan",
            )
        )
    while len(kpis) < 5:
        if working["_gross_margin_pct"].notna().any():
            kpis.append(
                make_kpi(
                    "平均毛利率",
                    f"{working['_gross_margin_pct'].mean(skipna=True):.1f}%",
                    "按已识别毛利率字段计算",
                    "cyan",
                )
            )
        elif working["_rd"].notna().any() and total_revenue:
            rd_total = float(working["_rd"].sum(skipna=True))
            kpis.append(
                make_kpi("研发投入率", f"{pct(rd_total, total_revenue)}%", f"研发投入 {compact_number(rd_total)}", "cyan")
            )
        else:
            kpis.append(make_kpi("分析焦点", " / ".join(focus[:2]), requirement or "管理层汇报", "cyan"))
        if len(kpis) >= 5:
            break

    entity_performance: list[dict[str, Any]] = []
    if entity_col:
        for entity, group in working.groupby("_entity", dropna=False):
            revenue = float(group["_revenue"].sum(skipna=True)) if group["_revenue"].notna().any() else None
            profit = float(group["_profit"].sum(skipna=True)) if group["_profit"].notna().any() else None
            item = {
                "name": str(entity) or "未识别主体",
                "records": int(len(group)),
                "revenue": round(revenue, 2) if revenue is not None else None,
                "profit": round(profit, 2) if profit is not None else None,
                "profit_margin": pct(profit or 0, revenue or 0) if revenue else None,
                "gross_margin": round(float(group["_gross_margin_pct"].mean(skipna=True)), 1)
                if group["_gross_margin_pct"].notna().any()
                else None,
                "rd": round(float(group["_rd"].sum(skipna=True)), 2) if group["_rd"].notna().any() else None,
                "debt": round(float(group["_debt_pct"].mean(skipna=True)), 1)
                if group["_debt_pct"].notna().any()
                else None,
                "max_debt": round(float(group["_debt_pct"].max(skipna=True)), 1)
                if group["_debt_pct"].notna().any()
                else None,
                "losses": int((group["_profit"] < 0).sum()) if group["_profit"].notna().any() else 0,
                "high_risk": int((group["_risk_level"] == "high").sum()),
                "medium_risk": int((group["_risk_level"] == "medium").sum()),
            }
            entity_performance.append(item)
        entity_performance.sort(
            key=lambda item: (
                item.get("high_risk", 0),
                item.get("losses", 0),
                item.get("max_debt") or 0,
                abs(item.get("profit") or 0),
            ),
            reverse=True,
        )

    mix_analysis: list[dict[str, Any]] = []
    if category_col and category_col in frame and primary_amount_col:
        grouped = working.groupby(working[category_col].fillna("未分类"))[primary_amount_col].agg(["sum", "count"])
        grouped = grouped.sort_values("sum", ascending=False)
        total_amount = float(working[primary_amount_col].sum(skipna=True)) or 0
        for name, row in grouped.head(8).iterrows():
            mix_analysis.append(
                {
                    "name": str(name),
                    "amount": round(float(row["sum"]), 2),
                    "share": pct(float(row["sum"]), total_amount),
                    "records": int(row["count"]),
                    "metric": primary_amount_label,
                }
            )

    exception_items: list[dict[str, Any]] = []
    for _, row in working.iterrows():
        reasons = []
        debt = row.get("_debt_pct")
        profit = row.get("_profit")
        risk_level = row.get("_risk_level")
        if risk_level == "high":
            reasons.append("高风险")
        elif risk_level == "medium":
            reasons.append("中风险")
        if pd.notna(debt) and debt >= 70:
            reasons.append(f"高负债 {debt:.1f}%")
        if pd.notna(profit) and profit < 0:
            reasons.append(f"亏损 {compact_number(profit)}")
        if not reasons:
            continue
        exception_items.append(
            {
                "entity": str(row.get("_entity", "")),
                "period": str(row.get("_period", "")),
                "reason": "、".join(reasons),
                "revenue": round(float(row["_revenue"]), 2) if pd.notna(row.get("_revenue")) else None,
                "profit": round(float(row["_profit"]), 2) if pd.notna(row.get("_profit")) else None,
                "debt": round(float(row["_debt_pct"]), 1) if pd.notna(row.get("_debt_pct")) else None,
            }
        )
    exception_items = exception_items[:12]

    insights: list[str] = []
    if revenue_growth is not None:
        latest_label = latest.get("period", "最近一期")
        direction = "增长" if revenue_growth >= 0 else "下滑"
        insights.append(
            f"{latest_label}营收较上一期{direction} {abs(revenue_growth):.1f}%，"
            f"最近一期营收 {compact_number(latest.get('revenue'))}。"
        )
    if profit_growth is not None:
        latest_label = latest.get("period", "最近一期")
        direction = "改善" if profit_growth >= 0 else "承压"
        insights.append(
            f"{latest_label}净利润环比{direction} {format_rate(profit_growth)}，"
            f"最近一期净利润 {compact_number(latest.get('profit'))}。"
        )
    if total_revenue is not None and total_profit is not None:
        insights.append(
            f"累计净利率 {pct(total_profit, total_revenue)}%，需要同时关注规模增长和盈利质量。"
        )
    if high_risk_count or medium_risk_count or high_debt_count or loss_count:
        insights.append(
            f"风险侧共识别 {high_risk_count} 条高风险、{medium_risk_count} 条中风险，"
            f"{high_debt_count} 条高负债、{loss_count} 条亏损记录，需进入管理层风险台账。"
        )
    if entity_performance:
        top_revenue = max(entity_performance, key=lambda item: item.get("revenue") or -float("inf"))
        insights.append(
            f"「{top_revenue['name']}」贡献最高{primary_amount_label} {compact_number(top_revenue.get('revenue') or top_revenue.get('profit'))}，"
            "建议拆分看增长质量和风险暴露。"
        )
        riskiest = entity_performance[0]
        if riskiest["high_risk"] or riskiest["losses"] or (riskiest.get("max_debt") or 0) >= 70:
            insights.append(
                f"「{riskiest['name']}」风险最突出：高风险 {riskiest['high_risk']} 条、"
                f"亏损 {riskiest['losses']} 期、最高负债率 {riskiest.get('max_debt') or '-'}%。"
            )
    if working["_rd"].notna().any() and total_revenue:
        rd_total = float(working["_rd"].sum(skipna=True))
        insights.append(f"研发投入率 {pct(rd_total, total_revenue)}%，可作为增长质量和未来投入强度的观察指标。")
    while len(insights) < 4:
        insights.append("当前报告已按财务经营口径完成趋势、结构、风险和行动建议汇总。")

    risks: list[dict[str, str]] = []
    if high_risk_count:
        risks.append(
            {
                "level": "high",
                "title": "高风险记录需要进入管理层台账",
                "detail": f"风险字段中识别到 {high_risk_count} 条高风险记录。",
                "action": "逐条确认责任主体、形成原因、预计改善时间，并在下次经营会上复盘。",
            }
        )
    if high_debt_count:
        risks.append(
            {
                "level": "high",
                "title": "资产负债率偏高",
                "detail": f"{high_debt_count} 条记录资产负债率达到或超过 70%。",
                "action": "对高负债主体做现金流、融资成本和偿债计划复核，必要时限制新增投入。",
            }
        )
    if loss_count:
        risks.append(
            {
                "level": "medium" if loss_count < max(3, rows * 0.2) else "high",
                "title": "亏损记录影响盈利质量",
                "detail": f"净利润为负的记录共 {loss_count} 条。",
                "action": "拆解亏损主体的收入、成本、费用和一次性因素，明确止损或转型动作。",
            }
        )
    if revenue_growth is not None and revenue_growth <= -10:
        risks.append(
            {
                "level": "medium",
                "title": "最近一期营收下滑",
                "detail": f"最近一期营收环比 {format_rate(revenue_growth)}。",
                "action": "排查客户、产品、渠道或确认周期变化，区分一次性波动与趋势性下行。",
            }
        )
    if total_variance is not None and total_budget:
        variance_rate = pct(total_variance, total_budget)
        if abs(variance_rate) >= 10:
            risks.append(
                {
                    "level": "medium",
                    "title": "预算执行偏差较大",
                    "detail": f"预算差异率 {variance_rate}%，差异金额 {compact_number(total_variance)}。",
                    "action": "按部门/科目拆解差异，确认是否需要预算调整、费用冻结或补充审批。",
                }
            )
    if not risks:
        risks.append(
            {
                "level": "low",
                "title": "未发现明显财务红灯",
                "detail": "按已识别字段看，高风险、亏损和高负债暴露有限。",
                "action": "继续补充预算、现金流、同比口径，提升下一版经营复盘深度。",
            }
        )

    assumptions = [
        f"分析焦点：{'、'.join(focus)}",
        f"主体字段：{entity_col or '未识别'}",
        f"期间字段：{period_col or '未识别'}",
        f"营收字段：{revenue_col or '未识别'}",
        f"利润字段：{profit_col or '未识别'}",
        f"毛利/利润率字段：{gross_margin_col or '未识别'}",
        f"负债率字段：{debt_col or '未识别'}",
        f"风险字段：{risk_col or '未识别'}",
    ]
    if status_col:
        assumptions.append(f"状态字段：{status_col}")

    return {
        "domain": "finance-expense",
        "title": title or "财务经营绩效分析报告",
        "subtitle": requirement or "从财务/经营明细自动生成的管理层汇报材料",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "focus": focus,
        "kpis": kpis[:5],
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": assumptions,
        "period_trend": period_trend[-12:],
        "entity_performance": entity_performance[:12],
        "mix_analysis": mix_analysis,
        "exception_items": exception_items,
        "profile": profile,
    }


def build_crm_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "CRM商机")

    columns = list(frame.columns)
    rows = len(frame)
    account_col = find_col(columns, ["客户", "客户名称", "公司", "account", "客户公司"])
    opp_col = find_col(columns, ["商机", "商机名称", "线索", "机会", "opportunity", "项目名称"])
    stage_col = find_col(columns, ["阶段", "商机阶段", "状态", "stage", "status"])
    owner_col = find_col(columns, ["销售", "负责人", "客户经理", "owner", "销售负责人"])
    amount_col = find_metric_col(columns, ["预计金额", "商机金额", "合同金额", "ARR", "MRR", "金额", "预算"])
    source_col = find_col(columns, ["来源", "线索来源", "渠道", "source", "channel"])
    next_col = find_col(columns, ["下次跟进", "下次联系", "跟进时间", "预计成交", "预计签约", "close date"])
    created_col = find_col(columns, ["创建时间", "创建日期", "录入时间", "日期"])

    working = frame.copy()
    working["_stage"] = text_series(working, stage_col, "未识别阶段")
    working["_owner"] = text_series(working, owner_col, "未识别负责人")
    working["_amount"] = numeric_series(working, amount_col)
    stage_norm = working["_stage"].map(normalized_text)
    won_mask = stage_norm.str.contains("赢单|已赢|成交|签约|won|closedwon", regex=True)
    lost_mask = stage_norm.str.contains("输单|丢单|失败|lost|closedlost", regex=True)
    open_mask = ~(won_mask | lost_mask)
    next_dates = parse_datetime_series(working, next_col)
    today = pd.Timestamp.now().normalize()
    stale_mask = open_mask & (next_dates.notna()) & (next_dates < today)
    no_next_mask = open_mask & (next_dates.isna())

    pipeline_amount = float(working.loc[open_mask, "_amount"].sum(skipna=True)) if amount_col else 0.0
    won_amount = float(working.loc[won_mask, "_amount"].sum(skipna=True)) if amount_col else 0.0
    kpis = [
        make_kpi("商机数", compact_number(rows), f"{working['_owner'].nunique()} 位负责人", "blue"),
        make_kpi("Pipeline 金额", compact_number(pipeline_amount), f"开放商机 {int(open_mask.sum())} 条", "green"),
        make_kpi("赢单率", f"{pct(int(won_mask.sum()), rows)}%", f"赢单 {int(won_mask.sum())} 条，输单 {int(lost_mask.sum())} 条", "orange"),
        make_kpi("过期跟进", compact_number(int(stale_mask.sum())), f"未设置下次跟进 {int(no_next_mask.sum())} 条", "red" if stale_mask.any() else "cyan"),
        make_kpi("已赢金额", compact_number(won_amount), "按已识别赢单阶段统计", "cyan"),
    ]

    stage_rows = value_counts_rows(working["_stage"], rows)
    owner_rows = []
    for owner, group in working.groupby("_owner"):
        amount = float(group["_amount"].sum(skipna=True)) if amount_col else 0.0
        owner_rows.append(
            {
                "name": str(owner),
                "value": round(amount if amount_col else len(group), 2),
                "share": pct(len(group), rows),
                "detail": f"{len(group)} 条商机，赢单 {int(won_mask.loc[group.index].sum())} 条",
            }
        )
    owner_rows.sort(key=lambda item: item["value"], reverse=True)

    source_rows = amount_mix_rows(working, source_col, amount_col)
    trend_rows = time_trend_rows(working, created_col or next_col, amount_col)

    exception_rows = []
    for idx, row in working[stale_mask | no_next_mask].head(12).iterrows():
        reason = "跟进已过期" if stale_mask.loc[idx] else "未设置下次跟进"
        exception_rows.append(
            {
                "customer": str(row.get(account_col, ""))[:60] if account_col else "",
                "opportunity": str(row.get(opp_col, ""))[:80] if opp_col else f"第 {idx + 1} 行",
                "owner": row.get("_owner", ""),
                "stage": row.get("_stage", ""),
                "amount": compact_number(row.get("_amount")),
                "reason": reason,
            }
        )

    insights = []
    if stage_rows:
        insights.append(f"当前商机最多停留在「{stage_rows[0]['name']}」阶段，占比 {stage_rows[0]['share']}%。")
    if pipeline_amount:
        insights.append(f"开放 Pipeline 金额 {compact_number(pipeline_amount)}，需要优先推进高金额且临近成交的商机。")
    if stale_mask.any() or no_next_mask.any():
        insights.append(f"{int(stale_mask.sum())} 条开放商机跟进已过期，{int(no_next_mask.sum())} 条缺少下一步动作。")
    if source_rows:
        insights.append(f"「{source_rows[0]['name']}」贡献最高商机金额 {compact_number(source_rows[0]['value'])}。")
    while len(insights) < 4:
        insights.append("CRM 报告已按漏斗、负责人、来源和跟进风险形成管理层复盘视图。")

    risks = []
    if stale_mask.any():
        risks.append({"level": "high", "title": "商机跟进过期", "detail": f"{int(stale_mask.sum())} 条开放商机下次跟进日期已过。", "action": "要求负责人当天更新下一步动作、预计成交时间和阻塞原因。"})
    if no_next_mask.any():
        risks.append({"level": "medium", "title": "缺少下一步动作", "detail": f"{int(no_next_mask.sum())} 条开放商机没有下次跟进日期。", "action": "建立 CRM 数据卫生规则，未设置下一步的商机不得进入预测。"})
    if stage_rows and stage_rows[0]["share"] >= 55:
        risks.append({"level": "medium", "title": "阶段集中度偏高", "detail": f"「{stage_rows[0]['name']}」阶段占比 {stage_rows[0]['share']}%。", "action": "复核该阶段的进入/退出标准，识别漏斗堵点。"})
    if not risks:
        risks.append({"level": "low", "title": "Pipeline 基本可控", "detail": "未识别明显跟进过期或阶段集中红灯。", "action": "继续补齐赢率、销售周期和预测分类口径。"})

    return {
        "domain": "crm-pipeline",
        "title": title or "CRM 商机管道分析报告",
        "subtitle": requirement or "从 CRM 导出表自动生成的销售管理汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": [
            f"客户字段：{account_col or '未识别'}",
            f"阶段字段：{stage_col or '未识别'}",
            f"金额字段：{amount_col or '未识别'}",
            f"负责人字段：{owner_col or '未识别'}",
            f"下次跟进字段：{next_col or '未识别'}",
        ],
        "analysis_sections": [
            bars_section("销售漏斗阶段分布", stage_rows),
            bars_section("负责人 Pipeline 排行", owner_rows[:8]),
            bars_section("线索来源贡献", source_rows),
            bars_section("创建/跟进趋势", trend_rows),
            table_section(
                "跟进风险明细",
                [
                    {"key": "customer", "label": "客户"},
                    {"key": "opportunity", "label": "商机"},
                    {"key": "owner", "label": "负责人"},
                    {"key": "stage", "label": "阶段"},
                    {"key": "amount", "label": "金额"},
                    {"key": "reason", "label": "原因"},
                ],
                exception_rows,
            ),
        ],
        "profile": profile,
    }


def build_inventory_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "库存采购")

    columns = list(frame.columns)
    item_col = find_col(columns, ["物料", "SKU", "商品编码", "商品", "物料编码", "item"])
    inventory_col = find_metric_col(columns, ["库存", "可用库存", "现存量", "库存数量", "available stock"])
    outbound_col = find_metric_col(columns, ["出库", "销量", "消耗", "日均销量", "月销量", "需求量"])
    warehouse_col = find_col(columns, ["仓库", "库位", "门店", "warehouse"])
    supplier_col = find_col(columns, ["供应商", "vendor", "supplier"])
    value_col = find_metric_col(columns, ["库存金额", "金额", "成本", "采购金额", "value"])
    date_col = find_col(columns, ["日期", "入库时间", "出库时间", "更新时间"])

    working = frame.copy()
    working["_item"] = text_series(working, item_col, "未识别物料")
    working["_stock"] = numeric_series(working, inventory_col)
    working["_outbound"] = numeric_series(working, outbound_col)
    working["_value"] = numeric_series(working, value_col)
    stock = working["_stock"]
    median_stock = float(stock.dropna().median()) if stock.notna().any() else 0.0
    stockout_mask = stock.fillna(0) <= 0
    overstock_threshold = max(median_stock * 2.5, stock.dropna().quantile(0.85) if stock.notna().any() else 0)
    overstock_mask = stock > overstock_threshold
    slow_mask = overstock_mask
    if working["_outbound"].notna().any():
        slow_mask = overstock_mask & (working["_outbound"].fillna(0) <= max(1, working["_outbound"].median() * 0.3))

    inventory_value = float(working["_value"].sum(skipna=True)) if value_col else 0.0
    kpis = [
        make_kpi("SKU/物料数", compact_number(working["_item"].nunique()), f"记录 {len(frame)} 条", "blue"),
        make_kpi("库存总量", compact_number(stock.sum(skipna=True)), f"库存金额 {compact_number(inventory_value)}", "green"),
        make_kpi("缺货风险", compact_number(int(stockout_mask.sum())), "库存小于等于 0", "red" if stockout_mask.any() else "cyan"),
        make_kpi("高库存风险", compact_number(int(overstock_mask.sum())), f"阈值约 {compact_number(overstock_threshold)}", "orange"),
        make_kpi("疑似呆滞", compact_number(int(slow_mask.sum())), "高库存且消耗偏低", "red" if slow_mask.any() else "cyan"),
    ]

    warehouse_rows = amount_mix_rows(working, warehouse_col, value_col or inventory_col)
    supplier_rows = amount_mix_rows(working, supplier_col, value_col or inventory_col)
    trend_rows = time_trend_rows(working, date_col, value_col or inventory_col)
    exception_rows = []
    focus = working[stockout_mask | slow_mask].copy()
    if not focus.empty:
        focus["_risk_sort"] = focus["_stock"].fillna(0)
        for _, row in focus.sort_values("_risk_sort", ascending=False).head(12).iterrows():
            reason = "缺货" if row.get("_stock", 0) <= 0 else "高库存/疑似呆滞"
            exception_rows.append(
                {
                    "item": row.get("_item", ""),
                    "warehouse": str(row.get(warehouse_col, ""))[:60] if warehouse_col else "",
                    "supplier": str(row.get(supplier_col, ""))[:60] if supplier_col else "",
                    "stock": compact_number(row.get("_stock")),
                    "value": compact_number(row.get("_value")),
                    "reason": reason,
                }
            )

    insights = []
    if warehouse_rows:
        insights.append(f"库存价值最高集中在「{warehouse_rows[0]['name']}」，占比 {warehouse_rows[0]['share']}%。")
    if supplier_rows:
        insights.append(f"供应商「{supplier_rows[0]['name']}」关联库存/采购金额最高，占比 {supplier_rows[0]['share']}%。")
    if stockout_mask.any():
        insights.append(f"识别到 {int(stockout_mask.sum())} 条缺货或负库存记录，需要优先补货或校正库存。")
    if slow_mask.any():
        insights.append(f"识别到 {int(slow_mask.sum())} 条高库存且消耗偏低记录，存在资金占用风险。")
    while len(insights) < 4:
        insights.append("库存报告已按库存规模、仓库/供应商集中度、缺货和呆滞风险形成复盘视图。")

    risks = []
    if stockout_mask.any():
        risks.append({"level": "high", "title": "缺货或负库存", "detail": f"{int(stockout_mask.sum())} 条记录库存小于等于 0。", "action": "核对系统库存和实际库存，对核心 SKU 立即补货或调整安全库存。"})
    if slow_mask.any():
        risks.append({"level": "medium", "title": "库存资金占用", "detail": f"{int(slow_mask.sum())} 条记录疑似高库存低消耗。", "action": "制定清库存、调拨、促销或采购暂停计划。"})
    if supplier_rows and supplier_rows[0]["share"] >= 60:
        risks.append({"level": "medium", "title": "供应商集中度过高", "detail": f"「{supplier_rows[0]['name']}」占比 {supplier_rows[0]['share']}%。", "action": "评估替代供应商和交付风险，避免单点供应中断。"})
    if not risks:
        risks.append({"level": "low", "title": "库存风险可控", "detail": "未识别明显缺货、呆滞或供应商集中红灯。", "action": "继续补充周转天数和安全库存口径。"})

    return {
        "domain": "erp-inventory",
        "title": title or "库存与采购风险分析报告",
        "subtitle": requirement or "从 ERP/库存导出表自动生成的运营汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": [
            f"物料字段：{item_col or '未识别'}",
            f"库存字段：{inventory_col or '未识别'}",
            f"消耗/销量字段：{outbound_col or '未识别'}",
            f"仓库字段：{warehouse_col or '未识别'}",
            f"供应商字段：{supplier_col or '未识别'}",
        ],
        "analysis_sections": [
            bars_section("仓库库存/金额贡献", warehouse_rows),
            bars_section("供应商集中度", supplier_rows),
            bars_section("库存变化趋势", trend_rows),
            table_section(
                "缺货与呆滞风险明细",
                [
                    {"key": "item", "label": "物料/SKU"},
                    {"key": "warehouse", "label": "仓库"},
                    {"key": "supplier", "label": "供应商"},
                    {"key": "stock", "label": "库存"},
                    {"key": "value", "label": "金额"},
                    {"key": "reason", "label": "风险"},
                ],
                exception_rows,
            ),
        ],
        "profile": profile,
    }


def build_support_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "客服工单")

    columns = list(frame.columns)
    status_col = find_col(columns, ["状态", "解决状态", "工单状态", "status"])
    owner_col = find_col(columns, ["客服", "处理人", "负责人", "坐席", "owner"])
    category_col = find_col(columns, ["问题类型", "问题分类", "分类", "产品", "模块"])
    channel_col = find_col(columns, ["渠道", "来源", "平台", "入口"])
    created_col = find_col(columns, ["创建时间", "提交时间", "日期"])
    response_col = find_metric_col(columns, ["响应时间", "首次响应", "响应时长"])
    handle_col = find_metric_col(columns, ["处理时长", "解决时长", "耗时", "工时"])
    rating_col = find_metric_col(columns, ["满意度", "评分", "评价", "星级"])
    sla_col = find_col(columns, ["SLA", "是否超时", "超时", "逾期"])

    working = frame.copy()
    working["_status"] = text_series(working, status_col, "未识别状态")
    working["_owner"] = text_series(working, owner_col, "未识别坐席")
    working["_category"] = text_series(working, category_col, "未分类问题")
    working["_response"] = numeric_series(working, response_col)
    working["_handle"] = numeric_series(working, handle_col)
    working["_rating"] = numeric_series(working, rating_col)
    status_norm = working["_status"].map(normalized_text)
    resolved_mask = status_norm.str.contains("已解决|已关闭|完成|resolved|closed|done", regex=True)
    unresolved_mask = ~resolved_mask
    if sla_col:
        sla_norm = text_series(working, sla_col, "").map(normalized_text)
        breach_mask = sla_norm.str.contains("超时|逾期|违约|breach|fail|yes|是", regex=True)
    else:
        breach_mask = working["_handle"] > max(24, working["_handle"].median() * 2 if working["_handle"].notna().any() else 24)
    low_rating_mask = working["_rating"].notna() & (working["_rating"] <= 3)

    kpis = [
        make_kpi("工单量", compact_number(len(frame)), f"{working['_owner'].nunique()} 位处理人", "blue"),
        make_kpi("解决率", f"{pct(int(resolved_mask.sum()), len(frame))}%", f"未解决 {int(unresolved_mask.sum())} 条", "green"),
        make_kpi("平均处理时长", compact_number(working["_handle"].mean(skipna=True)), "按已识别处理时长字段", "orange"),
        make_kpi("SLA/超时", compact_number(int(breach_mask.sum())), "超时或疑似超时记录", "red" if breach_mask.any() else "cyan"),
        make_kpi("低满意度", compact_number(int(low_rating_mask.sum())), "评分<=3", "red" if low_rating_mask.any() else "cyan"),
    ]

    category_rows = value_counts_rows(working["_category"], len(frame))
    channel_rows = amount_mix_rows(working, channel_col, None)
    trend_rows = time_trend_rows(working, created_col)
    owner_rows = []
    for owner, group in working.groupby("_owner"):
        owner_rows.append(
            {
                "name": str(owner),
                "value": int(len(group)),
                "share": pct(len(group), len(frame)),
                "detail": f"未解决 {int(unresolved_mask.loc[group.index].sum())}，超时 {int(breach_mask.loc[group.index].sum())}",
            }
        )
    owner_rows.sort(key=lambda item: item["value"], reverse=True)

    exception_rows = []
    for idx, row in working[unresolved_mask | breach_mask | low_rating_mask].head(12).iterrows():
        reasons = []
        if unresolved_mask.loc[idx]:
            reasons.append("未解决")
        if breach_mask.loc[idx]:
            reasons.append("SLA/超时")
        if low_rating_mask.loc[idx]:
            reasons.append("低满意度")
        exception_rows.append(
            {
                "category": row.get("_category", ""),
                "owner": row.get("_owner", ""),
                "status": row.get("_status", ""),
                "handle": compact_number(row.get("_handle")),
                "rating": compact_number(row.get("_rating")),
                "reason": "、".join(reasons),
            }
        )

    insights = []
    if category_rows:
        insights.append(f"问题最集中在「{category_rows[0]['name']}」，占全部工单 {category_rows[0]['share']}%。")
    if owner_rows:
        insights.append(f"坐席/处理人「{owner_rows[0]['name']}」负载最高，处理 {owner_rows[0]['value']} 条。")
    if breach_mask.any():
        insights.append(f"识别到 {int(breach_mask.sum())} 条 SLA/超时风险，需要优先复盘响应和解决链路。")
    if low_rating_mask.any():
        insights.append(f"低满意度记录 {int(low_rating_mask.sum())} 条，建议结合问题类型定位体验短板。")
    while len(insights) < 4:
        insights.append("客服工单报告已按问题类型、处理人负载、SLA 和满意度形成服务复盘视图。")

    risks = []
    if breach_mask.any():
        risks.append({"level": "high", "title": "SLA/超时风险", "detail": f"{int(breach_mask.sum())} 条工单超时或疑似超时。", "action": "优先处理未解决超时工单，复盘高频类型的知识库和升级路径。"})
    if low_rating_mask.any():
        risks.append({"level": "medium", "title": "低满意度集中", "detail": f"{int(low_rating_mask.sum())} 条评分较低。", "action": "抽样回访低评分用户，定位产品、服务或物流根因。"})
    if owner_rows and owner_rows[0]["share"] >= 45:
        risks.append({"level": "medium", "title": "坐席负载集中", "detail": f"「{owner_rows[0]['name']}」承接 {owner_rows[0]['share']}% 工单。", "action": "评估排班和分单规则，避免响应瓶颈。"})
    if not risks:
        risks.append({"level": "low", "title": "服务风险可控", "detail": "未识别明显超时、低满意度或负载集中红灯。", "action": "继续补充首次响应、升级次数和问题根因标签。"})

    return {
        "domain": "support-tickets",
        "title": title or "客服工单 SLA 分析报告",
        "subtitle": requirement or "从客服/工单系统导出表自动生成的服务管理汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": [
            f"状态字段：{status_col or '未识别'}",
            f"问题类型字段：{category_col or '未识别'}",
            f"处理人字段：{owner_col or '未识别'}",
            f"SLA字段：{sla_col or '未识别'}",
            f"满意度字段：{rating_col or '未识别'}",
        ],
        "analysis_sections": [
            bars_section("问题类型分布", category_rows),
            bars_section("处理人负载", owner_rows[:8]),
            bars_section("渠道来源", channel_rows),
            bars_section("工单趋势", trend_rows),
            table_section(
                "SLA 与满意度风险明细",
                [
                    {"key": "category", "label": "问题类型"},
                    {"key": "owner", "label": "处理人"},
                    {"key": "status", "label": "状态"},
                    {"key": "handle", "label": "处理时长"},
                    {"key": "rating", "label": "满意度"},
                    {"key": "reason", "label": "风险"},
                ],
                exception_rows,
            ),
        ],
        "profile": profile,
    }


def build_hr_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "HR")

    columns = list(frame.columns)
    employee_col = find_col(columns, ["员工", "姓名", "工号", "employee"])
    dept_col = find_col(columns, ["部门", "组织", "事业部", "团队"])
    role_col = find_col(columns, ["岗位", "职级", "角色", "职位"])
    date_col = find_col(columns, ["日期", "月份", "月度", "考勤月份"])
    score_col = find_metric_col(columns, ["绩效", "得分", "评分", "KPI", "产出"])
    hours_col = find_metric_col(columns, ["工时", "加班", "出勤时长", "工作时长"])
    status_col = find_col(columns, ["状态", "异常", "考勤状态", "审批"])

    working = frame.copy()
    working["_employee"] = text_series(working, employee_col, "未识别员工")
    working["_dept"] = text_series(working, dept_col, "未识别部门")
    working["_role"] = text_series(working, role_col, "未识别岗位")
    working["_score"] = numeric_series(working, score_col)
    working["_hours"] = numeric_series(working, hours_col)
    working["_status"] = text_series(working, status_col, "")
    status_norm = working["_status"].map(normalized_text)
    exception_mask = status_norm.str.contains("异常|迟到|早退|旷工|缺勤|未打卡|离职|低绩效|exception|absent", regex=True)
    low_score_mask = working["_score"].notna() & (working["_score"] < max(60, working["_score"].median() * 0.75 if working["_score"].notna().any() else 60))
    overtime_mask = working["_hours"].notna() & (working["_hours"] > max(10, working["_hours"].median() * 1.4 if working["_hours"].notna().any() else 10))

    kpis = [
        make_kpi("员工数", compact_number(working["_employee"].nunique()), f"{working['_dept'].nunique()} 个部门", "blue"),
        make_kpi("记录数", compact_number(len(frame)), f"{working['_role'].nunique()} 类岗位", "green"),
        make_kpi("平均绩效", compact_number(working["_score"].mean(skipna=True)), "按已识别绩效/得分字段", "orange"),
        make_kpi("考勤/状态异常", compact_number(int(exception_mask.sum())), "状态字段命中异常", "red" if exception_mask.any() else "cyan"),
        make_kpi("高工时记录", compact_number(int(overtime_mask.sum())), "疑似加班或负载偏高", "red" if overtime_mask.any() else "cyan"),
    ]

    dept_rows = []
    for dept, group in working.groupby("_dept"):
        score = group["_score"].mean(skipna=True)
        dept_rows.append(
            {
                "name": str(dept),
                "value": round(float(score), 1) if pd.notna(score) else int(len(group)),
                "share": pct(group["_employee"].nunique(), working["_employee"].nunique()),
                "detail": f"{group['_employee'].nunique()} 人，异常 {int(exception_mask.loc[group.index].sum())}",
            }
        )
    dept_rows.sort(key=lambda item: item["value"], reverse=True)
    role_rows = value_counts_rows(working["_role"], len(frame))
    trend_rows = time_trend_rows(working, date_col)
    exception_rows = []
    for idx, row in working[exception_mask | low_score_mask | overtime_mask].head(12).iterrows():
        reasons = []
        if exception_mask.loc[idx]:
            reasons.append("状态异常")
        if low_score_mask.loc[idx]:
            reasons.append("绩效偏低")
        if overtime_mask.loc[idx]:
            reasons.append("高工时")
        exception_rows.append(
            {
                "employee": row.get("_employee", ""),
                "dept": row.get("_dept", ""),
                "role": row.get("_role", ""),
                "score": compact_number(row.get("_score")),
                "hours": compact_number(row.get("_hours")),
                "reason": "、".join(reasons),
            }
        )

    insights = []
    if dept_rows:
        insights.append(f"部门「{dept_rows[0]['name']}」综合表现/记录值最高，涉及 {dept_rows[0]['detail']}。")
    if exception_mask.any():
        insights.append(f"识别到 {int(exception_mask.sum())} 条考勤或状态异常记录，需要部门负责人跟进。")
    if overtime_mask.any():
        insights.append(f"{int(overtime_mask.sum())} 条记录疑似高工时，可能存在排班或负载风险。")
    if low_score_mask.any():
        insights.append(f"{int(low_score_mask.sum())} 条记录绩效偏低，建议结合岗位和部门做辅导计划。")
    while len(insights) < 4:
        insights.append("HR 报告已按部门、岗位、绩效/考勤异常和负载风险形成管理视图。")

    risks = []
    if exception_mask.any():
        risks.append({"level": "medium", "title": "考勤/状态异常", "detail": f"{int(exception_mask.sum())} 条记录命中异常状态。", "action": "由部门负责人确认原因，区分系统漏打、真实缺勤和审批未闭环。"})
    if overtime_mask.any():
        risks.append({"level": "medium", "title": "高工时负载", "detail": f"{int(overtime_mask.sum())} 条记录工时偏高。", "action": "复核项目排期和人力配置，避免持续超负荷。"})
    if low_score_mask.any():
        risks.append({"level": "medium", "title": "绩效辅导对象", "detail": f"{int(low_score_mask.sum())} 条记录绩效偏低。", "action": "结合岗位要求制定辅导、调岗或目标重设计划。"})
    if not risks:
        risks.append({"level": "low", "title": "人员运营风险可控", "detail": "未识别明显考勤、绩效或工时红灯。", "action": "继续补充离职、入职、请假和组织层级字段。"})

    return {
        "domain": "hr-attendance",
        "title": title or "HR 人员运营分析报告",
        "subtitle": requirement or "从 HR/考勤绩效导出表自动生成的人效汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": [
            f"员工字段：{employee_col or '未识别'}",
            f"部门字段：{dept_col or '未识别'}",
            f"岗位字段：{role_col or '未识别'}",
            f"绩效字段：{score_col or '未识别'}",
            f"工时字段：{hours_col or '未识别'}",
        ],
        "analysis_sections": [
            bars_section("部门表现/覆盖", dept_rows),
            bars_section("岗位结构", role_rows),
            bars_section("记录趋势", trend_rows),
            table_section(
                "人员异常明细",
                [
                    {"key": "employee", "label": "员工"},
                    {"key": "dept", "label": "部门"},
                    {"key": "role", "label": "岗位"},
                    {"key": "score", "label": "绩效/得分"},
                    {"key": "hours", "label": "工时"},
                    {"key": "reason", "label": "风险"},
                ],
                exception_rows,
            ),
        ],
        "profile": profile,
    }


def build_feedback_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "反馈评论")

    columns = list(frame.columns)
    rating_col = find_metric_col(columns, ["评分", "星级", "满意度", "NPS", "rating"])
    text_col = find_col(columns, ["评论", "评价内容", "反馈", "建议", "备注", "review", "comment"])
    segment_col = find_col(columns, ["商品", "SKU", "门店", "部门", "城市", "人群", "渠道", "分类"])
    issue_col = find_col(columns, ["问题类型", "标签", "差评原因", "原因", "主题"])
    date_col = find_col(columns, ["评价时间", "提交时间", "创建时间", "日期"])

    working = frame.copy()
    working["_rating"] = numeric_series(working, rating_col)
    working["_segment"] = text_series(working, segment_col, "未识别分组")
    working["_issue"] = text_series(working, issue_col, "未分类主题")
    rating = working["_rating"]
    negative_mask = rating.notna() & (rating <= 3)
    high_mask = rating.notna() & (rating >= 4)

    keyword_bank = ["质量", "价格", "物流", "服务", "售后", "功能", "体验", "速度", "包装", "客服", "安装", "退款", "发货", "卡顿"]
    keyword_counts: Counter[str] = Counter()
    if text_col and text_col in working:
        for value in working[text_col].dropna().astype(str):
            for keyword in keyword_bank:
                if keyword in value:
                    keyword_counts[keyword] += 1

    avg_rating = float(rating.mean(skipna=True)) if rating.notna().any() else 0.0
    kpis = [
        make_kpi("反馈/评论数", compact_number(len(frame)), f"{working['_segment'].nunique()} 个分组", "blue"),
        make_kpi("平均评分", compact_number(avg_rating), f"高评分 {int(high_mask.sum())} 条", "green" if avg_rating >= 4 else "orange"),
        make_kpi("负面占比", f"{pct(int(negative_mask.sum()), len(frame))}%", f"评分<=3：{int(negative_mask.sum())} 条", "red" if negative_mask.any() else "cyan"),
        make_kpi("主题数", compact_number(working["_issue"].nunique()), "按问题/标签字段识别", "orange"),
        make_kpi("关键词命中", compact_number(sum(keyword_counts.values())), "从文本中提取常见主题", "cyan"),
    ]

    rating_rows = value_counts_rows(rating.dropna().astype(int) if rating.notna().any() else pd.Series(dtype=int), len(frame))
    segment_rows = []
    for segment, group in working.groupby("_segment"):
        avg = group["_rating"].mean(skipna=True)
        segment_rows.append(
            {
                "name": str(segment),
                "value": round(float(avg), 1) if pd.notna(avg) else int(len(group)),
                "share": pct(len(group), len(frame)),
                "detail": f"{len(group)} 条，负面 {int(negative_mask.loc[group.index].sum())}",
            }
        )
    segment_rows.sort(key=lambda item: item["share"], reverse=True)
    issue_rows = value_counts_rows(working["_issue"], len(frame))
    keyword_rows = [{"name": key, "value": count, "share": pct(count, len(frame)), "detail": "文本关键词"} for key, count in keyword_counts.most_common(10)]
    trend_rows = time_trend_rows(working, date_col)

    excerpt_rows = []
    if text_col and text_col in working:
        focus = working[negative_mask] if negative_mask.any() else working
        for _, row in focus.head(8).iterrows():
            excerpt_rows.append(
                {
                    "segment": row.get("_segment", ""),
                    "issue": row.get("_issue", ""),
                    "rating": compact_number(row.get("_rating")),
                    "text": str(row.get(text_col, ""))[:120],
                }
            )

    insights = []
    if rating.notna().any():
        insights.append(f"平均评分 {avg_rating:.1f}，负面反馈占比 {pct(int(negative_mask.sum()), len(frame))}%。")
    if issue_rows:
        insights.append(f"反馈主题最集中在「{issue_rows[0]['name']}」，占比 {issue_rows[0]['share']}%。")
    if segment_rows:
        insights.append(f"反馈最多来自「{segment_rows[0]['name']}」，占全部 {segment_rows[0]['share']}%。")
    if keyword_rows:
        insights.append(f"文本高频关键词为「{keyword_rows[0]['name']}」，命中 {keyword_rows[0]['value']} 次。")
    while len(insights) < 4:
        insights.append("反馈报告已按评分、主题、分组和代表性文本形成洞察视图。")

    risks = []
    if pct(int(negative_mask.sum()), len(frame)) >= 20:
        risks.append({"level": "high", "title": "负面反馈偏高", "detail": f"负面占比 {pct(int(negative_mask.sum()), len(frame))}%。", "action": "优先定位差评主题，形成产品、服务和售后整改清单。"})
    if issue_rows and issue_rows[0]["share"] >= 45:
        risks.append({"level": "medium", "title": "问题主题集中", "detail": f"「{issue_rows[0]['name']}」占比 {issue_rows[0]['share']}%。", "action": "将该主题拆解为根因，并指定负责人闭环。"})
    if not risks:
        risks.append({"level": "low", "title": "反馈风险可控", "detail": "未识别明显负面集中红灯。", "action": "继续补充更多文本、标签和人群分层以提升洞察深度。"})

    return {
        "domain": profile["inferred_domain"]["domain"],
        "title": title or "用户反馈与评论洞察报告",
        "subtitle": requirement or "从问卷/评论/反馈导出表自动生成的洞察汇报",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:6],
        "risks": risks[:8],
        "assumptions": [
            f"评分字段：{rating_col or '未识别'}",
            f"文本字段：{text_col or '未识别'}",
            f"分组字段：{segment_col or '未识别'}",
            f"主题字段：{issue_col or '未识别'}",
            f"时间字段：{date_col or '未识别'}",
        ],
        "analysis_sections": [
            bars_section("评分分布", rating_rows),
            bars_section("分组反馈表现", segment_rows[:8]),
            bars_section("问题主题排行", issue_rows),
            bars_section("文本关键词", keyword_rows),
            bars_section("反馈趋势", trend_rows),
            table_section(
                "代表性反馈摘录",
                [
                    {"key": "segment", "label": "分组"},
                    {"key": "issue", "label": "主题"},
                    {"key": "rating", "label": "评分"},
                    {"key": "text", "label": "摘录"},
                ],
                excerpt_rows,
            ),
        ],
        "profile": profile,
    }


def build_empty_report(
    profile: dict[str, Any], requirement: str, title: str | None, domain_label: str
) -> dict[str, Any]:
    """Generate a minimal report for empty DataFrames."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {
        "domain": profile.get("inferred_domain", {}).get("domain", "unknown"),
        "title": title or f"{domain_label}分析报告",
        "subtitle": "数据源为空或字段缺失，无法生成分析报告",
        "generated_at": now,
        "source": "",
        "kpis": [
            make_kpi("记录数", "0", "数据源无记录", "blue"),
            make_kpi("字段数", "0", "无法识别字段", "orange"),
            make_kpi("状态", "数据异常", "请检查数据源", "red"),
        ],
        "insights": [
            "数据源为空或字段缺失，无法进行业务分析",
            "请检查原始 Excel/CSV 文件是否包含有效数据",
            "确认文件格式正确（.xlsx, .xls, .csv）",
        ],
        "assumptions": ["输入数据为空或字段数为0"],
        "risks": [
            {
                "level": "high",
                "title": "数据源异常",
                "detail": "输入文件为空或无法读取有效数据，无法生成分析报告",
                "action": "请检查原始文件，确保包含有效数据后重新运行",
            }
        ],
    }


def build_generic_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    """Generate an exploratory but business-oriented report for any table."""
    if frame.empty or len(frame.columns) == 0:
        return build_empty_report(profile, requirement, title, "通用数据表")

    rows = len(frame)
    cols = len(frame.columns)
    domain = profile["inferred_domain"]["domain"]
    focus = requirement_focus(requirement)
    numeric_cols = [
        item
        for item in profile["columns_profile"]
        if "numeric" in item and item["non_null"] > 0
    ][:8]
    category_cols = [
        item
        for item in profile["columns_profile"]
        if item.get("top_values") and 1 < item["unique"] <= max(30, rows * 0.5)
    ][:8]
    date_cols = [item for item in profile["columns_profile"] if "date" in item][:4]
    missing = sorted(profile["columns_profile"], key=lambda item: item["missing_rate"], reverse=True)[:6]

    key_date = date_cols[0]["name"] if date_cols else None
    date_names = {item["name"] for item in date_cols}
    numeric_names = {item["name"] for item in numeric_cols}
    business_category_cols = [
        item
        for item in category_cols
        if item["name"] not in date_names and item["name"] not in numeric_names
    ]
    key_numeric = numeric_cols[0]["name"] if numeric_cols else None
    key_category = (
        business_category_cols[0]["name"]
        if business_category_cols
        else (category_cols[0]["name"] if category_cols else None)
    )

    working = frame.copy()
    trend_series: list[dict[str, Any]] = []
    trend_growth: float | None = None
    if key_date and key_numeric:
        parsed_date = pd.to_datetime(working[key_date], errors="coerce")
        metric = numeric_series(working, key_numeric)
        trend_frame = pd.DataFrame({"date": parsed_date, "metric": metric}).dropna()
        if not trend_frame.empty:
            monthly = (
                trend_frame.set_index("date")
                .groupby(pd.Grouper(freq="ME"))["metric"]
                .agg(["sum", "count"])
                .dropna()
                .tail(12)
            )
            for date, row in monthly.iterrows():
                trend_series.append(
                    {
                        "period": date.strftime("%Y-%m"),
                        "value": round(float(row["sum"]), 2),
                        "records": int(row["count"]),
                    }
                )
            if len(trend_series) >= 2:
                trend_growth = safe_rate(trend_series[-1]["value"], trend_series[-2]["value"])

    category_mix: list[dict[str, Any]] = []
    if key_category:
        if key_numeric:
            metric = numeric_series(working, key_numeric)
            mix_frame = pd.DataFrame({"category": working[key_category].fillna("未分类"), "metric": metric})
            grouped = mix_frame.dropna(subset=["metric"]).groupby("category")["metric"].agg(["sum", "count"])
            grouped = grouped.sort_values("sum", ascending=False)
            total_metric = float(grouped["sum"].sum()) if not grouped.empty else 0
            for name, row in grouped.head(8).iterrows():
                category_mix.append(
                    {
                        "name": str(name),
                        "amount": round(float(row["sum"]), 2),
                        "share": pct(float(row["sum"]), total_metric),
                        "records": int(row["count"]),
                        "metric": key_numeric,
                    }
                )
        else:
            counts = working[key_category].fillna("未分类").astype(str).value_counts().head(8)
            for name, count in counts.items():
                category_mix.append(
                    {
                        "name": str(name),
                        "amount": int(count),
                        "share": pct(int(count), rows),
                        "records": int(count),
                        "metric": "记录数",
                    }
                )

    label_col = (
        profile.get("semantic_fields", {}).get("title")
        or profile.get("semantic_fields", {}).get("id")
        or key_category
    )
    outliers: list[dict[str, Any]] = []
    for item in numeric_cols[:4]:
        col = item["name"]
        series = numeric_series(working, col)
        clean = series.dropna()
        if len(clean) < 5:
            continue
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr if iqr else clean.mean() + clean.std()
        selected = series[series > upper].sort_values(ascending=False).head(5)
        if selected.empty and clean.max() >= max(clean.mean() * 2, clean.median() * 2):
            selected = series.sort_values(ascending=False).head(3)
        for idx, value in selected.items():
            label = str(working.loc[idx, label_col])[:80] if label_col and label_col in working else f"第 {idx + 1} 行"
            outliers.append(
                {
                    "field": col,
                    "label": label,
                    "value": round(float(value), 2),
                    "baseline": round(float(clean.median()), 2),
                }
            )
    outliers = outliers[:10]

    kpis = [
        make_kpi("记录数", compact_number(rows), f"{cols} 个字段", "blue"),
        make_kpi("识别领域", domain.replace("-", " "), "可在生成后继续人工指定", "green"),
        make_kpi("数值字段", compact_number(len(numeric_cols)), "可用于规模、金额、效率分析", "orange"),
        make_kpi("分类字段", compact_number(len(category_cols)), "可用于结构和排名分析", "cyan"),
    ]
    if trend_growth is not None:
        kpis.append(make_kpi("最近趋势", format_rate(trend_growth), f"基于 {key_date} × {key_numeric}", "red" if trend_growth < -10 else "green"))
    kpis = kpis[:5]

    insights = []
    if requirement:
        insights.append(f"本报告按用户要求聚焦：{'、'.join(focus)}。")
    if category_mix:
        top = category_mix[0]
        if top["share"] >= 35:
            insights.append(
                f"{key_category} 中「{top['name']}」贡献 {top['share']}%，是最集中的结构项。"
            )
        else:
            insights.append(f"{key_category} 分布相对分散，最高分组占比 {top['share']}%，不存在单一分组绝对主导。")
    if numeric_cols:
        first_num = numeric_cols[0]
        insights.append(
            f"{first_num['name']} 总计 {compact_number(first_num['numeric'].get('sum'))}，"
            f"均值 {compact_number(first_num['numeric'].get('mean'))}。"
        )
    if trend_growth is not None:
        direction = "上升" if trend_growth >= 0 else "下降"
        insights.append(f"最近一期 {key_numeric} 较上一期{direction} {abs(trend_growth):.1f}%，需要结合业务背景判断是否为异常。")
    elif date_cols:
        first_date = date_cols[0]["date"]
        insights.append(f"数据时间范围约为 {first_date.get('min')} 至 {first_date.get('max')}。")
    if outliers:
        top_outlier = outliers[0]
        insights.append(
            f"{top_outlier['field']} 出现明显高值：{top_outlier['label']} 为 {compact_number(top_outlier['value'])}，"
            f"中位数约 {compact_number(top_outlier['baseline'])}。"
        )
    if missing and missing[0]["missing_rate"] > 0.2:
        insights.append(
            f"{missing[0]['name']} 缺失率 {pct(missing[0]['missing'], rows)}%，会影响后续细分分析。"
        )
    while len(insights) < 3:
        insights.append("当前表格已完成结构、数值、异常和口径检查，可作为第一版管理汇报基线。")

    risks = []
    if trend_growth is not None and trend_growth <= -15:
        risks.append(
            {
                "level": "medium",
                "title": "核心指标最近一期下滑",
                "detail": f"{key_numeric} 最近一期环比 {format_rate(trend_growth)}。",
                "action": "拆分到主要分类和责任主体，确认是一次性波动、数据口径变化，还是经营趋势下行。",
            }
        )
    if category_mix and category_mix[0]["share"] >= 60:
        risks.append(
            {
                "level": "medium",
                "title": "结构集中度较高",
                "detail": f"「{category_mix[0]['name']}」占比 {category_mix[0]['share']}%。",
                "action": "评估对单一类别、渠道、主体或项目的依赖风险，并准备替代方案。",
            }
        )
    if outliers:
        risks.append(
            {
                "level": "medium",
                "title": "存在需解释的数值异常",
                "detail": f"识别到 {len(outliers)} 个高值异常或明显偏离项。",
                "action": "逐条核对异常项是否真实、是否一次性发生，并在报告中补充业务解释。",
            }
        )
    for item in missing:
        if item["missing_rate"] >= 0.2:
            risks.append(
                {
                    "level": "medium",
                    "title": f"{item['name']} 缺失较多",
                    "detail": f"缺失 {item['missing']} 条，占 {pct(item['missing'], rows)}%。",
                    "action": "确认该字段是否为关键口径；若是，先补齐再对外汇报。",
                }
            )
    if not risks:
        risks.append(
            {
                "level": "low",
                "title": "未发现明显红灯项",
                "detail": "按已识别字段看，缺失、集中度、趋势下滑和异常高值风险有限。",
                "action": "如果用于正式汇报，建议补充目标口径、负责人字段和时间维度，进一步增强归因。",
            }
        )

    return {
        "domain": domain,
        "title": title or "通用业务表格分析报告",
        "subtitle": requirement or "从原始表格自动生成的管理层汇报材料",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": profile["source"],
        "sheet": profile.get("sheet"),
        "kpis": kpis,
        "insights": insights[:5],
        "category_columns": category_cols,
        "numeric_columns": numeric_cols,
        "date_columns": date_cols,
        "trend_series": trend_series,
        "category_mix": category_mix,
        "outliers": outliers,
        "risks": risks[:8],
        "assumptions": [
            f"分析焦点：{'、'.join(focus)}",
            f"推断领域：{domain}",
            f"核心数值字段：{key_numeric or '未识别'}",
            f"核心分类字段：{key_category or '未识别'}",
            f"核心时间字段：{key_date or '未识别'}",
            "未命中特定行业规则时，报告采用通用经营分析框架。",
        ],
        "profile": profile,
    }


def choose_report(
    frame: "pd.DataFrame", profile: dict[str, Any], requirement: str, title: str | None
) -> dict[str, Any]:
    domain = profile["inferred_domain"]["domain"]
    if domain == "devops-demand-pool":
        return build_devops_report(frame, profile, requirement, title)
    if domain in {"ecommerce-orders", "ecommerce-reviews"}:
        if domain == "ecommerce-reviews":
            return build_feedback_report(frame, profile, requirement, title)
        return build_ecommerce_report(frame, profile, requirement, title)
    if domain == "finance-expense":
        return build_finance_report(frame, profile, requirement, title)
    if domain == "crm-pipeline":
        return build_crm_report(frame, profile, requirement, title)
    if domain == "erp-inventory":
        return build_inventory_report(frame, profile, requirement, title)
    if domain == "support-tickets":
        return build_support_report(frame, profile, requirement, title)
    if domain == "hr-attendance":
        return build_hr_report(frame, profile, requirement, title)
    if domain == "survey-feedback":
        return build_feedback_report(frame, profile, requirement, title)
    return build_generic_report(frame, profile, requirement, title)


def render_report(report: dict[str, Any], style_key: str) -> str:
    theme = STYLE_THEMES.get(style_key, STYLE_THEMES["command-center"])
    body_class = theme["body_class"]
    report_json = json.dumps(report, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(report['title'])}</title>
  <style>
{base_css()}
  </style>
</head>
<body class="{body_class}">
  <canvas id="bgCanvas" aria-hidden="true"></canvas>
  <main class="page-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">{esc(report.get('domain', 'business-report'))} · {esc(theme['name'])}</p>
        <h1>{esc(report['title'])}</h1>
        <p class="subtitle">{esc(report.get('subtitle', ''))}</p>
      </div>
      <div class="meta-panel">
        <span>生成时间</span><strong>{esc(report.get('generated_at'))}</strong>
        <span>数据源</span><strong>{esc(Path(report.get('source', '')).name)}</strong>
        <span>工作表</span><strong>{esc(report.get('sheet') or '默认')}</strong>
      </div>
    </header>

    <section class="section">
      <div class="section-title"><span>01</span><h2>全局概览</h2></div>
      <div class="kpi-grid" id="kpiGrid"></div>
    </section>

    <section class="section two-col">
      <article class="card">
        <div class="card-title"><span>02</span><h2>关键洞察</h2></div>
        <div id="insightList" class="insight-list"></div>
      </article>
      <article class="card">
        <div class="card-title"><span>03</span><h2>口径假设</h2></div>
        <div id="assumptionList" class="assumption-list"></div>
      </article>
    </section>

    <section class="section" id="domainSection"></section>

    <section class="section">
      <div class="section-title"><span>90</span><h2>风险清单与行动建议</h2></div>
      <div class="risk-grid" id="riskGrid"></div>
    </section>
  </main>

  <script>
    window.__REPORT__ = {report_json};
{base_js()}
  </script>
</body>
</html>
"""


def base_css() -> str:
    return r"""
*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:"PingFang SC","Microsoft YaHei",Arial,sans-serif}body{overflow-x:hidden}.page-shell{position:relative;z-index:1;width:min(1180px,calc(100% - 32px));margin:0 auto;padding:44px 0 64px}#bgCanvas{position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}.theme-command{background:#08111f;color:#e5eefc}.theme-light{background:#f4f7fb;color:#142033}.theme-retail{background:#fff7ed;color:#1f2937}.theme-ledger{background:#101815;color:#e7f5ee}.theme-editorial{background:#fbf4e9;color:#241b15}.theme-studio{background:#101020;color:#eeeaff}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:24px;align-items:end;padding:32px 0 28px}.eyebrow{letter-spacing:.18em;text-transform:uppercase;font-size:12px;color:var(--muted);margin:0 0 12px}.hero h1{font-size:clamp(34px,5vw,64px);line-height:1.05;margin:0 0 14px;letter-spacing:0}.subtitle{font-size:18px;line-height:1.7;color:var(--muted);margin:0;max-width:760px}.meta-panel{border:1px solid var(--border);background:var(--card);border-radius:18px;padding:18px 18px;display:grid;grid-template-columns:84px 1fr;gap:8px 10px;box-shadow:var(--shadow)}.meta-panel span{color:var(--muted);font-size:12px}.meta-panel strong{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.section{margin:22px 0}.section-title,.card-title{display:flex;align-items:center;gap:10px;margin-bottom:14px}.section-title span,.card-title span{display:inline-flex;align-items:center;justify-content:center;min-width:34px;height:26px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:12px;font-weight:800}.section-title h2,.card-title h2{font-size:20px;margin:0}.two-col{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.card,.kpi,.cat-card,.risk-card,.metric-card{background:var(--card);border:1px solid var(--border);border-radius:18px;box-shadow:var(--shadow);backdrop-filter:blur(14px)}.card{padding:22px}.kpi-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}.kpi{position:relative;overflow:hidden;padding:18px 16px;min-height:132px}.kpi:before{content:"";position:absolute;inset:0 0 auto;height:3px;background:var(--tone,#38bdf8)}.kpi-label{font-size:13px;color:var(--muted);margin-bottom:10px}.kpi-value{font-size:36px;font-weight:850;line-height:1;margin-bottom:10px}.kpi-sub{font-size:12px;line-height:1.5;color:var(--muted)}.insight-list{display:grid;gap:12px}.insight{padding:14px 14px;border-radius:14px;background:var(--panel);border:1px solid var(--border);line-height:1.65}.insight strong{color:var(--accent)}.assumption-list{display:grid;gap:9px}.assumption{padding:10px 12px;border-radius:12px;background:var(--panel);color:var(--muted);font-size:13px}.funnel-layout{display:grid;grid-template-columns:380px minmax(0,1fr);gap:18px}.funnel{display:flex;flex-direction:column;align-items:center;padding:18px}.funnel-row{height:42px;margin-top:-5px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:12px;text-shadow:0 1px 2px rgba(0,0,0,.28);clip-path:polygon(8% 0,92% 0,100% 100%,0 100%);min-width:130px}.funnel-row:first-child{margin-top:0}.bar-list{display:grid;gap:10px}.bar-item{display:grid;grid-template-columns:118px 1fr 76px minmax(120px,.7fr);gap:10px;align-items:center;font-size:13px}.bar-item small{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:10px;background:var(--panel);border-radius:999px;overflow:hidden}.bar-fill{height:100%;border-radius:999px;background:var(--accent)}.cat-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.cat-card{padding:18px;position:relative;overflow:hidden}.cat-card:before{content:"";position:absolute;inset:0 0 auto;height:3px;background:var(--health)}.cat-head{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.cat-name{font-size:20px;font-weight:850}.badge{font-size:12px;border-radius:999px;padding:5px 9px;background:var(--panel);color:var(--muted);white-space:nowrap}.cat-rate{font-size:34px;font-weight:900;color:var(--health);margin-bottom:8px}.mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.mini{padding:9px;border-radius:12px;background:var(--panel);text-align:center}.mini b{display:block;font-size:18px}.mini span{font-size:11px;color:var(--muted)}.owner-line{margin-top:12px;font-size:12px;color:var(--muted);line-height:1.5}.special-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.special{padding:14px;border-radius:14px;background:var(--panel);border:1px solid var(--border)}.special h3{margin:0 0 8px;font-size:15px}.special-meta{display:flex;flex-wrap:wrap;gap:8px;color:var(--muted);font-size:12px}.sample-list{margin:10px 0 0;padding:0;list-style:none;display:grid;gap:7px}.sample-list li{font-size:12px;color:var(--muted);line-height:1.45}.risk-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.risk-card{padding:18px;border-left:4px solid var(--risk)}.risk-card h3{margin:0 0 8px;font-size:17px}.risk-card p{margin:0 0 10px;color:var(--muted);line-height:1.6}.risk-card .action{padding:10px 12px;border-radius:12px;background:var(--panel);font-size:13px;line-height:1.55}.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.metric-card{padding:18px}.metric-card h3{margin:0 0 12px}.top-values{display:grid;gap:9px}.top-row{display:grid;grid-template-columns:minmax(0,1fr) 60px;gap:10px;align-items:center;font-size:13px}.data-table{width:100%;border-collapse:separate;border-spacing:0 8px}.data-table th{color:var(--muted);font-size:12px;text-align:left;font-weight:700;padding:0 10px 4px}.data-table td{background:var(--panel);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:11px 10px;font-size:13px;line-height:1.45}.data-table td:first-child{border-left:1px solid var(--border);border-radius:12px 0 0 12px}.data-table td:last-child{border-right:1px solid var(--border);border-radius:0 12px 12px 0}.theme-command{--card:rgba(10,19,43,.82);--panel:rgba(15,28,58,.76);--border:rgba(56,189,248,.18);--muted:#93a4bb;--accent:#38bdf8;--accent-soft:rgba(56,189,248,.13);--shadow:0 18px 50px rgba(0,0,0,.28)}.theme-light{--card:rgba(255,255,255,.92);--panel:#eef3f8;--border:#dbe4ef;--muted:#64748b;--accent:#1d4ed8;--accent-soft:#dbeafe;--shadow:0 18px 45px rgba(15,23,42,.08)}.theme-retail{--card:rgba(255,255,255,.9);--panel:#fff1e7;--border:#fed7aa;--muted:#7c5b45;--accent:#f97316;--accent-soft:#ffedd5;--shadow:0 18px 45px rgba(154,52,18,.1)}.theme-ledger{--card:rgba(15,31,27,.88);--panel:rgba(30,54,48,.72);--border:rgba(52,211,153,.18);--muted:#9cb5aa;--accent:#34d399;--accent-soft:rgba(52,211,153,.14);--shadow:0 18px 50px rgba(0,0,0,.24)}.theme-editorial{--card:rgba(255,252,245,.94);--panel:#f4eadb;--border:#e8d8c3;--muted:#7b6653;--accent:#9f6b44;--accent-soft:#ead9c3;--shadow:0 18px 45px rgba(89,58,31,.09)}.theme-studio{--card:rgba(18,18,32,.86);--panel:rgba(38,34,58,.72);--border:rgba(139,92,246,.2);--muted:#a6a0bd;--accent:#8b5cf6;--accent-soft:rgba(139,92,246,.16);--shadow:0 18px 50px rgba(0,0,0,.26)}@media(max-width:980px){.hero,.two-col,.funnel-layout{grid-template-columns:1fr}.kpi-grid,.cat-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.risk-grid,.special-grid,.metric-grid{grid-template-columns:1fr}}@media(max-width:640px){.page-shell{width:min(100% - 20px,1180px);padding-top:24px}.kpi-grid,.cat-grid{grid-template-columns:1fr}.hero h1{font-size:36px}.bar-item{grid-template-columns:1fr}.bar-item small{white-space:normal}.meta-panel{grid-template-columns:72px 1fr}.data-table{display:block;overflow-x:auto;white-space:nowrap}}
"""


def base_js() -> str:
    return r"""
const data = window.__REPORT__;
const toneMap = {blue:"#38bdf8",green:"#34d399",orange:"#f59e0b",cyan:"#22d3ee",red:"#f87171"};
const healthMap = {green:"#34d399",amber:"#f59e0b",red:"#ef4444"};
function $(id){return document.getElementById(id)}
function escText(v){return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}
function compactNumber(v){
  if(v === null || v === undefined || v === "-") return "-";
  const n = typeof v === "string" ? parseFloat(v) : v;
  if(isNaN(n)) return String(v);
  if(Math.abs(n) >= 1e8) return (n/1e8).toFixed(1) + "亿";
  if(Math.abs(n) >= 1e4) return (n/1e4).toFixed(1) + "万";
  if(Number.isFinite(n) && !Number.isInteger(n)) return n.toLocaleString("zh-CN", {minimumFractionDigits:1, maximumFractionDigits:1});
  return n.toLocaleString("zh-CN");
}
function renderBasics(){
  $("kpiGrid").innerHTML = (data.kpis || []).map(k => `<article class="kpi" style="--tone:${toneMap[k.tone] || toneMap.blue}"><div class="kpi-label">${escText(k.label)}</div><div class="kpi-value">${escText(k.value)}</div><div class="kpi-sub">${escText(k.sub)}</div></article>`).join("");
  $("insightList").innerHTML = (data.insights || []).map((x,i)=>`<div class="insight"><strong>${String(i+1).padStart(2,"0")}.</strong> ${escText(x)}</div>`).join("");
  $("assumptionList").innerHTML = (data.assumptions || []).map(x=>`<div class="assumption">${escText(x)}</div>`).join("");
  $("riskGrid").innerHTML = (data.risks || []).map(r => {
    const color = r.level === "high" ? "#ef4444" : r.level === "medium" ? "#f59e0b" : "#38bdf8";
    return `<article class="risk-card" style="--risk:${color}"><h3>${escText(r.title)}</h3><p>${escText(r.detail)}</p><div class="action">${escText(r.action)}</div></article>`;
  }).join("");
}
function renderDevops(){
  const funnelMax = Math.max(...(data.funnel || []).map(x=>x.value), 1);
  const funnelHtml = `<div class="section-title"><span>04</span><h2>需求生命周期漏斗</h2></div><div class="card funnel-layout"><div class="funnel">${(data.funnel || []).map((x,i)=>{const w=92-(i*4);return `<div class="funnel-row" title="${x.desc}" style="width:${Math.max(44,w)}%;background:${x.color}">${x.label} · ${x.value}</div>`}).join("")}</div><div class="bar-list">${(data.funnel || []).map(x=>`<div class="bar-item"><span>${x.label}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(2,x.value/funnelMax*100)}%;background:${x.color}"></div></div><strong>${x.share}%</strong></div>`).join("")}</div></div>`;
  const catHtml = `<div class="section-title"><span>05</span><h2>各一级分类交付健康度</h2></div><div class="cat-grid">${(data.categories || []).map(c=>`<article class="cat-card" style="--health:${healthMap[c.health] || healthMap.amber}"><div class="cat-head"><div class="cat-name">${escText(c.name)}</div><div class="badge">${c.health === "green" ? "稳定交付" : c.health === "red" ? "严重风险" : "橙色预警"}</div></div><div class="cat-rate">${c.rate}%</div><div class="bar-track"><div class="bar-fill" style="width:${c.rate}%;background:var(--health)"></div></div><div class="mini-grid"><div class="mini"><b>${c.total}</b><span>总量</span></div><div class="mini"><b>${c.released}</b><span>已发布</span></div><div class="mini"><b>${c.backlog}</b><span>积压</span></div><div class="mini"><b>${c.in_progress}</b><span>推进中</span></div></div><div class="owner-line">主要经办人：${(c.owners || []).join("、") || "未识别"}</div></article>`).join("")}</div>`;
  const specialHtml = `<div class="section-title"><span>06</span><h2>专项下钻</h2></div><div class="special-grid">${(data.specials || []).slice(0,12).map(s=>`<article class="special"><h3>${escText(s.category ? s.category + " / " + s.name : s.name)}</h3><div class="special-meta"><span>总量 ${s.total}</span><span>发布率 ${s.rate}%</span><span>Backlog ${s.backlog}</span><span>评审 ${s.tech_review}</span></div><ul class="sample-list">${(s.items || []).slice(0,4).map(item=>`<li>${escText(item.title)}${item.owner ? " · " + escText(item.owner) : ""}</li>`).join("")}</ul></article>`).join("")}</div>`;
  $("domainSection").innerHTML = funnelHtml + catHtml + specialHtml;
}
function renderEcommerce(){
  const trend = data.gmv_trend || [];
  const catContrib = data.category_contribution || [];
  const chContrib = data.channel_contribution || [];
  const trendHtml = trend.length ? `<div class="section-title"><span>04</span><h2>GMV 趋势</h2></div><div class="card"><div class="bar-list">${trend.map(d=>`<div class="bar-item"><span>${d.period}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(2,d.gmv/Math.max(...trend.map(x=>x.gmv),1)*100)}%;background:var(--accent)"></div></div><strong>¥${compactNumber(d.gmv)}</strong></div>`).join("")}</div></div>` : "";
  const catHtml = catContrib.length ? `<div class="section-title"><span>05</span><h2>品类贡献</h2></div><div class="cat-grid">${catContrib.map(c=>`<article class="cat-card" style="--health:var(--accent)"><div class="cat-head"><div class="cat-name">${escText(c.name)}</div><div class="badge">${c.share}%</div></div><div class="cat-rate">¥${compactNumber(c.gmv)}</div><div class="bar-track"><div class="bar-fill" style="width:${c.share}%;background:var(--accent)"></div></div><div class="mini-grid"><div class="mini"><b>${c.orders}</b><span>订单</span></div><div class="mini"><b>${c.share}%</b><span>占比</span></div></div></article>`).join("")}</div>` : "";
  const chHtml = chContrib.length ? `<div class="section-title"><span>06</span><h2>渠道贡献</h2></div><div class="cat-grid">${chContrib.map(c=>`<article class="cat-card" style="--health:var(--accent)"><div class="cat-head"><div class="cat-name">${escText(c.name)}</div><div class="badge">${c.share}%</div></div><div class="cat-rate">¥${compactNumber(c.gmv)}</div><div class="bar-track"><div class="bar-fill" style="width:${c.share}%;background:var(--accent)"></div></div><div class="mini-grid"><div class="mini"><b>${c.orders}</b><span>订单</span></div><div class="mini"><b>${c.share}%</b><span>占比</span></div></div></article>`).join("")}</div>` : "";
  const returnHtml = data.return_rate !== undefined ? `<div class="section-title"><span>07</span><h2>退货分析</h2></div><div class="card"><div class="kpi-grid" style="grid-template-columns:repeat(3,1fr)"><div class="kpi" style="--tone:${toneMap.red}"><div class="kpi-label">退货率</div><div class="kpi-value">${data.return_rate}%</div><div class="kpi-sub">${data.returned_orders} 单退货</div></div><div class="kpi" style="--tone:${toneMap.blue}"><div class="kpi-label">总GMV</div><div class="kpi-value">¥${compactNumber(data.total_gmv)}</div><div class="kpi-sub">客单价 ¥${compactNumber(data.avg_order_value)}</div></div><div class="kpi" style="--tone:${toneMap.green}"><div class="kpi-label">成交订单</div><div class="kpi-value">${compactNumber(data.total_gmv ? (data.total_gmv - data.returned_orders * (data.avg_order_value || 0)) : 0)}</div><div class="kpi-sub">剔除退货后预估</div></div></div></div>` : "";
  $("domainSection").innerHTML = trendHtml + catHtml + chHtml + returnHtml;
}
function renderFinance(){
  const trend = data.period_trend || [];
  const entities = data.entity_performance || [];
  const mix = data.mix_analysis || [];
  const exceptions = data.exception_items || [];
  const money = v => (v === null || v === undefined || v === "-") ? "-" : "¥" + compactNumber(v);
  const pct = v => (v === null || v === undefined || isNaN(Number(v))) ? "-" : Number(v).toFixed(1) + "%";
  const maxRevenue = Math.max(...trend.map(x=>Math.abs(x.revenue || 0)), 1);
  const trendHtml = trend.length ? `<div class="section-title"><span>04</span><h2>季度趋势</h2></div><div class="card"><table class="data-table"><thead><tr><th>期间</th><th>营收</th><th>净利润</th><th>毛利率</th><th>平均负债率</th><th>风险/亏损</th></tr></thead><tbody>${trend.map(d=>`<tr><td>${escText(d.period)}</td><td><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3,Math.abs(d.revenue || 0)/maxRevenue*100)}%"></div></div>${money(d.revenue)}</td><td>${money(d.profit)}</td><td>${pct(d.gross_margin)}</td><td>${pct(d.debt)}</td><td>${d.high_risk || 0} 高风险 / ${d.losses || 0} 亏损</td></tr>`).join("")}</tbody></table></div>` : "";
  const entityHtml = entities.length ? `<div class="section-title"><span>05</span><h2>主体表现与风险排行</h2></div><div class="cat-grid">${entities.slice(0,9).map(e=>{const risk=(e.high_risk||0)>0 || (e.max_debt||0)>=70 || (e.losses||0)>0;return `<article class="cat-card" style="--health:${risk ? healthMap.red : healthMap.green}"><div class="cat-head"><div class="cat-name">${escText(e.name)}</div><div class="badge">${risk ? "重点关注" : "相对稳健"}</div></div><div class="cat-rate">${money(e.revenue ?? e.profit)}</div><div class="mini-grid"><div class="mini"><b>${money(e.profit)}</b><span>净利润</span></div><div class="mini"><b>${pct(e.profit_margin)}</b><span>净利率</span></div><div class="mini"><b>${pct(e.max_debt)}</b><span>最高负债</span></div><div class="mini"><b>${e.high_risk || 0}</b><span>高风险</span></div></div><div class="owner-line">亏损期数：${e.losses || 0}；中风险：${e.medium_risk || 0}</div></article>`}).join("")}</div>` : "";
  const mixHtml = mix.length ? `<div class="section-title"><span>06</span><h2>结构贡献</h2></div><div class="card"><div class="bar-list">${mix.map(m=>`<div class="bar-item"><span>${escText(m.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3,m.share || 0)}%"></div></div><strong>${m.share}%</strong></div>`).join("")}</div></div>` : "";
  const exceptionHtml = exceptions.length ? `<div class="section-title"><span>07</span><h2>异常与风险明细</h2></div><div class="card"><table class="data-table"><thead><tr><th>主体</th><th>期间</th><th>触发原因</th><th>营收</th><th>净利润</th><th>负债率</th></tr></thead><tbody>${exceptions.map(x=>`<tr><td>${escText(x.entity)}</td><td>${escText(x.period)}</td><td>${escText(x.reason)}</td><td>${money(x.revenue)}</td><td>${money(x.profit)}</td><td>${pct(x.debt)}</td></tr>`).join("")}</tbody></table></div>` : "";
  $("domainSection").innerHTML = trendHtml + entityHtml + mixHtml + exceptionHtml;
}
function renderAnalysisSections(){
  const sections = data.analysis_sections || [];
  const html = sections.map((section, idx) => {
    const number = String(idx + 4).padStart(2, "0");
    const title = `<div class="section-title"><span>${number}</span><h2>${escText(section.title)}</h2></div>`;
    if(section.kind === "bars"){
      const rows = section.rows || [];
      const maxValue = Math.max(...rows.map(r => Math.abs(Number(r.value) || 0)), 1);
      return title + `<div class="card"><div class="bar-list">${rows.map(r => `<div class="bar-item"><span>${escText(r.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3, Math.abs(Number(r.value) || 0) / maxValue * 100)}%"></div></div><strong>${r.share !== undefined && r.share !== 0 ? escText(r.share) + "%" : compactNumber(r.value)}</strong><small>${escText(r.detail || "")}</small></div>`).join("")}</div></div>`;
    }
    if(section.kind === "cards"){
      const rows = section.rows || [];
      return title + `<div class="cat-grid">${rows.map(r => `<article class="cat-card" style="--health:${toneMap[r.tone] || "var(--accent)"}"><div class="cat-head"><div class="cat-name">${escText(r.title || r.name)}</div><div class="badge">${escText(r.badge || "")}</div></div><div class="cat-rate">${escText(r.value ?? "")}</div><div class="owner-line">${escText(r.detail || r.sub || "")}</div></article>`).join("")}</div>`;
    }
    if(section.kind === "table"){
      const cols = section.columns || [];
      const rows = section.rows || [];
      return title + `<div class="card"><table class="data-table"><thead><tr>${cols.map(c => `<th>${escText(c.label || c.key)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${cols.map(c => `<td>${escText(row[c.key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    }
    return "";
  }).join("");
  $("domainSection").innerHTML = html;
}
function renderGeneric(){
  const cats = data.category_columns || [];
  const nums = data.numeric_columns || [];
  const trend = data.trend_series || [];
  const mix = data.category_mix || [];
  const outliers = data.outliers || [];
  const maxTrend = Math.max(...trend.map(x=>Math.abs(x.value || 0)), 1);
  const trendHtml = trend.length ? `<div class="section-title"><span>04</span><h2>趋势变化</h2></div><div class="card"><div class="bar-list">${trend.map(d=>`<div class="bar-item"><span>${escText(d.period)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3,Math.abs(d.value || 0)/maxTrend*100)}%"></div></div><strong>${compactNumber(d.value)}</strong></div>`).join("")}</div></div>` : "";
  const mixHtml = mix.length ? `<div class="section-title"><span>05</span><h2>结构贡献</h2></div><div class="cat-grid">${mix.map(c=>`<article class="cat-card" style="--health:var(--accent)"><div class="cat-head"><div class="cat-name">${escText(c.name)}</div><div class="badge">${escText(c.metric || "指标")} · ${c.share}%</div></div><div class="cat-rate">${compactNumber(c.amount)}</div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(3,c.share || 0)}%;background:var(--accent)"></div></div><div class="owner-line">记录数：${c.records}</div></article>`).join("")}</div>` : "";
  const catHtml = (!mix.length && cats.length) ? `<div class="section-title"><span>05</span><h2>主要分类分布</h2></div><div class="metric-grid">${cats.map(c=>`<article class="metric-card"><h3>${escText(c.name)}</h3><div class="top-values">${(c.top_values || []).slice(0,6).map(v=>`<div class="top-row"><span>${escText(v.value)}</span><strong>${v.count}</strong></div>`).join("")}</div></article>`).join("")}</div>` : "";
  const numHtml = nums.length ? `<div class="section-title"><span>06</span><h2>数值字段概览</h2></div><div class="metric-grid">${nums.map(n=>`<article class="metric-card"><h3>${escText(n.name)}</h3><div class="mini-grid"><div class="mini"><b>${compactNumber(n.numeric.sum)}</b><span>总计</span></div><div class="mini"><b>${compactNumber(n.numeric.mean)}</b><span>均值</span></div><div class="mini"><b>${compactNumber(n.numeric.max)}</b><span>最大</span></div><div class="mini"><b>${compactNumber(n.numeric.min)}</b><span>最小</span></div></div></article>`).join("")}</div>` : "";
  const outlierHtml = outliers.length ? `<div class="section-title"><span>07</span><h2>异常高值</h2></div><div class="card"><table class="data-table"><thead><tr><th>字段</th><th>对象</th><th>数值</th><th>基准中位数</th></tr></thead><tbody>${outliers.map(x=>`<tr><td>${escText(x.field)}</td><td>${escText(x.label)}</td><td>${compactNumber(x.value)}</td><td>${compactNumber(x.baseline)}</td></tr>`).join("")}</tbody></table></div>` : "";
  $("domainSection").innerHTML = trendHtml + mixHtml + catHtml + numHtml + outlierHtml;
}
function animateBg(){
  const canvas = $("bgCanvas");
  const ctx = canvas.getContext("2d");
  let points = [];
  function resize(){canvas.width=innerWidth;canvas.height=innerHeight;points=Array.from({length:46},()=>({x:Math.random()*canvas.width,y:Math.random()*canvas.height,vx:(Math.random()-.5)*.35,vy:(Math.random()-.5)*.35,r:Math.random()*2+0.4}))}
  function step(){ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle="rgba(56,189,248,.18)";for(const p of points){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>canvas.width)p.vx*=-1;if(p.y<0||p.y>canvas.height)p.vy*=-1;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill()}requestAnimationFrame(step)}
  resize();addEventListener("resize",resize);step();
}
renderBasics();
if(data.domain === "devops-demand-pool") renderDevops();
else if(data.domain === "ecommerce-orders") renderEcommerce();
else if(data.domain === "finance-expense") renderFinance();
else if(data.analysis_sections) renderAnalysisSections();
else renderGeneric();
animateBg();
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a self-contained HTML report.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--sheet", help="Excel sheet name. Defaults to first sheet.")
    parser.add_argument("--requirement", default="", help="User's analysis request.")
    parser.add_argument("--title", help="Report title.")
    parser.add_argument("--style", choices=sorted(STYLE_THEMES), help="Visual style preset.")
    parser.add_argument("--output", type=Path, help="Output HTML path.")
    parser.add_argument("--profile-output", type=Path, help="Optional JSON profile output path.")
    args = parser.parse_args()

    frame, table = read_any_table(args.input, args.sheet)
    profile = build_profile(table)
    report = choose_report(frame, profile, args.requirement, args.title)
    style = args.style or infer_default_style(report["domain"])
    output = args.output or args.input.with_suffix(".report.html")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(report, style), encoding="utf-8")
    if args.profile_output:
        args.profile_output.parent.mkdir(parents=True, exist_ok=True)
        args.profile_output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
