#!/usr/bin/env python3
"""voiceover_duck.py -- Mix a voice track over background music with auto-ducking.

Zero-dependency CLI (Python 3.9+, stdlib only) that drives ffmpeg.

The voice (channel 0) is kept at full level while background music (channel 1)
is automatically lowered whenever the voice is loud -- classic "ducking" for
voiceovers and podcasts -- then the two are mixed into a single output.

Requires ffmpeg >= 4.4 (sidechaincompress support). Checks availability with
shutil.which before running.
"""
import argparse
import shutil
import subprocess
import sys

# voice = input 0, music = input 1. Ducking graph (music auto-lowered while the
# voice is loud): the volume-scaled music is asplit into [bg1]/[bg2]; [bg1] is
# sidechain-compressed against the voice (input 0) into the ducked music
# [bduck]; full voice is then mixed with the ducked music.
#   ffmpeg requires every asplit output to be connected, so the redundant
#   [bg2] branch (asplit=2 produces two outputs but only [bg1] is needed here)
#   is sent to a null sink -- audio is identical to the classic graph below.
FILTER = (
    "[1:a]volume={bgv},asplit=2[bg1][bg2];"
    "[bg1][0:a]sidechaincompress=threshold={t}:ratio={r}:attack={a}:release={re}[bduck];"
    "[0:a][bduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a];"
    "[bg2]anull"
)


def build_parser():
    p = argparse.ArgumentParser(
        description="Mix voice + background music with automatic ducking via ffmpeg."
    )
    p.add_argument("voice", help="Voice/voiceover audio input file")
    p.add_argument("music", help="Background music audio input file")
    p.add_argument("-o", "--out", default="voice_ducked.m4a",
                   help="Output file (default: voice_ducked.m4a)")
    p.add_argument("--bg-volume", type=float, default=0.22, metavar="V",
                   help="Background music level (0-1, default 0.22)")
    p.add_argument("--threshold", type=float, default=0.03, metavar="T",
                   help="Ducking threshold (default 0.03)")
    p.add_argument("--ratio", type=float, default=6, metavar="R",
                   help="Ducking ratio (default 6)")
    p.add_argument("--attack", type=float, default=10, metavar="MS",
                   help="Ducking attack in ms (default 10)")
    p.add_argument("--release", type=float, default=400, metavar="MS",
                   help="Ducking release in ms (default 400)")
    p.add_argument("--video", action="store_true",
                   help="Keep the video stream from the voice input (-map 0:v -c:v copy)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        sys.stderr.write(
            "error: ffmpeg not found on PATH. voiceover_duck needs ffmpeg >= 4.4 "
            "to build the ducking graph.\n"
            "Install it with Homebrew:  brew install ffmpeg\n"
        )
        return 1

    filt = FILTER.format(
        bgv=args.bg_volume,
        t=args.threshold,
        r=args.ratio,
        a=args.attack,
        re=args.release,
    )

    cmd = [
        ffmpeg, "-y",
        "-i", args.voice,
        "-i", args.music,
        "-filter_complex", filt,
    ]
    if args.video:
        cmd += ["-map", "0:v", "-c:v", "copy"]
    cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k", args.out]

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        sys.stderr.write("error: ffmpeg exited with code {}\n".format(proc.returncode))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
