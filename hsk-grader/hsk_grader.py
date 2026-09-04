#!/usr/bin/env python3
"""hsk_grader.py -- Grade a Chinese text by HSK vocabulary level.

Zero-dependency CLI (Python 3.9+, stdlib only).

Loads the HSK 3.0 word list shipped with the tool (hsk-grader/data/hsk.tsv,
resolved relative to this file) and segments the input by longest match
(word length capped at 6 hanzi), reporting the HSK level of each word found.
"""
import argparse
import json
import os
import sys
import unicodedata

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "hsk.tsv")
MAX_MATCH = 6  # longest word (in hanzi) supported by the word list


def _is_hanzi(ch):
    return "\u4e00" <= ch <= "\u9fff"


def load_words(path=DATA_PATH):
    """Return {hanzi: (pinyin, level_int)} from the TSV data file."""
    words = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            hanzi, pinyin, level = parts[0], parts[1], parts[2]
            try:
                words[hanzi] = (pinyin, int(level))
            except ValueError:
                continue
    return words


def strip_tones(pinyin):
    """Remove tone diacritics from pinyin (NFD + drop combining marks)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", pinyin)
        if not unicodedata.combining(c)
    )


def segment(text, words):
    """Longest-match segmentation; yields (word, pinyin, level) in text order."""
    n = len(text)
    i = 0
    while i < n:
        if not _is_hanzi(text[i]):
            i += 1
            continue
        matched = None
        end = min(i + MAX_MATCH, n)
        # find the longest hanzi-only prefix ending <= end that is a known word
        found = None
        for j in range(end, i, -1):
            span = text[i:j]
            if all(_is_hanzi(c) for c in span) and span in words:
                found = span
                break
        if found is not None:
            pinyin, level = words[found]
            yield found, pinyin, level
            i += len(found)
        else:
            i += 1


def build_parser():
    p = argparse.ArgumentParser(
        description="Grade a Chinese text by HSK 3.0 vocabulary level."
    )
    p.add_argument("text", nargs="?", default=None,
                   help="Chinese text to grade (optional; reads stdin if omitted)")
    p.add_argument("--file", metavar="PATH", default=None,
                   help="Read Chinese text from a file")
    p.add_argument("--json", action="store_true",
                   help="Output JSON list of {word, pinyin, level}")
    p.add_argument("--no-tones", action="store_true",
                   help="Strip tone marks from pinyin in the output")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()
    if not text:
        text = ""

    words = load_words()

    results = []          # (word, pinyin, level) in order
    level_counts = {}     # level -> number of matched tokens
    for word, pinyin, level in segment(text, words):
        if args.no_tones:
            pinyin = strip_tones(pinyin)
        results.append({"word": word, "pinyin": pinyin, "level": level})
        level_counts[level] = level_counts.get(level, 0) + 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False))
        return 0

    for r in results:
        print("{}\t{}\tHSK {}".format(r["word"], r["pinyin"], r["level"]))
    levels = " ".join(
        "{}:{}".format(lv, level_counts[lv]) for lv in sorted(level_counts)
    )
    print("{} mots gradés · niveaux: {}".format(len(results), levels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
