# Interaction Patterns

Use these original interaction and motion patterns to make spreadsheet reports feel polished without becoming distracting.

## Principles

- Motion should clarify hierarchy, not decorate randomly.
- Interactions should reveal detail, compare groups, or help scanning.
- Critical conclusions must be visible without hover.
- Keep all interactions local and dependency-free.

## Recommended Patterns

### KPI Count-In

Use for high-level numeric cards. Count from 0 to the final value on load only when it does not delay readability.

Best for: total orders, GMV, backlog, inventory value, ticket count.

### Staggered Section Reveal

Use a subtle fade/translate reveal for cards as the page loads or enters viewport.

Best for: KPI rows, insight cards, risk cards.

Avoid: long delays or animations on every small table row.

### Detail-On-Demand

Use expandable cards or inline detail panels for drilldown records.

Best for: top products, backlog items, stale opportunities, exception records.

Critical summary values should remain visible before expansion.

### Tooltip For Chart-Like Components

Use lightweight custom tooltips for bars, funnels, heat strips, and scatter-like layouts.

Tooltip content should include:

- label
- value
- share or rate
- short explanation

### Severity Badges

Use text + color badges for risk levels:

- Green: healthy / completed / low risk
- Amber: watch / medium risk / needs follow-up
- Red: high risk / overdue / blocked

Do not use unexplained decorative colors.

### Ranked Bars

Use horizontal bars for top categories, products, channels, owners, suppliers, or issue types.

Always show the value next to the bar. Sort intentionally: biggest first for contribution, worst first for risk.

### Funnel

Use for staged processes:

- CRM pipeline
- demand lifecycle
- support ticket lifecycle
- approval workflow

Keep stage labels short and include stage counts/rates.

### Exception Register

Use a compact table/card hybrid for records requiring action.

Fields should include:

- item/title/id
- owner or department
- status/severity
- why it matters
- recommended action

## Motion Defaults

Use small timings:

- reveal duration: 300-500ms
- stagger gap: 50-100ms
- hover transition: 160-240ms

Respect reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Anti-Patterns

- Do not hide the main conclusion behind a hover tooltip.
- Do not animate every number, row, and chart at once.
- Do not use canvas effects that make text harder to read.
- Do not add filters or tabs unless they help the user's stated analysis.
