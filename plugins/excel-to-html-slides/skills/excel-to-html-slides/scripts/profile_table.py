#!/usr/bin/env python3
"""Profile a spreadsheet or delimited table for excel-to-html-slides.

The script emits compact JSON that an agent can use to choose a report
blueprint and generate grounded analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - user environment guard
    raise SystemExit(
        "Missing dependency: pandas. Install with `pip install pandas openpyxl`."
    ) from exc


DOMAIN_SIGNALS = {
    "devops-demand-pool": [
        "需求",
        "工作项",
        "状态",
        "优先级",
        "经办人",
        "产品负责人",
        "迭代",
        "版本",
        "预计上线",
        "一级分类",
        "业务专项",
        "backlog",
        "released",
    ],
    "ecommerce-orders": [
        "订单",
        "支付",
        "金额",
        "gmv",
        "sku",
        "商品",
        "店铺",
        "平台",
        "退款",
        "地区",
        "下单",
    ],
    "ecommerce-reviews": [
        "评价",
        "评分",
        "星级",
        "评论",
        "差评",
        "商品",
        "门店",
        "售后",
    ],
    "crm-pipeline": [
        "客户",
        "线索",
        "商机",
        "商机名称",
        "商机金额",
        "阶段",
        "销售",
        "客户经理",
        "预计金额",
        "预计成交",
        "预计签约",
        "赢单",
        "输单",
        "跟进",
        "下次跟进",
        "来源",
    ],
    "erp-inventory": [
        "物料",
        "库存",
        "库存金额",
        "可用库存",
        "现存量",
        "入库",
        "出库",
        "销量",
        "仓库",
        "供应商",
        "采购",
        "安全库存",
        "周转",
        "缺货",
        "呆滞",
    ],
    "finance-expense": [
        "费用",
        "成本",
        "收入",
        "营收",
        "营业收入",
        "利润",
        "净利润",
        "毛利率",
        "净利率",
        "资产负债率",
        "负债率",
        "研发投入",
        "现金流",
        "季度",
        "财务",
        "预算",
        "实际",
        "差异",
        "发票",
        "付款",
        "科目",
    ],
    "hr-attendance": [
        "员工",
        "工号",
        "部门",
        "岗位",
        "考勤",
        "绩效",
        "得分",
        "评分",
        "工时",
        "加班",
        "异常",
        "入职",
        "离职",
        "薪资",
    ],
    "support-tickets": [
        "工单",
        "客服",
        "坐席",
        "处理时长",
        "解决时长",
        "首次响应",
        "满意度",
        "投诉",
        "问题类型",
        "问题分类",
        "响应",
        "解决",
        "超时",
        "sla",
    ],
    "survey-feedback": ["问卷", "选项", "提交时间", "姓名", "部门", "城市", "人群", "满意度", "反馈", "建议", "NPS", "调研"],
}


SEMANTIC_FIELDS = {
    "id": ["编号", "id", "key", "工作项id", "订单号", "客户id", "物料编码", "工单号", "员工编号"],
    "title": ["标题", "名称", "summary", "需求标题", "商品名称", "客户名称", "商机名称", "项目名称"],
    "description": ["描述", "说明", "description", "评论", "反馈", "备注"],
    "status": ["状态", "status", "阶段", "流程状态", "商机阶段", "解决状态", "考勤状态"],
    "priority": ["优先级", "priority", "业务优先级"],
    "category": ["一级分类", "业务线", "模块", "系统", "需求分类", "品类", "分类", "问题类型", "问题分类", "科目"],
    "subcategory": ["二级分类", "三级分类", "业务专项", "专题", "子类"],
    "owner": ["经办人", "负责人", "owner", "assignee", "销售负责人", "销售员", "业务员", "客户经理", "客服"],
    "product_owner": ["产品负责人", "pm", "产品"],
    "tester": ["测试", "qa"],
    "amount": ["金额", "gmv", "支付金额", "收入", "销售额", "预计金额", "商机金额", "合同金额", "库存金额"],
    "quantity": ["数量", "件数", "销量", "库存", "可用库存", "现存量"],
    "date": ["日期", "时间", "创建时间", "下单时间", "提交时间", "提出时间", "评价时间", "跟进时间"],
    "period": ["季度", "月份", "月度", "期间", "报告期", "年月"],
    "planned_date": ["预计上线", "预计结束", "计划完成", "预计升级"],
    "revenue": ["营收", "营业收入", "收入", "销售额", "revenue"],
    "profit": ["净利润", "利润总额", "营业利润", "利润", "profit"],
    "margin": ["毛利率", "净利率", "利润率", "margin"],
    "debt_ratio": ["资产负债率", "负债率", "debt ratio"],
    "risk": ["风险等级", "风险", "risk"],
    "rating": ["评分", "星级", "满意度", "NPS", "rating"],
    "sla": ["SLA", "是否超时", "超时", "逾期"],
}


@dataclass
class TableData:
    path: Path
    sheet: str | None
    frame: "pd.DataFrame"
    all_sheets: list[str]


def normalize_name(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    # Convert numpy types to Python native types early
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (float, int)):
        if math.isnan(value) or math.isinf(value):
            return None
        if isinstance(value, float):
            return round(value, 6)
        return int(value)
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    return str(value)


def read_table(path: Path, sheet: str | None = None) -> TableData:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        workbook = pd.ExcelFile(path)
        sheet_name = sheet or workbook.sheet_names[0]
        frame = workbook.parse(sheet_name)
        return TableData(path, sheet_name, cleanup_frame(frame), workbook.sheet_names)
    if suffix in {".csv", ".tsv"}:
        sep = "\t" if suffix == ".tsv" else sniff_delimiter(path)
        frame = pd.read_csv(path, sep=sep)
        return TableData(path, None, cleanup_frame(frame), [])
    raise SystemExit(f"Unsupported file type: {suffix}")


def sniff_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="ignore")[:4096]
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        return ","


def cleanup_frame(frame: "pd.DataFrame") -> "pd.DataFrame":
    frame = frame.copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    frame = frame.dropna(how="all")
    frame = frame.loc[:, [not str(c).startswith("Unnamed:") for c in frame.columns]]
    return frame


def infer_semantic_fields(columns: list[str]) -> dict[str, str]:
    normalized = {col: normalize_name(col) for col in columns}
    result: dict[str, str] = {}
    for semantic, aliases in SEMANTIC_FIELDS.items():
        alias_norm = [normalize_name(alias) for alias in aliases]
        for col, norm in normalized.items():
            if any(alias in norm or norm in alias for alias in alias_norm):
                result[semantic] = col
                break
    return result


def infer_domain(columns: list[str], frame: "pd.DataFrame") -> dict[str, Any]:
    haystack = " ".join(columns).lower()
    sample_values = []
    for col in columns[:30]:
        values = frame[col].dropna().astype(str).head(30).tolist()
        sample_values.extend(values)
    haystack += " " + " ".join(sample_values).lower()

    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}
    for domain, signals in DOMAIN_SIGNALS.items():
        hits = [signal for signal in signals if normalize_name(signal) in normalize_name(haystack)]
        scores[domain] = len(hits)
        matched[domain] = hits
    best = max(scores, key=scores.get) if scores else "generic-table"
    if scores.get(best, 0) < 2:
        best = "generic-table"
    return {"domain": best, "scores": scores, "matched_signals": matched.get(best, [])}


def column_profile(frame: "pd.DataFrame", max_top: int = 8) -> list[dict[str, Any]]:
    rows = len(frame)
    profile = []
    for col in frame.columns:
        series = frame[col]
        non_null = int(series.notna().sum())
        unique = int(series.nunique(dropna=True))
        item: dict[str, Any] = {
            "name": col,
            "dtype": str(series.dtype),
            "non_null": non_null,
            "missing": rows - non_null,
            "missing_rate": round((rows - non_null) / rows, 4) if rows else 0,
            "unique": unique,
        }
        if non_null:
            if pd.api.types.is_numeric_dtype(series):
                numeric = pd.to_numeric(series, errors="coerce").dropna()
                if len(numeric):
                    item["numeric"] = {
                        "min": json_safe(numeric.min()),
                        "max": json_safe(numeric.max()),
                        "mean": json_safe(numeric.mean()),
                        "median": json_safe(numeric.median()),
                        "sum": json_safe(numeric.sum()),
                    }
            parsed_dates = parse_date_series_if_likely(col, series)
            if parsed_dates is not None and parsed_dates.notna().sum() >= max(3, min(non_null, rows) * 0.5):
                item["date"] = {
                    "min": json_safe(parsed_dates.min()),
                    "max": json_safe(parsed_dates.max()),
                    "non_null": int(parsed_dates.notna().sum()),
                }
            if unique <= 50 or series.dtype == "object":
                top = (
                    series.dropna()
                    .astype(str)
                    .str.strip()
                    .replace("", pd.NA)
                    .dropna()
                    .value_counts()
                    .head(max_top)
                )
                item["top_values"] = [
                    {"value": str(idx)[:120], "count": int(count)}
                    for idx, count in top.items()
                ]
        profile.append(item)
    return profile


def parse_date_series_if_likely(col: str, series: "pd.Series") -> "pd.Series | None":
    """Parse dates only for columns that look date-like enough to avoid noisy warnings."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    col_hint = any(token in normalize_name(col) for token in ["日期", "时间", "date", "time"])
    sample = series.dropna().astype(str).head(30)
    pattern_hits = sample.str.contains(r"\d{4}[-/年]\d{1,2}(?:[-/月]\d{1,2})?", regex=True).sum()
    if not col_hint and pattern_hits < max(3, len(sample) * 0.4):
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce")


def sample_rows(frame: "pd.DataFrame", limit: int = 5) -> list[dict[str, Any]]:
    rows = []
    for record in frame.head(limit).to_dict(orient="records"):
        rows.append({str(k): json_safe(v) for k, v in record.items()})
    return rows


def build_profile(table: TableData, sample_limit: int = 5) -> dict[str, Any]:
    frame = table.frame
    columns = list(frame.columns)
    semantics = infer_semantic_fields(columns)
    return {
        "source": str(table.path),
        "sheet": table.sheet,
        "all_sheets": table.all_sheets,
        "rows": int(len(frame)),
        "columns": int(len(columns)),
        "column_names": columns,
        "semantic_fields": semantics,
        "inferred_domain": infer_domain(columns, frame),
        "columns_profile": column_profile(frame),
        "sample_rows": sample_rows(frame, sample_limit),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile an Excel/CSV table.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--sheet", help="Excel sheet name. Defaults to first sheet.")
    parser.add_argument("--output", type=Path, help="Write JSON profile to this path.")
    parser.add_argument("--sample-rows", type=int, default=5)
    args = parser.parse_args()

    table = read_table(args.input, args.sheet)
    profile = build_profile(table, args.sample_rows)
    payload = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
