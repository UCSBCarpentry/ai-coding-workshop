# Install JS dependencies for the accessibility checks (first-time setup).
install:
    npm install

# Render the full static site to _site/.
render:
    quarto render

# Render the site, then run axe-core accessibility checks against it.
# Pass page paths to override the default set, e.g. `just a11y index.html`.
a11y *pages: render
    npm run a11y -- {{pages}}

# Run accessibility checks against the existing _site/ without re-rendering.
a11y-only *pages:
    npm run a11y -- {{pages}}
