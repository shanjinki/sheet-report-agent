# Agent Installation

This project is designed to be useful even when an agent does not support a formal plugin marketplace.

## Universal Use

Any coding agent with filesystem and shell access can use the repository by reading `SKILL.md` first, then loading the referenced files it needs.

Install Python dependencies once in the repository:

```bash
pip install -r requirements.txt
```

Verify the repository with:

```bash
python3 scripts/smoke_check.py
```

Recommended user prompt:

```text
Use $excel-to-html-slides from this repository to convert my Excel export into an HTML business briefing.
```

## Codex

- The root folder is a skill-compatible folder.
- The `plugins/excel-to-html-slides/.codex-plugin/plugin.json` wrapper exposes the same skill as a Codex plugin.
- The repo-local marketplace entry is `.agents/plugins/marketplace.json`.
- `install.sh codex` installs the skill under `${CODEX_HOME:-$HOME/.codex}/skills/excel-to-html-slides`.

## Claude Code

- The root `.claude-plugin/marketplace.json` points to `plugins/excel-to-html-slides`.
- The plugin folder includes `.claude-plugin/plugin.json`.
- The skill is under `plugins/excel-to-html-slides/skills/excel-to-html-slides`.
- `install.sh claude` installs the skill under `$HOME/.claude/skills/excel-to-html-slides`.

## Other Agent Runtimes

For tools such as QClaw, OpenClaw, Work Buddy, Kimi Code, Gemini CLI, or Qwen-style local agents, use one of these modes:

1. If the agent supports skill folders, copy the `excel-to-html-slides` skill folder into that agent's skills directory.
2. If the agent supports repository skills, point it at this GitHub URL and ask it to start from `SKILL.md`.
3. If the agent supports command tools only, run `scripts/profile_table.py` and `scripts/generate_report.py` directly, then ask the agent to refine the generated HTML.

Because these runtimes do not all share one public manifest standard, `SKILL.md` is the stable interface and plugin manifests are provided as adapters.
