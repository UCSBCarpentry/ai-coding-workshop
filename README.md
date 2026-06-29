# ai-coding-workshop
Workshop on AI-Assisted Coding (in development)

## Development

Tools needed to build and test the site:

- **Quarto** — renders the site from `.qmd` sources to `_site/`.
- **just** — command runner for the build/test recipes (see `justfile`).
- **Node / npm** — runtime for the accessibility checks.
- **Google Chrome** — headless browser used to run the checks.
- **axe-core + puppeteer-core** — npm dev dependencies that run the accessibility checks (`just install`).
