# Install JS dependencies, for a11y testing and mermaid diagrams
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

# Generate PNG and SVG images from Mermaid (.mmd) files in the diagrams directory
diagrams:
	@for file in diagrams/*.mmd; do \
		echo "Generating $file -> ${file%.mmd}.png & ${file%.mmd}.svg..."; \
		./node_modules/.bin/mmdc -p diagrams/puppeteer-config.json -i "$file" -o "${file%.mmd}.png"; \
		./node_modules/.bin/mmdc -p diagrams/puppeteer-config.json -i "$file" -o "${file%.mmd}.svg"; \
	done
