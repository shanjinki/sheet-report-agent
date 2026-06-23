---
name: excel-to-html-slides
description: Turn any spreadsheet or tabular business export into a polished single-file HTML briefing report. Use when the user provides Excel, CSV, TSV, CRM/ERP exports, ecommerce orders or reviews, DevOps demand lists, survey results, finance/operations tables, offline collection forms, or other structured data and asks for an HTML report, dashboard, briefing page, management summary, analysis material, or presentation-style output.
---

# excel-to-html-slides

Create beautiful, complete HTML briefing reports from raw tables. The user gives a spreadsheet and an analysis request; the agent profiles the table, chooses the right analytical frame, applies a strong visual report system, and delivers a self-contained `.html` file that can be used for management review or cross-team alignment.

The DevOps demand-pool report in `examples/` is only one concrete scenario. This skill is deliberately generic: ecommerce, CRM, ERP, surveys, operations, finance trackers, project lists, support tickets, offline collection sheets, and messy internal exports should all be handled through the same workflow.

## Core Promise

- Input: `.xlsx`, `.xls`, `.csv`, or `.tsv` plus a natural-language analysis requirement.
- Output: a polished standalone HTML report with inline CSS/JS, no build step, no frontend framework, and no external chart library.
- Default result: executive summary, KPI cards, visual analysis sections, charts or chart-like components, key insights, risks/opportunities, and action recommendations.
- Primary objective: reduce repeated style-tuning conversations. The first report should already look presentable.
- Built-in analyzers: DevOps/project demands, ecommerce orders, finance/performance, CRM pipeline, inventory/procurement, support tickets, HR/attendance/performance, and survey/review feedback. Use these before falling back to the generic table analyzer.
- Visual promise: six runnable visual systems plus an 18-template direction pack for stronger agent-led refinement. Do not claim that all 18 template directions are separate CLI style values.
- Differentiation goal: reduce multi-turn report tuning by providing deterministic metrics, domain modules, visual rails, and a quality checklist before the agent writes custom refinements.

## Non-Negotiables

- Do not produce a raw data dump as the main report.
- Do not make generic "AI dashboard" visuals. Choose a deliberate visual system from `references/style-presets.md`.
- Do not omit important columns merely because they are inconvenient. Profile the table first and account for relevant dimensions.
- Do not invent conclusions unsupported by the table.
- Do not publish private business data unless explicitly approved.
- Do not stop at "profile complete" when the user asked for a report. Generate the HTML and check that domain-specific modules are present.

## First-Run Dependency Check

If `pandas` or `openpyxl` is missing, tell the user to install dependencies from this repository:

```bash
pip install -r requirements.txt
```

After installation or before publishing, a quick self-check is:

```bash
python3 scripts/smoke_check.py
```

## Workflow

### 1. Understand The Report Job

Identify:

- Audience: management, department sync, customer/market review, operations review, project governance, sales review, etc.
- Decision: what the report should help decide or align on.
- Density: concise meeting report or detailed reading report.
- Output language and tone: infer from the user unless specified.

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

For multi-sheet workbooks, pick the sheet with the primary business records unless the user specifies a sheet. If multiple sheets matter, mention the assumption and use supporting sheets only when their schema is clear.

### 3. Choose An Analysis Blueprint

Read `references/report-blueprints.md`.

Pick or combine blueprints based on the data signals:

- ecommerce orders/reviews
- CRM leads/opportunities
- ERP inventory/procurement
- DevOps or project demand lists
- survey/offline collection
- finance/operations trackers
- generic business table

The blueprint decides the report modules, not just the labels. Example: an order export needs revenue/refund/product/channel analysis; a demand list needs lifecycle/backlog/owner risk; a survey needs distribution, segments, verbatims, and recommendations.

### 4. Choose The Visual System

Read `references/style-presets.md`.

Default behavior:

- If the user names a style, use it.
- Otherwise infer a strong style from the data and audience.
- Read `report-template-pack/selection-index.json` to shortlist report templates when the report needs a polished, domain-specific structure.
- Read only the shortlisted templates' `preview.md` files. Do not bulk-read every preview unless the user is browsing the gallery.
- For high-stakes or taste-sensitive reports, generate 3 style previews by running `scripts/generate_report.py` with three distinct `--style` values and saving them under `.excel-to-html-slides/previews/`.

Do not ask the user abstract questions like "professional or modern?" unless necessary. Show visual options or choose a confident default.

### 5. Generate The Report

Run:

```bash
python3 scripts/generate_report.py <input-file> \
  --requirement "<user analysis request>" \
  --output <report.html>
```

The script must produce a directly usable first report, not merely a data profile. Treat the generated HTML as the minimum acceptable deliverable: it should already contain executive KPIs, trend or lifecycle analysis, risk/exception items, and action recommendations. Then improve the report when needed:

- Rewrite insights so they answer the user's exact question.
- Add sections required by the blueprint if the source table has enough fields and the generated report still misses them.
- Reorder modules around the decision the report supports.
- Add safe excerpts only when useful and privacy-appropriate.
- Tighten chart labels and recommendation language.

If the selected blueprint has a built-in analyzer, verify that the report contains the domain modules available from the data. Do not deliver a generic profile page for finance, CRM, inventory/procurement, support tickets, HR, feedback/review, ecommerce order, or DevOps demand data.

### 6. Check Completeness

Read `references/quality-bar.md` before delivery.

Use this content checklist:

- Does the report answer the user's stated analysis request?
- Are the most important columns represented in a chart, table, KPI, filter, risk, or assumption?
- Are totals reconciled against source row counts?
- Is there at least one explicit decision/action section?
- Are assumptions and missing fields visible?

Use this visual checklist:

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

Generate multiple visual directions:

```bash
mkdir -p .excel-to-html-slides/previews
python3 scripts/generate_report.py input.xlsx --requirement "..." --style command-center --output .excel-to-html-slides/previews/style-a.html
python3 scripts/generate_report.py input.xlsx --requirement "..." --style boardroom-light --output .excel-to-html-slides/previews/style-b.html
python3 scripts/generate_report.py input.xlsx --requirement "..." --style retail-pulse --output .excel-to-html-slides/previews/style-c.html
```

## Resource Map

- `references/report-blueprints.md`: analysis modules, field signals, KPI logic, and recommendation patterns by table domain.
- `references/style-presets.md`: visual systems and preview-selection rules.
- `references/quality-bar.md`: final validation checklist.
- `references/html-report-template.md`: standalone HTML report architecture and section contract.
- `references/interaction-patterns.md`: dependency-free interaction and motion patterns for polished reports.
- `references/agent-installation.md`: cross-agent installation and publication guidance.
- `report-template-pack/selection-index.json`: compact index of report templates for fast visual/analytical direction selection.
- `report-template-pack/templates/*/preview.md`: lightweight preview cards for shortlisted templates.
- `scripts/profile_table.py`: deterministic table profiler.
- `scripts/generate_report.py`: deterministic baseline HTML report generator.
- `scripts/smoke_check.py`: no-pytest validation that all synthetic examples generate specialized report sections.

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
