# hsk-grader

Grade any Chinese text by HSK 3.0 vocabulary level, straight from your terminal.

## What it does

`hsk_grader.py` segments a Chinese sentence using a longest-match dictionary built
from the official public HSK 3.0 word list, and reports the HSK level (1–9) of
every word it recognises.

**Zero dependency** — pure Python 3.9+ standard library. No installs, no API, no
network. Your text never leaves your machine.

## Usage

```sh
# Grade a sentence passed as an argument
python3 hsk_grader.py 我爱我的家人。

# Read from a file
python3 hsk_grader.py --file notes.txt

# Pipe text in
echo "我爱我的家人。" | python3 hsk_grader.py

# Structured output
python3 hsk_grader.py --json "我爱我的家人。"

# Pinyin without tone marks
python3 hsk_grader.py --no-tones "我爱我的家人。"
```

### Output (default)

Each recognised word is printed as `word<TAB>pinyin<TAB>HSK n`, followed by a
summary of the counts per level:

```
我	yǐ	HSK 1
爱	ài	HSK 2
我	yǐ	HSK 1
...
X mots gradés · niveaux: 1:a 2:b ...
```

### `--json`

Prints a JSON array of `{"word": "...", "pinyin": "...", "level": n}` objects.

### Options

| Option        | Description                                                  |
|---------------|--------------------------------------------------------------|
| `text`        | Positional text to grade (optional; reads stdin if omitted)  |
| `--file PATH` | Read the Chinese text from a file instead                     |
| `--json`      | Emit a JSON array of matches                                  |
| `--no-tones`  | Strip tone diacritics from pinyin (NFD + remove combining marks) |

## How segmentation works

Words are matched by **longest match** against the bundled dictionary, scanning
the text left to right and preferring the longest known word starting at each
position (maximum 6 hanzi, the longest entry in the list). Non-hanzi characters
(punctuation, spaces) are skipped. Untracked characters contribute no output.

## Data & source

- Data file: [`data/hsk.tsv`](data/hsk.tsv) — `hanzi<TAB>pinyin<TAB>level`, loaded
  relative to the script (`__file__`).
- Source: the **public HSK 3.0 word list** (standard set, levels 1–9), the open
  vocabulary used by the Chinese Proficiency Test (Hànyǔ Shuǐpíng Kǎoshì).
- The tool ships with no Chinese input model, no ML and no web calls — the list
  is plain tab-separated data bundled in the repo.

## Requirements

- Python 3.9 or newer (only the standard library is used)
- No third-party packages

## Tests

```sh
cd hsk-grader
python3 -m unittest -v test_hsk_grader.py
```

## License

MIT — see the repository root [`LICENSE`](../LICENSE).
