# Preprocessing Social Media Posts

Our data consists of roughly 5,800 social media posts about the Apple TV series
*Severance*. Each social media post should be normalized using the following rules.

| Rule                         | What it does                                                            |
| ---------------------------- | ----------------------------------------------------------------------- |
| Remove URLs                  | Strip web addresses (`http://`, `https://`, `www.`).                    |
| Remove hidden characters     | Strip invisible Unicode formatting chars and non-breaking spaces.       |
| Standardize apostrophes      | Convert Unicode apostrophe variants (e.g. `’`) to ASCII `'`.            |
| Expand contractions          | Rewrite shortened forms to full words (`can't` → `cannot`).             |
| Remove mentions              | Strip social-media usernames prefixed with `@`.                         |
| Split hashtags               | Separate camelCase inside hashtags (`#TextAnalysis` → `Text Analysis`). |
| Convert to lowercase         | Lowercase all text.                                                     |
| Remove punctuation & symbols | Strip punctuation and special characters.                               |
| Remove numbers               | Strip digit sequences.                                                  |
| Normalize elongation         | Collapse 3+ repeated chars (`loooove` → `love`).                        |
| Convert emojis to text       | Replace emojis with text descriptions (`🔥` → `[fire]`).                                  |
| Remove single characters     | Strip isolated letters left after cleanup.                              |
| Normalize whitespace         | Collapse repeated spaces and trim edges.                                |

## Structure

### Data

- `data/raw/comments.csv.enc`: encrypted raw data in git.
- `data/raw/comments.csv`: the decrypted raw data. ignored by git.
- `data/normalized/comments.csv`: normalized data (output). ignored by git.
- `data/test/examples.csv`: normalization input and output pairs for testing.

### Code

- `normalize.py`: normalize raw data, output to `data/normalized/comments.csv`.
- `review_server.py`: a web app for review raw/normalized message pairs.

## Workflow

- `uv run pytest` — run the test suite against `data/test/examples.csv`
- `uv run python -m normalize` — normalize `data/raw/comments.csv` → `data/normalized/comments.csv`

## Review Server

Use the review server to review raw/normalized message pairs. The server runs on
http://localhost:5001

- `uv run python review_server.py`

Pairs are paginated 100 per page. The top-bar **Regenerate** button re-runs
normalization in place, re-importing `normalize.py` each time — so you can edit
the rules and click Regenerate to see the effect, without restarting the server.
A broken edit shows an error banner instead of stopping the server.
