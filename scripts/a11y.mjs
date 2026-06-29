// Accessibility checker for the Quarto site.
//
// Runs axe-core (WCAG 2.1 A + AA) against the rendered pages in `_site/` using the
// system Chrome via puppeteer-core. Writes a full JSON report per page to
// `a11y-report/` and prints a console summary. Exits non-zero only when a
// `serious` or `critical` violation is found.
//
// Page selection (first match wins):
//   1. CLI args:        node scripts/a11y.mjs index.html lessons/01_intro.html
//   2. a11y.config.json at repo root:  { "pages": ["index.html", "setup.html", ...] }
//   3. Default: index.html, setup.html, and one page per lessons/*.qmd source file.
//
// Assumes the site has already been rendered (`quarto render`). The `just a11y`
// recipe renders first; `just a11y-only` skips the render.

import { createServer } from 'node:http';
import { readFile, readdir, mkdir, writeFile, access } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const siteDir = path.join(repoRoot, '_site');
const reportDir = path.join(repoRoot, 'a11y-report');
const axeSource = require.resolve('axe-core/axe.min.js');

const CHROME_PATH = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
const FAILING_IMPACTS = new Set(['serious', 'critical']);

const CONTENT_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/json; charset=utf-8',
};

async function fileExists(p) {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

async function resolvePages() {
  const cliArgs = process.argv.slice(2);
  if (cliArgs.length > 0) return cliArgs;

  const configPath = path.join(repoRoot, 'a11y.config.json');
  if (await fileExists(configPath)) {
    const config = JSON.parse(await readFile(configPath, 'utf8'));
    if (Array.isArray(config.pages) && config.pages.length > 0) return config.pages;
  }

  // Default: index, setup, and every lesson derived from source .qmd files.
  const pages = ['index.html', 'setup.html'];
  const lessonsDir = path.join(repoRoot, 'lessons');
  if (await fileExists(lessonsDir)) {
    const entries = await readdir(lessonsDir);
    for (const entry of entries.sort()) {
      if (entry.endsWith('.qmd')) {
        pages.push(`lessons/${entry.replace(/\.qmd$/, '.html')}`);
      }
    }
  }
  return pages;
}

// Minimal static file server for the rendered _site directory.
function startServer() {
  const server = createServer(async (req, res) => {
    try {
      let urlPath = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      if (urlPath.endsWith('/')) urlPath += 'index.html';
      const filePath = path.join(siteDir, path.normalize(urlPath));
      if (!filePath.startsWith(siteDir)) {
        res.writeHead(403).end('Forbidden');
        return;
      }
      const body = await readFile(filePath);
      const type = CONTENT_TYPES[path.extname(filePath)] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': type }).end(body);
    } catch {
      res.writeHead(404).end('Not found');
    }
  });
  return new Promise((resolve, reject) => {
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ server, port });
    });
  });
}

function summarize(violations) {
  const counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
  for (const v of violations) {
    const impact = v.impact || 'minor';
    if (impact in counts) counts[impact] += 1;
  }
  return counts;
}

async function main() {
  if (!(await fileExists(siteDir))) {
    console.error(`No rendered site found at ${siteDir}. Run \`quarto render\` first (or \`just a11y\`).`);
    process.exit(2);
  }

  const pages = await resolvePages();
  await mkdir(reportDir, { recursive: true });

  const { server, port } = await startServer();
  const baseUrl = `http://127.0.0.1:${port}`;
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  let hasFailingViolations = false;
  const rows = [];

  try {
    for (const pagePath of pages) {
      const page = await browser.newPage();
      const url = `${baseUrl}/${pagePath.replace(/^\//, '')}`;
      let counts = { critical: 0, serious: 0, moderate: 0, minor: 0 };
      let violations = [];
      try {
        const response = await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
        if (!response || !response.ok()) {
          console.error(`  ! ${pagePath}: HTTP ${response ? response.status() : 'no response'} (skipped)`);
          rows.push({ pagePath, error: true });
          continue;
        }
        await page.addScriptTag({ path: axeSource });
        const result = await page.evaluate((tags) => {
          // eslint-disable-next-line no-undef
          return axe.run(document, { runOnly: { type: 'tag', values: tags } });
        }, WCAG_TAGS);
        violations = result.violations;
        counts = summarize(violations);

        const slug = pagePath.replace(/[\\/]/g, '__').replace(/\.html$/, '');
        await writeFile(
          path.join(reportDir, `${slug}.json`),
          JSON.stringify(result, null, 2),
        );
      } finally {
        await page.close();
      }

      if (counts.serious > 0 || counts.critical > 0) hasFailingViolations = true;
      rows.push({ pagePath, counts });

      // Per-page details.
      if (violations.length > 0) {
        console.log(`\n${pagePath}`);
        for (const v of violations) {
          const mark = FAILING_IMPACTS.has(v.impact) ? 'FAIL' : 'warn';
          console.log(`  [${mark}] (${v.impact}) ${v.id}: ${v.help} — ${v.nodes.length} node(s)`);
          console.log(`         ${v.helpUrl}`);
        }
      } else {
        console.log(`\n${pagePath}\n  No violations.`);
      }
    }
  } finally {
    await browser.close();
    server.close();
  }

  // Summary table.
  console.log('\n=== Accessibility summary (WCAG 2.1 A + AA) ===');
  console.log('page                                     crit  seri  mod  min');
  for (const row of rows) {
    if (row.error) {
      console.log(`${row.pagePath.padEnd(40)}  (load error)`);
      continue;
    }
    const { critical, serious, moderate, minor } = row.counts;
    console.log(
      `${row.pagePath.padEnd(40)} ${String(critical).padStart(4)}  ${String(serious).padStart(4)}  ${String(moderate).padStart(3)}  ${String(minor).padStart(3)}`,
    );
  }
  console.log(`\nReports written to ${path.relative(repoRoot, reportDir)}/`);

  if (hasFailingViolations) {
    console.error('\nFAIL: serious or critical accessibility violations found.');
    process.exit(1);
  }
  console.log('\nPASS: no serious or critical violations.');
}

main().catch((err) => {
  console.error(err);
  process.exit(2);
});
