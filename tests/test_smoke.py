import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_sample_report(tmp_path):
    output = tmp_path / "sample.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_report.py"),
            str(ROOT / "examples" / "sample_demands.csv"),
            "--requirement",
            "分析需求池整体健康度、积压风险和管理建议",
            "--output",
            str(output),
        ],
        check=True,
    )
    html = output.read_text(encoding="utf-8")
    assert "需求池全景分析报告" in html
    assert "全局概览" in html
    assert "风险清单" in html
    assert "window.__REPORT__" in html


def test_generate_finance_report_has_business_analysis(tmp_path):
    output = tmp_path / "finance.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_report.py"),
            str(ROOT / "examples" / "sample_finance.csv"),
            "--requirement",
            "分析这份多家公司多季度的财务数据，生成管理层汇报材料，突出关键指标、风险和行动建议",
            "--style",
            "boardroom-light",
            "--output",
            str(output),
        ],
        check=True,
    )
    html = output.read_text(encoding="utf-8")
    assert "财务经营绩效分析报告" in html
    assert "季度趋势" in html
    assert "主体表现与风险排行" in html
    assert "异常与风险明细" in html
    assert "高风险" in html
    assert "资产负债率" in html


def test_generate_generic_report_uses_business_category_not_date(tmp_path):
    source = tmp_path / "generic.csv"
    source.write_text(
        "\n".join(
            [
                "日期,区域,销售额,处理时长,负责人",
                "2026-01-01,华东,1200,4,A",
                "2026-01-15,华南,980,5,B",
                "2026-02-02,华东,1600,4,A",
                "2026-02-20,华北,7000,12,C",
                "2026-03-01,华南,1300,6,B",
                "2026-03-15,华东,1800,5,A",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "generic.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_report.py"),
            str(source),
            "--requirement",
            "分析销售和异常，生成管理层汇报",
            "--output",
            str(output),
        ],
        check=True,
    )
    html = output.read_text(encoding="utf-8")
    assert "通用业务表格分析报告" in html
    assert "趋势变化" in html
    assert "结构贡献" in html
    assert "异常高值" in html
    assert "核心分类字段：区域" in html


def test_generate_domain_reports_have_specialized_sections(tmp_path):
    cases = [
        (
            "sample_crm.csv",
            "分析销售 pipeline 健康度、跟进风险和行动建议",
            ["CRM 商机管道分析报告", "销售漏斗阶段分布", "跟进风险明细"],
        ),
        (
            "sample_inventory.csv",
            "分析库存缺货、呆滞库存、供应商集中度和补货建议",
            ["库存与采购风险分析报告", "供应商集中度", "缺货与呆滞风险明细"],
        ),
        (
            "sample_support.csv",
            "分析客服工单 SLA、问题类型、处理人负载和服务风险",
            ["客服工单 SLA 分析报告", "问题类型分布", "SLA 与满意度风险明细"],
        ),
        (
            "sample_hr.csv",
            "分析部门绩效、考勤异常、高工时负载和管理建议",
            ["HR 人员运营分析报告", "部门表现/覆盖", "人员异常明细"],
        ),
        (
            "sample_feedback.csv",
            "分析问卷满意度、负面反馈主题和改进建议",
            ["用户反馈与评论洞察报告", "评分分布", "代表性反馈摘录"],
        ),
    ]
    for filename, requirement, needles in cases:
        output = tmp_path / f"{filename}.html"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "generate_report.py"),
                str(ROOT / "examples" / filename),
                "--requirement",
                requirement,
                "--output",
                str(output),
            ],
            check=True,
        )
        html = output.read_text(encoding="utf-8")
        for needle in needles:
            assert needle in html
