# HTML Report Template

Use this reference when refining or rebuilding generated HTML reports. It is an original report-page architecture for spreadsheet analysis output, not a slide template.

## Page Architecture

Every report should be a standalone HTML file with inline CSS and JavaScript.

Recommended structure:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Report Title</title>
  <style>
    /* theme variables, layout, modules, responsive rules */
  </style>
</head>
<body class="theme-name">
  <main class="page-shell">
    <header class="hero">...</header>
    <section class="kpi-section">...</section>
    <section class="insight-section">...</section>
    <section class="analysis-section">...</section>
    <section class="risk-section">...</section>
    <section class="action-section">...</section>
    <section class="assumption-section">...</section>
  </main>
  <script>
    window.__REPORT__ = {...};
    /* render modules from structured data */
  </script>
</body>
</html>
```

## Required Sections

- **Hero**: report title, data source, generated time, inferred domain, report purpose.
- **KPI Row**: 4-6 metrics that answer the user's main question.
- **Insights**: short, data-grounded findings in business language.
- **Analysis Modules**: charts or chart-like components selected from the blueprint.
- **Risks / Opportunities**: ranked list with severity or priority.
- **Actions**: concrete next steps, owners, decisions, or follow-up checks.
- **Assumptions**: field mapping, filters, exclusions, missing data.

## Layout Rules

- Use a scrollable report page, not fixed slides.
- Start with conclusions before details.
- Keep KPI cards stable in height and alignment.
- Use responsive grids: 5 columns on wide desktop, 2 columns on tablet, 1 column on mobile.
- Keep tables and long labels readable with wrapping or truncation plus context.
- Never let visual modules depend on external chart libraries unless the user permits it.

## Data Contract

Prefer embedding a single structured JSON object:

```js
window.__REPORT__ = {
  domain: "ecommerce-orders",
  title: "...",
  kpis: [],
  insights: [],
  modules: [],
  risks: [],
  actions: [],
  assumptions: []
};
```

Render UI from this object so a future agent can safely edit data, copy modules, or add export features.

## Accessibility And Usability

- Use semantic headings in order.
- Keep contrast high enough for projector and laptop screens.
- Do not communicate risk by color alone; include text labels.
- Avoid hover-only access to critical data.
- Make the report usable when opened directly from `file://`.

## Code Quality

- Keep all CSS/JS in the file unless the user wants a web app project.
- Use clear section comments for large CSS/JS blocks.
- Avoid minified generated code when the user may need to edit it.
- Keep generated data separate from rendering functions.
