import csv
from pathlib import Path

import pytest

import normalize as N

EXAMPLES = Path(__file__).parent.parent / "data" / "test" / "examples.csv"


def load_examples():
    with open(EXAMPLES, encoding="utf-8") as f:
        return [(r["rule"], r["input"], r["expected"]) for r in csv.DictReader(f)]


@pytest.mark.parametrize(
    "rule,text,expected",
    load_examples(),
    ids=[f"{i}:{r[0]}" for i, r in enumerate(load_examples())],
)
def test_examples(rule, text, expected):
    assert N.normalize(text) == expected


# --- targeted unit tests for individual rule functions ---

def test_remove_urls():
    assert N.remove_urls("a https://t.co/x b") == "a  b"
    assert N.remove_urls("go www.apple.com now") == "go  now"


def test_remove_hidden_chars():
    assert N.remove_hidden_chars("a b") == "a b"          # NBSP -> space
    assert N.remove_hidden_chars("a​b") == "ab"           # ZWSP dropped
    assert N.remove_hidden_chars("\U0001F44D\U0001F3FB") == "\U0001F44D"  # skin tone dropped


def test_standardize_apostrophes():
    assert N.standardize_apostrophes("it’s") == "it's"


def test_expand_contractions():
    assert N.expand_contractions("can't") == "cannot"
    assert N.expand_contractions("they don't") == "they do not"


def test_remove_mentions():
    assert N.remove_mentions("hi @bob there") == "hi  there"


def test_split_hashtags():
    assert N.split_hashtags("#TextAnalysis") == "Text Analysis"
    assert N.split_hashtags("#Season2") == "Season 2"


def test_remove_numbers():
    assert N.remove_numbers("season 2") == "season "


def test_normalize_elongation():
    assert N.normalize_elongation("loooove") == "love"
    assert N.normalize_elongation("good") == "good"  # doubles preserved


def test_remove_single_chars():
    assert N.remove_single_chars("it was a show") == "it was show"


def test_normalize_whitespace():
    assert N.normalize_whitespace("  a   b  ") == "a b"
