---
name: excel-to-html-slides
description: Turn any spreadsheet or tabular business export into a polished single-file HTML report or slide deck. Use when the user provides Excel, CSV, TSV, CRM/ERP exports, ecommerce orders or reviews, DevOps demand lists, survey results, finance/operations tables, or other structured data and asks for an HTML report, dashboard, briefing page, management summary, analysis material, or presentation-style output.
---

# excel-to-html-slides

Create beautiful, complete HTML reports from raw tables. The user gives a spreadsheet and an analysis request; the agent profiles the table, chooses the right analytical frame, applies a strong visual design system, and delivers a self-contained `.html` file ready for management review or cross-team alignment.

This skill covers 9 enterprise domains out of the box: ecommerce, CRM, ERP, surveys, HR, support tickets, finance, DevOps, and generic data tables.

## Core Promise

- **Input**: `.xlsx`, `.xls`, `.csv`, or `.tsv` plus a natural-language analysis request.
- **Output**: a polished standalone HTML report with inline CSS/JS, no build step, no frontend framework, and no external chart library.
- **Default result**: executive summary, KPI cards, visual analysis sections, key insights, risks/opportunities, and action recommendations.
- **Primary objective**: reduce repeated style-tuning conversations. The first report should already look presentable.
- **Built-in analyzers**: DevOps/project demands, ecommerce orders, finance/performance, CRM pipeline, inventory/procurement, support tickets, HR/attendance/performance, and survey/review feedback. Use these before falling back to the generic table analyzer.
- **Visual promise**: six runnable visual systems plus 12 bold variants and an 18-template direction pack for stronger agent-led refinement.
- **Differentiation goal**: reduce multi-turn report tuning by providing deterministic metrics, domain modules, visual rails, and a quality checklist before the agent writes custom refinements.

## Why Not Just Ask The Agent To Generate HTML Directly?

Three things agents struggle with — and this skill solves:

1. **Anti-AI homogenization** — Agents tend to generate the same "purple gradient + white cards + rounded corners" aesthetic 95% of the time. This skill ships 18 curated visual styles with distinct design personalities, not just color swaps.
2. **Deterministic business metrics** — Agent understandings of "gross margin" or "return rate" drift between runs. This skill hardcodes enterprise-standard formulas in Python, so the same spreadsheet produces identical numbers across 1000 runs.
3. **Batch automation with zero tokens** — Running 50 weekly reports via agent API costs 50 token calls and may drift in formatting. This skill does it offline in Python, zero API needed.

## Non-Negotiables

- Do not produce a raw data dump as the main report.
- Do not generate generic "AI dashboard" visuals. Choose a deliberate visual system from `references/style-presets.md` or the bold-style pack.
- Do not omit important columns merely because they are inconvenient. Profile the table first and account for relevant dimensions.
- Do not invent conclusions unsupported by the table.
- Do not publish private business data unless explicitly approved.
- Do not stop at "profile complete" when the user asked for a report. Generate the HTML and check that domain-specific modules are present.

## Workflow

### 1. Understand The Report Job

Identify:

- **Audience**: management, department sync, customer/market review, operations review, project governance, sales review, etc.
- **Decision**: what the report should help decide or align on.
- **Density**: concise meeting report or detailed reading report.
- **Output language and tone**: infer from the user unless specified.

If the user only says "analyze this table", still proceed: profile the table, infer the domain, and generate a useful baseline report with assumptions listed.

### 2. Profile The Table

Run:

```bash
python3 scripts/profile_table.py <input-file> --output <profile.json>
```

Use the profile to inspect:

- sheets, row count, column count
- likely ID/title/status/date/category/owner/amount/rating fields
- missingness and duplicated-looking values
- categorical distributions
- numeric ranges and totals
- date ranges
- inferred domain signals

For multi-sheet workbooks, pick the sheet with the primary business records unless the user specifies a sheet.

### 3. Choose An Analysis Blueprint

Read `references/report-blueprints.md`.

Pick or combine blueprints based on the data signals:

- ecommerce orders/reviews
- CRM leads/opportunities
- ERP inventory/procurement
- DevOps or project demand lists
- survey/offline collection
- finance/operations trackers
- HR attendance/performance
- support tickets
- generic business table

The blueprint decides the report modules, not just the labels.

### 4. Choose The Visual System (Visual Preview Recommended)

Read `references/style-presets.md` for the 6 base visual systems.

**Recommended**: generate 3 visual previews so the user can *see* the difference instead of describing aesthetics in words:

```bash
mkdir -p .excel-to-html-slides/previews
python3 scripts/generate_report.py <input-file> --requirement "<...>" --style command-center --output .excel-to-html-slides/previews/preview-a.html
python3 scripts/generate_report.py <input-file> --requirement "<...>" --style boardroom-light --output .excel-to-html-slides/previews/preview-b.html
python3 scripts/generate_report.py <input-file> --requirement "<...>" --style retail-pulse   --output .excel-to-html-slides/previews/preview-c.html
```

