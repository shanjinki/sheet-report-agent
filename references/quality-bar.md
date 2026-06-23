# Quality Bar

Use this checklist before delivering an HTML report.

## Data Reconciliation

- Row count in the report matches the profiled source table.
- Excluded rows are clearly defined, for example discarded/cancelled records.
- KPI formulas are explainable from visible source fields.
- Percentages use the right denominator and show one decimal place when helpful.
- Empty, unknown, and missing values are not silently treated as good data.

## Narrative

- The first screen says what changed, what matters, and what decision is needed.
- Insights are grounded in a metric, comparison, concentration, or risk threshold.
- Recommendations name concrete actions: coordinate review resources, prune backlog, follow up stale leads, replenish stock, fix missing categories, etc.
- Avoid vague conclusions such as "data needs attention" unless paired with the exact field or segment.

## Visual Quality

- No blank sections or placeholder text.
- No chart overlaps, clipped KPI labels, or illegible colors.
- The report works at common laptop widths and on mobile with horizontal density reduced where needed.
- Cards, tables, and charts have consistent spacing.
- Risk colors are used consistently: green good, amber warning, red risk.

## Differentiation Check

- The report contains at least one domain-specific module, not just generic field summaries.
- The report includes a trend, funnel, structure, exception, or ranking view whenever the source fields make one possible.
- Recommendations are tied to specific segments, records, owners, risks, or missing fields.
- The generated page would still be useful if the user stopped the conversation after the first output.

## Privacy

- Do not publish raw private spreadsheets or generated reports containing real names, customer data, internal URLs, order IDs, requirement text, or financial details without explicit approval.
- For GitHub examples, create synthetic data.

## Delivery

- Give the absolute path to the final HTML.
- State the inferred domain and selected style.
- List any assumptions or missing fields that affected analysis quality.
