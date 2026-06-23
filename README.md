# excel-to-html-slides

> Drop an Excel or CSV file in. Get a presentation-ready HTML business briefing out.
>
> 把企业里导出的 Excel/CSV 表格，变成可以直接拿去汇报的单文件 HTML 汇报材料。

[Demand demo](examples/sample_demand_report.html) · [Finance demo](examples/sample_finance_report.html) · [CRM demo](examples/sample_crm_report.html) · [Inventory demo](examples/sample_inventory_report.html) · [Support demo](examples/sample_support_report.html) · [HR demo](examples/sample_hr_report.html) · [Feedback demo](examples/sample_feedback_report.html)

---

## 中文快速理解

这个项目解决的是企业里很常见的一件事：专员从系统里导出 Excel 后，不能直接拿给管理层或跨部门对齐，还要花很多时间做图表、写结论、调样式。

`excel-to-html-slides` 让 Agent 装上一个稳定的“表格汇报能力包”：用户给原始表格和分析要求，Agent 先用脚本生成一份有业务口径、有视觉系统、有风险建议的 HTML 汇报材料，再按需要精修。

它的差异化不是“提示词写得好”，而是把重复工作沉淀成了可复用资产：领域识别、确定性指标计算、常见业务蓝图、视觉规范、质量检查和示例验证。

---

## The Pain

Enterprise teams already have the data. It is sitting in exports from CRM, ERP, ecommerce platforms, DevOps systems, ticket systems, HR tools, surveys, or offline collection sheets.

The real bottleneck is what happens next:

```text
Export Excel
Clean field names
Figure out what matters
Build charts
Rewrite insights
Make it look presentable
Move it into a meeting deck
Repeat after every manager comment
```

That is why specialists often spend half a day turning a raw table into something management can read.

`excel-to-html-slides` is an AI-agent skill and deterministic Python toolkit that turns that workflow into a few minutes: profile the table, infer the business domain, calculate the core metrics, choose a visual system, and generate a polished standalone HTML report.

---

## Why Not Just Ask An Agent?

You can. For one-off analysis, a strong agent can write HTML from scratch.

This project exists because direct agent output is unreliable in exactly the places enterprise reports care about.

| Direct agent generation | `excel-to-html-slides` |
|---|---|
| Every report tends to become the same generic AI dashboard | Six runnable visual systems plus an 18-template direction pack |
| Business metrics can drift between conversations | Deterministic Python analyzers calculate repeatable KPIs |
| The agent spends tokens rediscovering common CRM/ERP/ecommerce logic | Built-in blueprints encode common exported-table patterns |
| Style tuning takes many back-and-forth prompts | First output is designed to clear a practical presentation bar |
| Batch or weekly reporting is expensive and inconsistent | Runs locally, offline, and produces self-contained HTML |

The skill is not trying to replace the agent. It gives the agent a better starting point: fixed business logic, reusable report structure, and visual rails that prevent the usual ugly first draft.

---

## Differentiation In One Minute

This is not just a prompt library. The repository ships four reusable assets that reduce multi-turn report tuning:

1. **Deterministic analyzers**: Python code calculates domain KPIs and risk signals for common enterprise exports, so numbers do not drift between conversations.
2. **Domain blueprints**: CRM, ERP, finance, ecommerce, support, HR, survey, DevOps, and generic-table report modules are pre-defined instead of rediscovered from scratch.
3. **Visual rails**: six runnable design systems and 18 template directions keep the first report away from the generic AI dashboard look.
4. **Quality contract**: the skill tells the agent to check row counts, missing fields, assumptions, risk/action cards, and visual completeness before delivery.

For users, that means fewer prompts like "make it prettier", "add risk analysis", "why is this just a data profile", or "where is the trend chart".

---

## What It Generates

The output is a single `.html` file with inline CSS and JavaScript. No build step, no hosted service, no external chart library.

Each report is designed around:

- executive KPIs
- business-domain analysis sections
- trend, funnel, structure, or exception views where the data supports them
- grounded insights
- risk and action cards
- visible assumptions and missing-field notes
- responsive layout for desktop review and quick mobile reading

This is closer to a management briefing page than a raw dashboard export. It can be opened directly in a browser, shared as a file, or embedded into a broader reporting workflow.

---

## Supported Business Domains

