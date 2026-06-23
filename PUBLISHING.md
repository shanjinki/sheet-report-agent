# Publishing Handoff

Use this file when QClaw, WorkBuddy, or another agent publishes the local repository.

## Local Repository

```text
/Users/ninebot/Documents/Skill 制作/excel-to-html-slides
```

## Suggested GitHub Repository

```text
shanjinki/excel-to-html-slides
```

Suggested description:

```text
Turn spreadsheets into polished HTML business briefings with cross-agent skills.
```

Suggested topics:

```text
excel, csv, html-report, business-analysis, slides, agents, codex, claude-code, qclaw, workbuddy
```

## Publishing Prompt

```text
Publish the local repository at /Users/ninebot/Documents/Skill 制作/excel-to-html-slides to GitHub as shanjinki/excel-to-html-slides.
Do not add ignored files. Do not add outputs/ or any real spreadsheet from the desktop.
Keep the repository public, description: "Turn spreadsheets into polished HTML business briefings with cross-agent skills."
After pushing, verify README.md renders and examples/sample_demand_report.html is present.
```

## Preflight Checks

Run these before pushing:

```bash
git status --short --ignored
python3 scripts/generate_report.py examples/sample_demands.csv \
  --requirement "分析需求池整体健康度、积压风险和管理建议" \
  --output /tmp/sheet-report-smoke.html
test -s /tmp/sheet-report-smoke.html
python3 scripts/smoke_check.py
```

Confirm ignored files include:

```text
outputs/
*.xlsx
*.xls
*.xlsm
```

## Files That Should Be Published

- `README.md`
- `SKILL.md`
- `scripts/`
- `tests/`
- `references/`
- `report-template-pack/`
- `assets/`
- `examples/sample_demands.csv`
- `examples/sample_demand_report.html`
- `plugins/excel-to-html-slides/`
- `.agents/plugins/marketplace.json`
- `.claude-plugin/marketplace.json`
- `requirements.txt`
- `LICENSE`

## Files That Must Not Be Published Without Explicit Approval

- Any spreadsheet copied from a company system.
- Any generated report based on private business data.
- `/Users/ninebot/Desktop/需求_清洗结果_v2.xlsx`
- `/Users/ninebot/Desktop/demand_report_v17.html`
- `outputs/`

## Post-Publish Verification

1. Open the GitHub repository page.
2. Confirm README title and quick-start instructions render correctly.
3. Confirm `examples/sample_demand_report.html` is visible in the repo.
4. Confirm `outputs/` is absent.
5. Clone the public repo into a temp directory and run the quick-start command.
