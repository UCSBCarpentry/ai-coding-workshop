#!/usr/bin/env node
// Post-render accessibility fix for Quarto collapsible callouts.
//
// Quarto emits collapsible callout headers as a <div> carrying
// `data-bs-toggle="collapse"` and `aria-expanded`, but without a role that
// permits `aria-expanded`. axe-core flags this as a critical
// `aria-allowed-attr` violation. Adding `role="button"` makes the ARIA state
// valid and correctly conveys that the header is an interactive toggle.
//
// Runs as a Quarto `post-render` script: it patches the HTML files listed in
// QUARTO_PROJECT_OUTPUT_FILES (falling back to a recursive scan of _site/).

import { readFile, writeFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const siteDir = path.join(repoRoot, '_site');

// Match a callout-header toggle div that lacks a role attribute.
const HEADER_RE = /<div class="callout-header([^"]*)"((?:(?!role=)[^>])*?data-bs-toggle="collapse"(?:(?!role=)[^>])*?)>/g;

async function listHtmlFiles() {
  const fromQuarto = process.env.QUARTO_PROJECT_OUTPUT_FILES;
  if (fromQuarto) {
    return fromQuarto
      .split('\n')
      .map((f) => f.trim())
      .filter((f) => f.endsWith('.html'))
      .map((f) => path.resolve(repoRoot, f));
  }
  // Fallback: walk _site for .html files.
  const files = [];
  async function walk(dir) {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) await walk(full);
      else if (entry.name.endsWith('.html')) files.push(full);
    }
  }
  await walk(siteDir);
  return files;
}

let patchedFiles = 0;
let patchedHeaders = 0;

for (const file of await listHtmlFiles()) {
  let html;
  try {
    html = await readFile(file, 'utf8');
  } catch {
    continue;
  }
  let count = 0;
  const next = html.replace(HEADER_RE, (match, cls, attrs) => {
    count += 1;
    return `<div class="callout-header${cls}"${attrs} role="button">`;
  });
  if (count > 0) {
    await writeFile(file, next);
    patchedFiles += 1;
    patchedHeaders += count;
  }
}

if (patchedHeaders > 0) {
  console.log(
    `a11y: added role="button" to ${patchedHeaders} collapsible callout header(s) across ${patchedFiles} file(s).`,
  );
}
