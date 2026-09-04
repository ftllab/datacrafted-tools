# md-pages

A minimal, honest **markdown → static HTML** site generator in one file.

**Zero dependency** — pure Python 3.9+ standard library. No bundler, no npm, no
template engine. Point it at a folder of `.md` files and it emits a clean,
self-contained HTML site (inline CSS, dark theme) with an auto-generated index.

## Usage

```sh
python3 md_pages.py build SRC OUT
```

- `SRC` — a folder containing `.md` source files
- `OUT` — destination folder for the generated HTML site

`OUT` is rebuilt from scratch on each run. Every source file `NAME.md` becomes
`NAME.html`; `index.html` lists all pages as cards (title, date, source path),
sorted by `date` descending. Every page links back to `index.html`.

### Example

```sh
python3 md_pages.py build ./content ./site
```

```text
content/
  hello.md
  guide.md
site/
  hello.html
  guide.html
  index.html
```

## Supported Markdown (the honest list)

A deliberately small subset — everything else is rendered as plain text.

- **Frontmatter** (optional, YAML-ish): `title:` and `date:` on their own lines,
  delimited by `---` at the start of the file.
- **Headings** `#` … `######`
- **Unordered lists** (`-`, `*`, `+`) and **ordered lists** (`1.`, `2.`, …)
- **Fenced code blocks** ``` ``` ``` ``` (content escaped)
- **Blockquotes** `>` (multi-line joined with `<br>`)
- **Horizontal rules** `---` and `***`
- **Paragraphs** (consecutive text lines joined into one paragraph)
- **Inline**: `**bold**`, `*italic*`, `` `code` ``, `[text](url)`,
  `![alt](url)` — code spans are protected with placeholders before other
  inline rules run, so markup inside code stays literal.

### Documented limits

- **Raw HTML is always escaped** and shown as text — no passthrough.
- No nested lists, no task lists, no tables, no footnotes, no fenced-code
  language highlighting (fence language labels are ignored).
- No headings-with-`#` mid-line, no reference-style links or autolinks.
- Frontmatter only supports flat `key: value` pairs.
- Only `.md` files at the top level of `SRC` are processed (no recursion).

## Output

The site uses a clean dark template with inline CSS and a card-based index:

- dark `#0f1115` background, system font stack, blue links
- `<pre>`/`<code>` blocks styled distinctly
- index cards show title, date and source filename

## Tests

```sh
cd md-pages
python3 -m unittest -v test_md_pages.py
```

The test builds a sample site from a markdown file (frontmatter + heading +
list + link + code block) and verifies the generated `index.html` links to
`sample.html` and that `sample.html` contains `<h1>`, `<a href` and `<code>`.
It also checks that raw HTML in source is escaped.

## License

MIT — see the repository root [`LICENSE`](../LICENSE).
