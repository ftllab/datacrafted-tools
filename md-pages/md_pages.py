#!/usr/bin/env python3
"""md_pages.py -- Minimal zero-dependency markdown -> static HTML generator.

Builds a folder of .md files into an HTML site with a clean dark template,
an auto-generated index, and per-page back-to-index links.

Usage:
    python3 md_pages.py build SRC OUT

Only a small, honest subset of Markdown is supported (see README for the exact
limits). No external dependencies -- pure Python 3.9+ standard library.
"""
import html
import os
import re
import shutil
import sys

# --- metadata / markdown helpers ---------------------------------------------

TITLE_META = "title"
DATE_META = "date"

CSS = """\
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e6e6e6;font:16px/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:40px 24px 80px}
a{color:#5ea3ff;text-decoration:none}
a:hover{text-decoration:underline}
.back{display:inline-block;margin-bottom:24px;font-size:14px;color:#9aa0a6}
h1{font-size:2rem;margin:.2em 0 .4em}
h2{font-size:1.5rem;border-bottom:1px solid #2a2e37;padding-bottom:.3em}
h3{font-size:1.25rem}
.meta{color:#9aa0a6;font-size:.9rem;margin-bottom:2em}
hr{border:0;border-top:1px solid #2a2e37;margin:2em 0}
code{background:#1c2028;padding:.15em .4em;border-radius:4px;font-size:.9em}
pre{background:#1c2028;padding:14px 16px;border-radius:8px;overflow:auto;border:1px solid #2a2e37}
pre code{background:none;padding:0}
blockquote{margin:.5em 0;padding:.2em 1.2em;border-left:4px solid #5ea3ff;color:#c9cdd4;background:#161a21;border-radius:0 6px 6px 0}
ul,ol{padding-left:1.6em}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid #2a2e37;padding:.4em .7em;text-align:left}
th{background:#1c2028}
img{max-width:100%}"""

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<p class="back"><a href="index.html">&larr; Back to index</a></p>
<h1>{title}</h1>
{meta_html}
<hr>
{content}
</div>
</body>
</html>
"""

INDEX_CSS = CSS


def parse_frontmatter(text):
    """Extract leading YAML-ish frontmatter. Returns (meta_dict, rest)."""
    meta = {}
    if text.startswith("---"):
        lines = text.split("\n")
        # find closing fence
        try:
            end = lines[1:].index("---") + 1
        except ValueError:
            return meta, text  # unterminated: treat whole thing as body
        head = lines[1:end]
        for line in head:
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip().lower()] = value.strip()
        return meta, "\n".join(lines[end + 1:])
    return meta, text


def parse_inline(text):
    """Apply inline markdown. Code spans are protected first via placeholders."""
    # 1. protect inline code spans
    code_spans = []
    def stash_code(m):
        code_spans.append(html.escape(m.group(1)))
        return "\x00CODE{}\x00".format(len(code_spans) - 1)
    text = re.sub(r"`([^`]+)`", stash_code, text)

    # 2. links and images (text already html-escaped)
    def repl_image(m):
        return '<img src="{}" alt="{}">'.format(
            html.escape(m.group(2), quote=True), html.escape(m.group(1), quote=True))
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", repl_image, text)

    def repl_link(m):
        return '<a href="{}">{}</a>'.format(
            html.escape(m.group(2), quote=True), m.group(1))
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", repl_link, text)

    # 3. bold / italic
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    # 4. restore code spans
    def restore(m):
        return "<code>{}</code>".format(code_spans[int(m.group(1))])
    text = re.sub(r"\x00CODE(\d+)\x00", restore, text)
    return text


def render_blocks(blocks):
    """Convert block-level structures into HTML. Returns a list of html chunks."""
    out = []
    i = 0
    while i < len(blocks):
        line = blocks[i]
        stripped = line.strip()

        if stripped == "":                      # blank -> paragraph gap
            i += 1
            continue

        if stripped.startswith("```"):          # fenced code block
            buf = []
            i += 1
            while i < len(blocks) and not blocks[i].strip().startswith("```"):
                buf.append(blocks[i])
                i += 1
            i += 1  # skip closing fence
            code = html.escape("\n".join(buf))
            out.append("<pre><code>{}</code></pre>".format(code))
            continue

        # headings
        hm = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if hm:
            level = len(hm.group(1))
            out.append("<h{0}>{1}</h{0}>".format(level, parse_inline(hm.group(2))))
            i += 1
            continue

        if stripped == "---" or stripped == "***":  # horizontal rule
            out.append("<hr>")
            i += 1
            continue

        # quote block
        if stripped.startswith(">"):
            buf = []
            while i < len(blocks) and blocks[i].strip().startswith(">"):
                buf.append(blocks[i].strip()[1:].strip())
                i += 1
            content = "<br>".join(parse_inline(b) for b in buf)
            out.append("<blockquote>{}</blockquote>".format(content))
            continue

        # ordered list
        om = re.match(r"^\s*\d+[.)]\s+(.*)$", stripped)
        if om:
            buf = []
            while i < len(blocks):
                m = re.match(r"^\s*\d+[.)]\s+(.*)$", blocks[i].strip())
                if m:
                    buf.append(parse_inline(m.group(1)))
                    i += 1
                else:
                    break
            out.append("<ol>" + "".join("<li>{}</li>".format(x) for x in buf) + "</ol>")
            continue

        # unordered list (-, *, +)
        um = re.match(r"^\s*[-*+]\s+(.*)$", stripped)
        if um:
            buf = []
            while i < len(blocks):
                m = re.match(r"^\s*[-*+]\s+(.*)$", blocks[i].strip())
                if m:
                    buf.append(parse_inline(m.group(1)))
                    i += 1
                else:
                    break
            out.append("<ul>" + "".join("<li>{}</li>".format(x) for x in buf) + "</ul>")
            continue

        # plain paragraph (collect consecutive non-empty, non-special lines)
        para = [parse_inline(blocks[i].strip())]
        i += 1
        while i < len(blocks):
            s = blocks[i].strip()
            if s == "" or s.startswith(("```", "#", ">", "-", "*", "+", "---", "***")) \
               or re.match(r"^\s*\d+[.)]\s+", s):
                break
            para.append(parse_inline(s))
            i += 1
        out.append("<p>{}</p>".format(" ".join(para)))
    return out


def markdown_to_html(md_text):
    """Full pipeline: escape raw HTML first, then build blocks."""
    meta, body = parse_frontmatter(md_text)
    # escape HTML everywhere first (so <div> etc. show as text)
    safe = html.escape(body, quote=False)
    lines = safe.split("\n")
    body_html = "\n".join(render_blocks(lines))

    title = meta.get(TITLE_META) or "Untitled"
    date = meta.get(DATE_META) or ""
    date_safe = html.escape(date, quote=True)
    meta_html = "<p class=\"meta\">{}</p>".format(date_safe) if date else ""
    content = PAGE_TEMPLATE.format(
        title=html.escape(title, quote=True), css=CSS,
        meta_html=meta_html, content=body_html)
    return meta, content


def build(src, out):
    src = os.path.abspath(src)
    out = os.path.abspath(out)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)

    pages = []  # (out_filename, title, date, rel_source)
    for name in sorted(os.listdir(src)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(src, name)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        meta, page_html = markdown_to_html(text)
        stem = name[:-3]
        out_file = os.path.join(out, stem + ".html")
        with open(out_file, "w", encoding="utf-8") as fh:
            fh.write(page_html)
        pages.append((stem + ".html", meta.get(TITLE_META) or stem,
                      meta.get(DATE_META) or "", name))

    # index, sorted by date descending (pages without a date sort last)
    def sort_key(p):
        return (not bool(p[2]), p[2])
    pages.sort(key=sort_key, reverse=True)

    cards = []
    for fname, title, date, src_name in pages:
        meta = "<span class=\"date\">{}</span> ".format(date) if date else ""
        cards.append(
            '<div class="card">'
            '<h2><a href="{f}">{t}</a></h2>'
            '<p>{d}<span class="path">{p}</span></p>'
            '</div>'.format(f=html.escape(fname, quote=True),
                            t=html.escape(title, quote=True),
                            d=meta,
                            p=html.escape(src_name, quote=True)))
    index_css = INDEX_CSS + (
        ".card{background:#161a21;border:1px solid #2a2e37;border-radius:10px;"
        "padding:16px 20px;margin:16px 0}"
        ".card h2{margin:0 0 6px;border:0}"
        ".card .date{color:#9aa0a6}.card .path{color:#6b7280;font-size:.85em}"
    )
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Index</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<h1>Index</h1>
<p class="back"><a href=".">Site root</a></p>
{cards}
</div>
</body>
</html>
""".format(css=index_css, cards="\n".join(cards))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_html)
    return len(pages)


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 3 or args[0] != "build":
        sys.stderr.write(
            "Usage: python3 md_pages.py build SRC OUT\n"
            "  SRC   folder containing .md source files\n"
            "  OUT   destination folder for the generated HTML site\n")
        return 2
    src, out = args[1], args[2]
    if not os.path.isdir(src):
        sys.stderr.write("error: source folder not found: {}\n".format(src))
        return 2
    n = build(src, out)
    print("Built {} page(s) into {}".format(n, os.path.abspath(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