| Domain | Typical export | Built-in analysis |
|---|---|---|
| `ecommerce-orders` | Orders, refunds, product sales | GMV, category/channel contribution, refund risk, trends |
| `finance-expense` | Revenue, expense, budget, reconciliation | revenue/profit, budget variance, entity comparison, loss/debt risk |
| `crm-pipeline` | Leads, opportunities, follow-up records | pipeline amount, stage funnel, owner ranking, stale deals |
| `erp-inventory` | Inventory, procurement, warehouse records | stockout, overstock, supplier concentration, movement trend |
| `support-tickets` | Tickets, complaints, service cases | volume, resolution rate, SLA risk, agent workload |
| `hr-attendance` | Attendance, performance, staff operations | department comparison, abnormal attendance, score distribution |
| `survey-feedback` | Surveys, ratings, comments, offline forms | rating distribution, segment comparison, representative feedback |
| `devops-demand-pool` | Requirement pools, project/task exports | lifecycle funnel, backlog health, owner load, delivery risk |
| `generic-table` | Unknown or mixed business tables | trend, structure, numeric summary, outliers, missingness |

---

## Visual System

The runtime generator currently supports six production-ready styles:

| Style | Best for | Feel |
|---|---|---|
| `command-center` | risk, project governance, DevOps, operations | dark, dense, control-room |
| `boardroom-light` | finance, CRM, management reviews | calm, executive, print-friendly |
| `retail-pulse` | ecommerce, product, customer reports | energetic, commercial, trend-forward |
| `ops-ledger` | ERP, procurement, inventory | precise, operational, exception-led |
| `editorial-brief` | surveys, research, qualitative feedback | readable, human, insight-led |
| `data-studio` | generic or exploratory tables | analytical, neutral, transparent |

The `report-template-pack/` adds 18 template directions for agents to choose from when a report needs stronger narrative or visual framing. These are template briefs and selection metadata, not 18 separate runtime CLI styles yet.

---

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify the local repo:

```bash
python3 scripts/smoke_check.py
```

Generate a report directly:

```bash
python3 scripts/generate_report.py your_data.xlsx \
  --requirement "分析这份表格，生成管理层汇报材料，突出关键指标、风险和行动建议" \
  --style boardroom-light \
  --output report.html
```

Profile a table first:

```bash
python3 scripts/profile_table.py your_data.xlsx --output profile.json
```

Open `report.html` in any browser.

---

## Install As An Agent Skill

Clone the repository, install Python dependencies, then install the skill into the agent runtime:

```bash
pip install -r requirements.txt

# WorkBuddy
./install.sh workbuddy

# Codex
./install.sh codex

# Claude Code
./install.sh claude

# All supported local agents
./install.sh all
```

Then ask your agent:

```text
Use $excel-to-html-slides to analyze /path/to/data.xlsx and generate a management-ready HTML report.
```

The skill is intentionally agent-agnostic. It works best when the host agent can read local files and run Python scripts.

If an agent only supports repository skills, point it at this repo and tell it to start from `SKILL.md`. If an agent only supports shell tools, run `scripts/generate_report.py` directly and let the agent refine the generated HTML if needed.

---

## Examples

All examples use synthetic data.

- [DevOps demand pool report](examples/sample_demand_report.html)
- [Finance performance report](examples/sample_finance_report.html)
- [CRM pipeline report](examples/sample_crm_report.html)
- [Inventory and procurement report](examples/sample_inventory_report.html)
- [Support ticket report](examples/sample_support_report.html)
- [HR operations report](examples/sample_hr_report.html)
- [Survey and feedback report](examples/sample_feedback_report.html)

You can regenerate all sample reports with:

```bash
python3 scripts/smoke_check.py
```

---

## Project Structure

```text
├── SKILL.md                       # cross-agent workflow instructions
├── agents/openai.yaml             # skill display metadata
├── install.sh                     # local installer for WorkBuddy, Codex, Claude
├── scripts/
│   ├── profile_table.py           # table profiler and domain inference
│   ├── generate_report.py         # deterministic HTML report generator
│   └── smoke_check.py             # no-pytest verification for all examples
├── references/
│   ├── report-blueprints.md       # analysis modules by business domain
│   ├── style-presets.md           # visual system guidance
│   ├── quality-bar.md             # delivery checklist
│   └── html-report-template.md    # HTML architecture contract
├── report-template-pack/
│   ├── selection-index.json       # 18 template directions
│   └── templates/                 # lightweight preview cards
├── examples/                      # synthetic source data and generated reports
└── tests/                         # smoke tests for key report domains
```

---

## Current Boundaries

- The generator handles one primary sheet/table at a time. Multi-sheet workbooks are profiled, but cross-sheet relationship modeling is not yet a full semantic engine.
- The six CLI styles are fully runnable. The 18 template directions guide agents and future expansion.
- The output is HTML briefing material, not an editable PowerPoint file.
- The project avoids uploading data. Reports are generated locally from local files.

---

## License

MIT
