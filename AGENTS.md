This is a quarto-based research website for a workshop on AI-assisted coding.
The site is deployed to github pages using an action.

- to preview the site: `quarto preview --no-browser --host 0.0.0.0 --port 4444`
- to run accessibility checks (axe-core, WCAG 2.1 A + AA): `just a11y` (renders the
  site, then checks `index`, `setup`, and all lesson pages). Use `just a11y-only` to
  skip the re-render, or pass page paths to override the default set
  (e.g. `just a11y index.html`). Requires a one-time `just install`. Per-page JSON
  reports land in `a11y-report/`; the command exits non-zero on serious/critical
  violations.
