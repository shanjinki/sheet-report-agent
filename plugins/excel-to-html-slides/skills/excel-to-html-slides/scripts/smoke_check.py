#!/usr/bin/env python3
"""Run a dependency-light smoke check for excel-to-html-slides."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CASES = [
    (
        "examples/sample_demands.csv",
        "分析需求池整体健康度、积压风险和管理建议",
        ["需求池全景分析报告", "需求生命周期漏斗", "风险清单"],
    ),
    (
        "examples/sample_finance.csv",
        "分析财务经营表现，生成管理层汇报材料，突出关键指标、风险和行动建议",
        ["财务经营绩效分析报告", "季度趋势", "主体表现与风险排行", "异常与风险明细"],
    ),
    (
        "examples/sample_crm.csv",
        "分析销售 pipeline 健康度、跟进风险和行动建议",
        ["CRM 商机管道分析报告", "销售漏斗阶段分布", "跟进风险明细"],
    ),
    (
        "examples/sample_inventory.csv",
        "分析库存缺货、呆滞库存、供应商集中度和补货建议",
        ["库存与采购风险分析报告", "供应商集中度", "缺货与呆滞风险明细"],
    ),
    (
        "examples/sample_support.csv",
        "分析客服工单 SLA、问题类型、处理人负载和服务风险",
        ["客服工单 SLA 分析报告", "问题类型分布", "SLA 与满意度风险明细"],
    ),
    (
        "examples/sample_hr.csv",
        "分析部门绩效、考勤异常、高工时负载和管理建议",
        ["HR 人员运营分析报告", "部门表现/覆盖", "人员异常明细"],
    ),
    (
        "examples/sample_feedback.csv",
        "分析问卷满意度、负面反馈主题和改进建议",
        ["用户反馈与评论洞察报告", "评分分布", "代表性反馈摘录"],
    ),
]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="excel-to-html-slides-") as tmp:
        tmpdir = Path(tmp)
        for index, (source, requirement, needles) in enumerate(CASES, start=1):
            output = tmpdir / f"case-{index}.html"
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "generate_report.py"),
                        str(ROOT / source),
                        "--requirement",
                        requirement,
                        "--output",
                        str(output),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                print(f"FAIL {source}: generator exited with {exc.returncode}", file=sys.stderr)
                if exc.stdout:
                    print(exc.stdout, file=sys.stderr)
                if exc.stderr:
                    print(exc.stderr, file=sys.stderr)
                return exc.returncode
            html = output.read_text(encoding="utf-8")
            missing = [needle for needle in needles if needle not in html]
            if missing:
                print(f"FAIL {source}: missing {missing}", file=sys.stderr)
                return 1
            print(f"OK   {source} -> {output.name}")
    print("Smoke check passed: all sample reports generated with specialized sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
