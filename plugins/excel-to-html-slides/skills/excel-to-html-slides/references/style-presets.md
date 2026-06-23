# Style Presets

Generated reports should look like finished business material, not an exported notebook. Pick a coherent design direction before generating the final report, then keep all sections inside that system.

## Preview Policy

Default: infer one style and generate the final report.

Use 3 previews when:

- the report is for leadership or external-facing discussion
- the user has already complained about ugly AI outputs
- the data has no obvious visual direction
- the user explicitly wants options

Preview mix:

1. a safe executive style
2. a domain-matched style
3. a more distinctive wildcard style

Never render internal labels like "preview", "template", or "style option" inside the report page itself. Those names belong in the agent's message, not the artifact.

## command-center

Best for: operations, project governance, demand pools, risk reviews, incident reports, executive control-room summaries.

- Background: deep navy / ink black.
- Accent: cyan, indigo, emerald, amber, red.
- Typography: high-contrast sans-serif; compact but readable.
- Components: KPI cards, glowing borders, lifecycle funnels, risk tags, category grids, drilldown blocks.
- Narrative tone: decisive, analytical, urgent where needed.
- Avoid for: reports intended for print-heavy board memos.

## boardroom-light

Best for: management summaries, finance, CRM, consulting-style reviews, cross-department alignment.

- Background: warm white or very light gray.
- Accent: navy, slate, green, amber.
- Typography: calm sans-serif, strong hierarchy, restrained numerals.
- Components: executive memo, KPI tiles, ranked tables, clean bar charts, assumption panels.
- Narrative tone: restrained, authoritative, readable in print.
- Avoid for: highly visual consumer/customer insight reports that need energy.

## retail-pulse

Best for: ecommerce orders, reviews, campaigns, customer feedback, store/platform comparisons.

- Background: soft light canvas with saturated accents.
- Accent: coral, teal, blue, violet, yellow.
- Typography: friendly but sharp.
- Components: sales cards, trend strips, product grids, opportunity/risk badges, review snippets.
- Narrative tone: commercial, energetic, action-oriented.
- Avoid for: strict compliance or audit reports.

## ops-ledger

Best for: ERP, inventory, procurement, warehouse, supply chain, process quality, exception management.

- Background: charcoal or paper-like ledger.
- Accent: green, amber, steel blue.
- Typography: tabular, precise, operations-friendly.
- Components: exception lists, stock risk badges, warehouse/category blocks, heat strips, movement summaries.
- Narrative tone: precise, operational, reliable.
- Avoid for: marketing or customer-facing decks.

## editorial-brief

Best for: survey results, research synthesis, customer interviews, offline collection forms, qualitative + quantitative summaries.

- Background: paper, off-white, or muted editorial canvas.
- Accent: ink, sage, muted red, warm yellow.
- Typography: editorial heading + readable body.
- Components: finding cards, quote/excerpt blocks, segment comparisons, recommendation memo.
- Narrative tone: thoughtful, human, insight-led.
- Avoid for: dense operational dashboards where speed scanning matters more than interpretation.

## data-studio

Best for: generic data exploration, mixed business tables, analytics-first reports, unknown schemas.

- Background: neutral dark or light studio.
- Accent: blue, teal, amber, violet.
- Typography: clean analytical hierarchy.
- Components: dataset profile, distribution cards, numeric summaries, missingness panels, suggested analyses.
- Narrative tone: exploratory, transparent, methodical.
- Avoid for: final executive reports when a stronger domain style is clear.

## Selection Rules

- Leadership + risk: `command-center` or `boardroom-light`.
- Ecommerce/customer: `retail-pulse`.
- ERP/supply/warehouse/process: `ops-ledger`.
- Survey/research/feedback: `editorial-brief`.
- Unknown/mixed table: `data-studio` for profiling, then switch once the domain is clearer.
- If the generated report looks generic, revise the visual system before revising small details.

## Design Quality Rules

- Use a real report composition: hero, KPI row, insight block, analytical modules, action section.
- Use charts or chart-like visuals with clear labels and business meaning.
- Keep the visual grammar consistent across cards, charts, tables, badges, and recommendations.
- Use color for meaning, not decoration only.
- Avoid purple-gradient-on-white defaults, random card piles, and unstyled dataframes.
- Keep generated HTML self-contained; do not depend on external chart libraries.
