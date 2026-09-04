#!/usr/bin/env python3
"""Tests for voiceover_duck.py (stdlib unittest, subprocess-based).

Synthesises two 3s mono 44.1 kHz sine WAVs with the standard library
(wave + math) inside .test_tmp/, runs the CLI and checks the output exists.
Skipped automatically when ffmpeg is not installed.
"""
import math
import os
import shutil
import struct
import subprocess
import sys
import unittest
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "voiceover_duck.py")
TMP = os.path.join(HERE, ".test_tmp")

RATE = 44100
DURATION = 3.0
AMPLITUDE = 16000


def make_sine_wav(path, freq):
    os.makedirs(TMP, exist_ok=True)
    n = int(RATE * DURATION)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = b"".join(
            struct.pack("<h", int(AMPLITUDE * math.sin(2 * math.pi * freq * i / RATE)))
            for i in range(n)
        )
        w.writeframes(frames)


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


@unittest.skipUnless(has_ffmpeg(), "ffmpeg not available on this machine")
class VoiceoverDuckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.voice = os.path.join(TMP, "voice.wav")
        cls.music = os.path.join(TMP, "music.wav")
        make_sine_wav(cls.voice, 440)
        make_sine_wav(cls.music, 220)
        cls.out = os.path.join(TMP, "out.m4a")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, CLI] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )

    def test_mix_produces_output(self):
        proc = self.run_cli(self.voice, self.music, "-o", self.out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.exists(self.out), "output file missing")
        self.assertGreater(os.path.getsize(self.out), 1024,
                           "output file too small")

    def test_custom_volume_output(self):
        out2 = os.path.join(TMP, "out2.m4a")
        proc = self.run_cli(self.voice, self.music, "-o", out2,
                            "--bg-volume", "0.1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.exists(out2))

    def test_missing_ffmpeg_reports_clear_error(self):
        # Simulate ffmpeg absence by hiding PATH.
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        proc = subprocess.run(
            [sys.executable, CLI, self.voice, self.music, "-o", self.out],
            capture_output=True, text=True, encoding="utf-8",
            timeout=120, env=env,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ffmpeg", proc.stderr.lower())


if __name__ == "__main__":
    unittest.main()
