# Style Presets

Generated reports should look like finished business material, not an exported notebook. Pick a coherent design direction before generating the final report, then keep all sections inside that system.

## Why Style Diversity Matters

Directly asking an AI agent to "make a beautiful HTML report" produces the same aesthetic ~95% of the time:

> purple gradient + white cards + rounded corners + sans-serif = **every AI-generated report looks identical**

This skill ships **18 curated visual styles** with distinct design personalities. Each has its own color logic, typographic hierarchy, chart language, and information density — not just a color variable swap.

## Preview Policy

Default: infer one style and generate the final report.

Use 3 previews when:

- the report is for leadership or external-facing discussion
- the user has already complained about ugly AI outputs
- the data has no obvious visual direction
- the user explicitly wants options

Preview mix:

1. a safe executive style (`boardroom-light` or `command-center`)
2. a domain-matched style (e.g. `retail-pulse` for ecommerce)
3. a more distinctive wild card style from the Bold Variants below

Never render internal labels like "preview", "template", or "style option" inside the report page itself. Those names belong in the agent's message, not the artifact.

Run previews with:

```bash
mkdir -p .data-slide/previews
python3 scripts/generate_report.py data.xlsx --style command-center  --output .data-slide/previews/preview-a.html
python3 scripts/generate_report.py data.xlsx --style boardroom-light --output .data-slide/previews/preview-b.html
python3 scripts/generate_report.py data.xlsx --style retail-pulse     --output .data-slide/previews/preview-c.html
```

---

## 6 Base Visual Systems

### command-center

Best for: operations, project governance, demand pools, risk reviews, incident reports, executive control-room summaries.

- Background: deep navy / ink black.
- Accent: cyan, indigo, emerald, amber, red.
- Typography: high-contrast sans-serif; compact but readable.
- Components: KPI cards, glowing borders, lifecycle funnels, risk tags, category grids, drilldown blocks.
- Narrative tone: decisive, analytical, urgent where needed.
- Avoid for: reports intended for print-heavy board memos.

### boardroom-light

Best for: management summaries, finance, CRM, consulting-style reviews, cross-department alignment.

- Background: warm white or very light gray.
- Accent: navy, slate, green, amber.
- Typography: calm sans-serif, strong hierarchy, restrained numerals.
- Components: executive memo, KPI tiles, ranked tables, clean bar charts, assumption panels.
- Narrative tone: restrained, authoritative, readable in print.
- Avoid for: highly visual consumer/customer insight reports that need energy.

### retail-pulse

Best for: ecommerce orders, reviews, campaigns, customer feedback, store/platform comparisons.

- Background: soft light canvas with saturated accents.
- Accent: coral, teal, blue, violet, yellow.
- Typography: friendly but sharp.
- Components: sales cards, trend strips, product grids, opportunity/risk badges, review snippets.
- Narrative tone: commercial, energetic, action-oriented.
- Avoid for: strict compliance or audit reports.

### ops-ledger

Best for: ERP, inventory, procurement, warehouse, supply chain, process quality, exception management.

- Background: charcoal or paper-like ledger.
- Accent: green, amber, steel blue.
- Typography: tabular, precise, operations-friendly.
- Components: exception lists, stock risk badges, warehouse/category blocks, heat strips, movement summaries.
- Narrative tone: precise, operational, reliable.
- Avoid for: marketing or customer-facing decks.

### editorial-brief

Best for: survey results, research synthesis, customer interviews, offline collection forms, qualitative + quantitative summaries.

- Background: paper, off-white, or muted editorial canvas.
- Accent: ink, sage, muted red, warm yellow.
- Typography: editorial heading + readable body.
- Components: finding cards, quote/excerpt blocks, segment comparisons, recommendation memo.
- Narrative tone: thoughtful, human, insight-led.
- Avoid for: dense operational dashboards where speed scanning matters more than interpretation.

### data-studio

Best for: generic data exploration, mixed business tables, analytics-first reports, unknown schemas.

- Background: neutral dark or light studio.
- Accent: blue, teal, amber, violet.
- Typography: clean analytical hierarchy.
- Components: dataset profile, distribution cards, numeric summaries, missingness panels, suggested analyses.
- Narrative tone: exploratory, transparent, methodical.
- Avoid for: final executive reports when a stronger domain style is clear.

---

## Bold Variants (12 distinct design personalities)

> **Note**: These are *design variants*, not just color swaps. Each has a distinct typographic voice, chart language, and information density philosophy. They live in `references/bold-style-pack/` as lightweight preview descriptors that the agent reads before generating.

### 1. `ink-wash` — 水墨 / Ink Wash

