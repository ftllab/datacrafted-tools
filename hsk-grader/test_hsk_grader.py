#!/usr/bin/env python3
"""Tests for hsk_grader.py (stdlib unittest, subprocess-based)."""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "hsk_grader.py")


def run_cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, CLI] + list(args),
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


class HskGraderTest(unittest.TestCase):
    def test_positional_text_marks_hsk1(self):
        proc = run_cli("我爱我的家人。")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("我", proc.stdout)
        self.assertIn("HSK 1", proc.stdout)

    def test_stdin_input(self):
        proc = run_cli(stdin="我爱我的家人。")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("HSK 1", proc.stdout)

    def test_json_parseable(self):
        proc = run_cli("--json", "我爱我的家人。")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("word", first)
        self.assertIn("pinyin", first)
        self.assertIn("level", first)

    def test_no_tones_strips_diacritics(self):
        proc = run_cli("--no-tones", "--json", "我爱我的家人。")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        for item in data:
            self.assertNotIn("\u0304", item["pinyin"])  # no macron
            self.assertNotIn("\u0301", item["pinyin"])  # no acute
            self.assertNotIn("\u030c", item["pinyin"])  # no caron
            self.assertNotIn("\u0300", item["pinyin"])  # no grave

    def test_summary_line_present(self):
        proc = run_cli("我爱我的家人。")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("mots gradés", proc.stdout)
        self.assertIn("niveaux:", proc.stdout)

    def test_file_input(self):
        sample = os.path.join(HERE, "sample.txt")
        with open(sample, "w", encoding="utf-8") as fh:
            fh.write("我爱我的家人。")
        try:
            proc = run_cli("--file", sample)
        finally:
            os.remove(sample)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("HSK 1", proc.stdout)


if __name__ == "__main__":
    unittest.main()
