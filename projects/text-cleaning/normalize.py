"""Normalize social-media posts for analysis.

Applies the 13 normalization rules from AGENTS.md, in a fixed order (several
rules depend on earlier ones). Run as a script to normalize the raw comments:

    uv run python -m normalize
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import contractions
import emoji

RAW = Path("data/raw/comments.csv")
NORMALIZED = Path("data/normalized/comments.csv")

# --- rule 1: remove hidden characters -------------------------------------
# Invisible formatting / joiner chars and emoji skin-tone modifiers are dropped
# outright; Unicode spaces (NBSP etc.) collapse to a normal space.
_HIDDEN = re.compile(
    "["
    "​-‏"  # zero-width space/joiner (ZWJ)/marks
    "‪-‮"  # bidi embedding/override
    "⁠"          # word joiner
    "﻿"          # BOM / zero-width no-break space
    "­"          # soft hyphen
    "︀-️"  # variation selectors (e.g. VS16)
    "\U0001F3FB-\U0001F3FF"  # emoji skin-tone modifiers
    "]"
)
_UNICODE_SPACE = re.compile("[   -   　]")

# --- rule 2: standardize apostrophes --------------------------------------
_APOSTROPHES = re.compile("[’‘ʼ＇′]")

# --- rule 3: remove URLs ---------------------------------------------------
_URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# --- rule 4: remove mentions ----------------------------------------------
_MENTION = re.compile(r"@\w+")

# --- rule 5: split hashtags ------------------------------------------------
_HASHTAG = re.compile(r"#(\w+)")
# insert a space at camelCase and letter<->digit boundaries
_CAMEL = re.compile(
    r"(?<=[a-z0-9])(?=[A-Z])"          # camelCase: fooBar
    r"|(?<=[A-Z])(?=[A-Z][a-z])"       # acronym then word: TVShow
    r"|(?<=[a-zA-Z])(?=[0-9])"         # letter -> digit
    r"|(?<=[0-9])(?=[a-zA-Z])"         # digit -> letter
)

# --- rule 9: remove numbers ------------------------------------------------
_NUMBER = re.compile(r"\d+")

# --- rule 10: remove punctuation & symbols --------------------------------
# keep ASCII letters and whitespace only
_NON_TEXT = re.compile(r"[^a-zA-Z\s]")

# --- rule 12: normalize elongation ----------------------------------------
_ELONG = re.compile(r"(\w)\1{2,}")

# --- rule 13: normalize whitespace ----------------------------------------
_WS = re.compile(r"\s+")


def remove_hidden_chars(text: str) -> str:
    text = _HIDDEN.sub("", text)
    return _UNICODE_SPACE.sub(" ", text)


def standardize_apostrophes(text: str) -> str:
    return _APOSTROPHES.sub("'", text)


def remove_urls(text: str) -> str:
    return _URL.sub("", text)


def remove_mentions(text: str) -> str:
    return _MENTION.sub("", text)


def split_hashtags(text: str) -> str:
    return _HASHTAG.sub(lambda m: _CAMEL.sub(" ", m.group(1)), text)


def expand_contractions(text: str) -> str:
    return contractions.fix(text)


def emojis_to_text(text: str) -> str:
    text = emoji.demojize(text, delimiters=(" ", " "))
    return text.replace("_", " ")


def to_lowercase(text: str) -> str:
    return text.lower()


def remove_numbers(text: str) -> str:
    return _NUMBER.sub("", text)


def remove_punctuation(text: str) -> str:
    return _NON_TEXT.sub("", text)


def normalize_elongation(text: str) -> str:
    return _ELONG.sub(r"\1", text)


def remove_single_chars(text: str) -> str:
    return " ".join(tok for tok in text.split() if len(tok) > 1)


def normalize_whitespace(text: str) -> str:
    return _WS.sub(" ", text).strip()


# Pipeline order matters — see AGENTS.md and the module docstring.
_PIPELINE = (
    remove_hidden_chars,
    standardize_apostrophes,
    remove_urls,
    remove_mentions,
    split_hashtags,
    expand_contractions,
    emojis_to_text,
    to_lowercase,
    remove_numbers,
    remove_punctuation,
    normalize_elongation,
    remove_single_chars,
    normalize_whitespace,
)


def normalize(text: str) -> str:
    for step in _PIPELINE:
        text = step(text)
    return text


def main() -> None:
    if not RAW.exists():
        sys.exit(f"raw input not found: {RAW}")
    NORMALIZED.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW, encoding="utf-8", newline="") as fin, open(
        NORMALIZED, "w", encoding="utf-8", newline=""
    ) as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout)
        writer.writerow(["id", "text"])
        n = 0
        for row in reader:
            writer.writerow([row["id"], normalize(row["text"])])
            n += 1
    print(f"normalized {n} rows -> {NORMALIZED}")


if __name__ == "__main__":
    main()