- Philosophy: "Data as poetry" — inspired by Chinese ink wash painting and whitespace aesthetics.
- Background: warm parchment (#f5f0e8) with subtle texture.
- Accent: ink black, washed indigo, muted cinnabar.
- Typography: serif headings (Noto Serif SC) + clean sans body; large whitespace margins.
- Chart language: horizontal bar charts only; no gridlines; data-ink ratio maximized (Tufte-inspired).
- Best for: executive summaries where calm authority matters more than visual excitement.
- Unique trait: KPI numbers are set in an oversized serif with ultra-light weight — looks like a printed annual report.

### 2. `terminal-green` — 终端绿屏 / Terminal Green

- Philosophy: "Raw data, zero decoration" — inspired by green-phosphor terminal output and monospace code displays.
- Background: pure black (#000c00).
- Accent: green-cyan (#00e676), amber (#ffab00) for warnings.
- Typography: monospace only (Courier New / SimHei Mono); tabular numerals everywhere.
- Chart language: ASCII-style bar charts rendered with CSS (no canvas); dot-matrix style sparklines.
- Best for: DevOps reports, incident postmortems, technical operations reviews.
- Unique trait: the entire report looks like it was `cat`ed from a log file — but the numbers are real and the layout is deliberate.

### 3. `neon-noir` — 霓虹夜市 / Neon Noir

- Philosophy: "Data after dark" — inspired by neon signage, night markets, and cyberpunk visual language.
- Background: deep violet-black (#0a0014).
- Accent: neon pink (#ff2d7b), electric cyan (#00fff0), sodium vapor yellow (#ffeb3b).
- Typography: wide-track sans; all-caps headings; glowing text-shadow on KPIs.
- Chart language: outlined bars (no fills) with neon glow; dark data-ink; animated pulse on live numbers.
- Best for: consumer-facing ecommerce reports, campaign performance, social media ROI.
- Unique trait: hover effects trigger a "neon flicker" animation — CSS-only, no JS dependency.

### 4. `swiss-grid` — 瑞士网格 / Swiss Grid

- Philosophy: "Typography is the chart" — inspired by Swiss Style (International Typographic Style) and Josef Müller-Brockmann.
- Background: pure white (#ffffff); 1px rule-line grid in #e0e0e0.
- Accent: primary cyan (#0085ca), magenta (#d4007a) for highlights (CMYK-inspired).
- Typography: Grotesk-style sans; strict baseline grid; all numbers tabular + oldstyle figures.
- Chart language: only horizontal rules and type — data shown as numbered lists with precise leading; no decorative charts.
- Best for: consulting decks, strategy presentations, board-level summaries where text + numbers dominate.
- Unique trait: zero visual noise — the grid lines *are* the design. If you remove all data, you still see a beautiful Swiss poster.

### 5. `warm-earth` — 暖陶土 / Warm Earth

- Philosophy: "Human-scale data" — inspired by terracotta, adobe architecture, and warm material palettes.
- Background: warm sand (#faf3e0).
- Accent: terracotta (#c75b39), sage green (#7fa882), muted ochre (#c4a35a).
- Typography: humanist sans (rounded terminals); generous line height; ampersand ligatures in headings.
- Chart language: soft-edged bars (border-radius: 40%); earth-tone sequential palette; no pure primaries.
- Best for: HR reports, team retrospectives, culture surveys, anything people-centric.
- Unique trait: color palette is derived from real terracotta + sage samples — not a color wheel. Looks warm and unthreatening.

### 6. `data-ink` — 数据墨水 / Data Ink (Tufte-style)

- Philosophy: "Maximize the data-ink ratio" — directly inspired by Edward Tufte's *The Visual Display of Quantitative Information*.
- Background: near-white (#fcfcfb); no decorative elements.
- Accent: single hue (dark blue #1a1a2e); grayscale for secondary data.
- Typography: compact sans; small font sizes (11-13px) to fit more data per viewport.
- Chart language: scatterplots, small multiples, sparklines inline with text; no legends (labels placed directly on data).
- Best for: dense analytical reports, multi-dimensional data exploration, technical deep-dives.
- Unique trait: supports "small multiples" — 12 charts in a 4×3 grid, each with direct-labeling. Agent generates these when the dataset has 3+ dimensions.

### 7. `retro-wave` — 复古波浪 / Retro Wave

- Philosophy: "80s data" — inspired by 1980s computer graphics, arcade game palettes, and Memphis design.
- Background: dark navy (#1a1a2e) with radial gradient glow.
- Accent: hot pink (#ff6eb4), electric blue (#00d4ff), bright yellow (#ffe600).
- Typography: geometric sans (tight tracking); all-caps labels; 8px grid snap.
- Chart language: thick bars (80s arcade style); scanline overlay effect; "high score" KPI treatment.
- Best for: consumer product reports, Gen-Z targeted presentations, anything needing energy and nostalgia.
- Unique trait: KPI cards have a "CRT scanline" overlay — pure CSS, works even in static export.

### 8. `minimal-mono` — 极简单色 / Minimal Mono

- Philosophy: "One color, many weights" — a exercise in restraint using only one hue + black/white.
- Background: white (#ffffff).
- Accent: single color (user-chosen, default: slate #475569); 5 weights of the same color for hierarchy.
- Typography: one sans-serif family; hierarchy via weight (300/400/600/800) and size only — no color variation.
- Chart language: single-color bars with varying opacity; no gridlines; annotations in italic.
- Best for: minimalist executives who hate "colorful charts"; academic posters; print-optimized reports.
- Unique trait: even the most complex multi-series chart uses only one hue — distinction via opacity and pattern fill.

### 9. `corporate-navy` — 深蓝商务 / Corporate Navy

- Philosophy: "The C-suite standard" — the visual language of Fortune 500 board decks and annual reports.
- Background: very light gray (#f8f9fa); navy sidebar or header stripe.
- Accent: navy (#1e3a5f), silver (#9ca3af), success green (#065f46).
- Typography: conservative sans (Arial/Helvetica fallback); generous margins; numbered section tabs.
- Chart language: conservative stacked bars; 2-color max per chart; always show baseilne/target lines.
- Best for: board meetings, investor updates, annual report summaries, anything requiring "boring but correct".
- Unique trait: includes a "Appendix" section generator — agent auto-generates detailed data tables after the executive summary, mimicking real board deck structure.

### 10. `editorial-type` — 杂志排版 / Editorial Type

- Philosophy: "Data as editorial content" — inspired by magazine layout: large pull-quotes, sidebars, typographic emphasis.
- Background: warm white (#fefefe); 1-column + sidebar layout.
- Accent: brick red (#b8423a), olive green (#6b7f3a).
- Typography: mix of display serif (headings) and narrow sans (body + numbers); pull-quotes in italic.
- Chart language: charts treated as "figures" with captions and source lines; inline data callouts within body text.
- Best for: market research reports, survey result writeups, anything that reads like a magazine feature.
- Unique trait: agent writes 2-3 sentence "figure captions" for each chart — not just chart titles, but actual interpretive captions like a magazine would.

### 11. `high-density` — 高密度 / High Density

- Philosophy: "More data per square inch" — for power users who want to scan 20 KPIs in 10 seconds.
- Background: very light gray (#f0f2f5); border-separated cards (no border-radius).
- Accent: blue (#3b82f6), red for risk, green for good.
- Typography: compact; 11px body; tabular numerals; tight line height (1.3).
- Chart language: mini sparklines inline with KPI text; no dedicated chart section — insights are compact 2-line statements.
- Best for: operations dashboards, daily standup reports, power-user internal tools.
- Unique trait: the entire report fits in 2 scroll depths on a 1920×1080 screen — extremely high information density without feeling cramped.

### 12. `gradient-soft` — 柔和渐变 / Gradient Soft

- Philosophy: "Modern but not loud" — a contemporary gradient language that feels premium without being aggressive.
- Background: white (#ffffff); subtle gradient accents in header/hero only.
- Accent: soft gradient pairs (e.g. blue→cyan, coral→pink, green→teal); all gradients at 60% opacity.
- Typography: friendly rounded sans; gradient text effects on hero heading only (CSS background-clip).
- Chart language: gradient-filled bars (same hue, varying saturation); soft drop-shadows; no harsh borders.
- Best for: consumer brand reports, marketing performance, product launch retrospectives.
- Unique trait: the only style that uses CSS `background-clip: text` for gradient headings — looks premium and modern without the "AI purple gradient" cliché.

---

## Selection Rules

- Leadership + risk: `command-center` or `boardroom-light`.
- Ecommerce/customer: `retail-pulse` or `neon-noir` (bold).
- ERP/supply/warehouse/process: `ops-ledger` or `terminal-green` (bold).
- Survey/research/feedback: `editorial-brief` or `editorial-type` (bold).
- Finance / board: `boardroom-light` or `corporate-navy` (bold).
- Unknown/mixed table: `data-studio` for profiling, then switch once the domain is clearer.
- Minimalist / print: `minimal-mono` or `swiss-grid` (bold).
- Dense analytical: `data-ink` (bold).
- If the generated report looks generic, revise the visual system before revising small details.

## Design Quality Rules

- Use a real report composition: hero, KPI row, insight block, analytical modules, action section.
- Use charts or chart-like visuals with clear labels and business meaning.
- Keep the visual grammar consistent across cards, charts, tables, badges, and recommendations.
- Use color for meaning, not decoration only.
- Avoid purple-gradient-on-white defaults, random card piles, and unstyled dataframes.
- Keep generated HTML self-contained; do not depend on external chart libraries.
- **Anti-homogenization rule**: before delivering, ask: "Could this have been generated by a generic AI prompt?" If yes, increase the distinctiveness of the chosen style (stronger typography, more deliberate color, more intentional whitespace).

