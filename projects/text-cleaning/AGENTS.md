Script to preprocess/normalize social media posts for analysis.

## Data

- `data/raw/comments.csv.enc`: encrypted raw data (AES-256-CBC) in git. DO NOT
  MODIFY.
- `data/raw/comments.csv`: the decrypted raw data. DO NOT COMMIT OR MODIFY.
- `data/normalized/comments.csv`: normalized data (output). DO NOT COMMIT.
- `data/test/examples.csv`: normalization input and output pairs for testing.

## Tools & Workflow

- first, check if`data/raw/comments.csv` exists and decrypt
  `data/raw/comments.csv.enc` if necessary.
- Use uv to manage dependencies and run project scripts
- Use red/green TDD

## Decrypting data

To decrypt raw data, first ask the user for the password, then:

```
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in data/raw/comments.csv.enc \
  -out data/raw/comments.csv
```

## Run tests

- `uv run pytest` — run the test suite against `data/test/examples.csv`

## Run normalization

- `uv run python -m normalize` — normalize `data/raw/comments.csv` → `data/normalized/comments.csv`

## Review server

To start the data review server, run it in a detached tmux session (it serves on
port 5001):

```
tmux new-session -d -s review-server 'uv run python review_server.py'
```

To check on the review server or stop it:

```
tmux capture-pane -p -t review-server   # view output
tmux kill-session -t review-server      # stop the server
```

The **Regenerate** button re-imports `normalize.py` before running it, so edits to
the normalization rules take effect on the next click — do not restart the server
after editing `normalize.py`. If the edit does not compile or raises, the page shows
an error banner and the server keeps running; fix the code and click Regenerate
again.