Open the 3 previews in a browser and let the user pick. This "show, don't tell" approach eliminates ambiguous aesthetic discussions.

**Bold style pack** (optional): for high-stakes or taste-sensitive reports, also consider the 12 bold variants listed in `references/style-presets.md` section "Bold Variants". These are more experimental and personality-driven than the 6 base styles.

Default behavior:
- If the user names a style, use it.
- Otherwise infer a confident default from the data domain and audience.
- Do not ask abstract questions like "professional or modern?" unless necessary.

### 5. Generate The Report

Run:

```bash
python3 scripts/generate_report.py <input-file> \
  --requirement "<user analysis request>" \
  --style <selected-style> \
  --output <report.html>
```

The script auto-detects the data domain and generates a **complete, presentation-ready report** in one step. It covers 9 enterprise domains out of the box:

| Domain | Specialist | Key Analysis |
|--------|------------|--------------|
| `finance-expense` | Finance | KPIs, entity comparison, quarterly trends, loss/debt/cashflow risk |
| `crm-pipeline` | Sales | Pipeline amount, stage funnel, sales performance, source quality, zombie deals |
| `ecommerce-orders` | Operations | GMV, category/channel contribution, return analysis, trends |
| `erp-inventory` | Warehouse/Purchase | SKU/inventory/amount, stockout/overstock, in/out trends, anomalous items |
| `hr-attendance` | HR | Department comparison, attendance/performance distribution, anomaly detection, trends |
| `support-tickets` | Support | Ticket volume, resolution rate, handling time, satisfaction, SLA breaches, agent performance |
| `survey-feedback` | Marketing | Response volume, rating distribution, cohort comparison, NPS, question statistics, trends |
| `devops-demand-pool` | R&D PM | Demand lifecycle, category health, drill-down, owner workload |
| `generic-table` | Data Analyst | Cross-analysis, category distribution, numeric overview, outliers, missing detection |

Optional refinement: if the user has specific analytical questions not covered by the domain builder, the agent can post-process the HTML. But for standard enterprise reporting scenarios, the script output is the final deliverable.

### 6. Check Completeness

Read `references/quality-bar.md` before delivery.

Content checklist:
- Does the report answer the user's stated analysis request?
- Are the most important columns represented in a chart, table, KPI, filter, risk, or assumption?
- Are totals reconciled against source row counts?
- Is there at least one explicit decision/action section?
- Are assumptions and missing fields visible?

Visual checklist:
- No blank charts or placeholder text.
- No clipped headings, labels, or KPI values.
- The report is visually coherent on desktop and acceptable on mobile.
- Colors carry meaning consistently.
- It feels like a designed report, not a notebook export.

### 7. Deliver

Return the absolute path to the HTML report and summarize:

- inferred data domain
- selected visual style
- key report modules
- assumptions or missing fields
- any privacy note if the file contains sensitive records

## Script Quick Reference

Profile a spreadsheet:

```bash
python3 scripts/profile_table.py input.xlsx --sheet Sheet1 --output profile.json
```

Generate an HTML report:

```bash
python3 scripts/generate_report.py input.xlsx \
  --requirement "分析这份表格，生成管理层汇报材料，突出关键指标、风险和行动建议" \
  --style boardroom-light \
  --output report.html
```

## Resource Map

- `references/report-blueprints.md`: analysis modules, field signals, KPI logic, and recommendation patterns by table domain.
- `references/style-presets.md`: visual systems, bold variants, and preview-selection rules.
- `references/quality-bar.md`: final validation checklist.
- `references/html-report-template.md`: standalone HTML report architecture and section contract.
- `references/interaction-patterns.md`: dependency-free interaction and motion patterns for polished reports.
- `references/agent-installation.md`: cross-agent installation and publication guidance.
- `report-template-pack/selection-index.json`: compact index of report templates for fast visual/analytical direction selection.
- `report-template-pack/templates/*/preview.md`: lightweight preview cards for shortlisted templates.
- `scripts/profile_table.py`: deterministic table profiler.
- `scripts/generate_report.py`: deterministic baseline HTML report generator with 9 domain builders.

## Data Safety Rules

- Do not commit or publish customer, employee, order, financial, requirement, CRM, ERP, or review raw data by default.
- If creating examples for GitHub, use synthetic or sanitized data.
- Treat names, IDs, URLs, order numbers, customer notes, requirement text, review text, and financial values as sensitive unless the user says otherwise.

## Completion Criteria

The task is complete only when:

- The HTML exists and opens as a standalone file.
- The report answers the requested business question.
- Key totals match the source profile.
- Relevant columns are either analyzed or listed as assumptions/limitations.
- The styling is presentation-ready without repeated user tuning.
- Recommendations are specific enough for a manager or specialist to act on.

---

**excel-to-html-slides** — *Spreadsheets in, presentation-ready HTML out.*

