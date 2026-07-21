"""Review server for raw/normalized comment pairs.

A minimal read-only viewer: raw messages joined to their normalized output,
paginated 100 per page, with a top-bar button that re-runs the normalization
pipeline. The raw CSV is never written to.

Each Regenerate imports normalize.py fresh, so you can edit the rules and see
the effect without restarting the server. A broken edit shows up as an error
banner rather than taking the server down.

    uv run python review_server.py   # -> http://localhost:5001
"""

from __future__ import annotations

import contextlib
import csv
import importlib
import io
import sys
import traceback
from datetime import datetime
from pathlib import Path
from types import ModuleType

from flask import Flask, redirect, render_template, request, url_for

RAW = Path("data/raw/comments.csv")
NORMALIZED = Path("data/normalized/comments.csv")
PER_PAGE = 100

app = Flask(__name__, template_folder="review_templates")

# Outcome of the most recent Regenerate, rendered as a banner. None until the
# button is first clicked.
_status: dict[str, str | bool | None] | None = None


def _load_normalize() -> ModuleType:
    """Import normalize.py fresh so edits take effect without a restart.

    Imported lazily (not at module scope) so a broken normalize.py can never
    stop the server from starting.
    """
    module = sys.modules.get("normalize")
    if module is None:
        return importlib.import_module("normalize")
    return importlib.reload(module)


def _status_entry(ok: bool, message: str, detail: str | None = None) -> dict:
    return {
        "ok": ok,
        "message": message,
        "detail": detail,
        "when": datetime.now().strftime("%H:%M:%S"),
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_pairs() -> list[dict[str, str]]:
    """Raw rows (in file order) joined to their normalized text by id."""
    normalized = {row["id"]: row["text"] for row in _read_csv(NORMALIZED)}
    return [
        {
            "id": row["id"],
            "raw": row["text"],
            "normalized": normalized.get(row["id"]),
        }
        for row in _read_csv(RAW)
    ]


@app.route("/")
def index():
    pairs = load_pairs()
    total = len(pairs)
    page_count = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    page = request.args.get("page", 1, type=int)
    page = max(1, min(page, page_count))

    start = (page - 1) * PER_PAGE
    page_pairs = pairs[start : start + PER_PAGE]

    return render_template(
        "index.html",
        pairs=page_pairs,
        page=page,
        page_count=page_count,
        total=total,
        start=start,
        status=_status,
    )


@app.route("/regenerate", methods=["POST"])
def regenerate():
    """Re-run the normalization pipeline, then return to the same page.

    normalize.py is re-imported first, so whatever is on disk right now is what
    runs. Anything it raises becomes a banner instead of a dead server.
    """
    global _status
    try:
        normalize = _load_normalize()
        # redirect_stdout swaps the process-wide sys.stdout; the dev server is
        # threaded, so a concurrent request could lose its output. Fine for a
        # single-reviewer tool.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            normalize.main()
    except SystemExit as exc:  # normalize.main() exits on missing raw input
        _status = _status_entry(False, str(exc.code))
    except Exception:
        # A syntax error is caught at compile time and leaves the loaded module
        # untouched. An error part-way through executing normalize.py leaves it
        # partially updated — the next successful Regenerate replaces it fully.
        _status = _status_entry(False, "normalization failed", traceback.format_exc())
    else:
        _status = _status_entry(True, out.getvalue().strip())

    page = request.form.get("page", 1, type=int)
    return redirect(url_for("index", page=page))


if __name__ == "__main__":
    # Exclude normalize.py from the reloader: once it is in sys.modules the
    # reloader would restart the server on every edit, which is both the restart
    # we are trying to avoid and fatal if the edit does not compile.
    app.run(
        debug=True,
        port=5001,
        exclude_patterns=[str(Path(__file__).with_name("normalize.py"))],
    )
