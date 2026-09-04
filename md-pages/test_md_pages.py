#!/usr/bin/env python3
"""Tests for md_pages.py (stdlib unittest)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "md_pages.py")

SAMPLE = """---
title: Sample page
date: 2026-05-01
---
# Hello World

This is a sample with a [link](https://example.com) and a list:

- item one
- item two

```python
print("hi")
```
"""


class MdPagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mdpages_")
        self.src = os.path.join(self.tmp, "src")
        self.out = os.path.join(self.tmp, "out")
        os.makedirs(self.src)
        with open(os.path.join(self.src, "sample.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(SAMPLE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self):
        return subprocess.run(
            [sys.executable, CLI, "build", self.src, self.out],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )

    def test_build_generates_pages(self):
        proc = self.build()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.out, "sample.html")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "index.html")))

    def test_sample_html_has_expected_markup(self):
        self.build()
        path = os.path.join(self.out, "sample.html")
        with open(path, "r", encoding="utf-8") as fh:
            htmltext = fh.read()
        self.assertIn("<h1>", htmltext)
        self.assertIn("Hello World", htmltext)
        self.assertIn("<a href=\"https://example.com\"", htmltext)
        self.assertIn("<code>", htmltext)
        self.assertIn("<ul>", htmltext)
        self.assertIn("print(&quot;hi&quot;)", htmltext)  # code escaped

    def test_index_links_to_sample(self):
        self.build()
        path = os.path.join(self.out, "index.html")
        with open(path, "r", encoding="utf-8") as fh:
            htmltext = fh.read()
        self.assertIn('href="sample.html"', htmltext)
        self.assertIn("Sample page", htmltext)
        self.assertIn("2026-05-01", htmltext)

    def test_raw_html_is_escaped(self):
        with open(os.path.join(self.src, "evil.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("# Title\n\n<div>should be text</div>\n")
        self.build()
        path = os.path.join(self.out, "evil.html")
        with open(path, "r", encoding="utf-8") as fh:
            htmltext = fh.read()
        self.assertNotIn("<div>should be text</div>", htmltext)
        self.assertIn("&lt;div&gt;should be text&lt;/div&gt;", htmltext)

    def test_bad_usage_returns_2(self):
        proc = subprocess.run([sys.executable, CLI], capture_output=True,
                              text=True, timeout=30)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
