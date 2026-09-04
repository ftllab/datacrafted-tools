# voiceover-duck

Mix a voiceover on top of background music with **automatic ducking** — the music
dips automatically whenever the voice speaks, then comes back up. Exactly what a
narrator or podcaster needs, in one command.

**Zero dependency** — pure Python 3.9+ standard library. It simply builds the
correct ffmpeg ducking filter graph for you; the actual processing is done by
your local ffmpeg.

## Requirements

- **ffmpeg >= 4.4** (for `sidechaincompress` support) available on `PATH`
  - macOS (Homebrew): `brew install ffmpeg`
- Python 3.9+ (standard library only)

If ffmpeg is missing, the script stops with a clear message instead of failing
silently.

## Usage

```sh
python3 voiceover_duck.py voice.m4a music.mp3 -o voiceover_final.m4a
```

Defaults produce `voice_ducked.m4a` in the current directory.

### Options

| Option             | Default  | Description                                          |
|--------------------|----------|------------------------------------------------------|
| `voice`            | —        | Voice / voiceover audio input (positional)           |
| `music`            | —        | Background music audio input (positional)            |
| `-o, --out`        | `voice_ducked.m4a` | Output file                                |
| `--bg-volume`      | `0.22`   | Background music level (0–1)                         |
| `--threshold`      | `0.03`   | Ducking threshold                                    |
| `--ratio`          | `6`      | Ducking ratio (higher = more aggressive)             |
| `--attack`         | `10`     | Ducking attack time in ms                            |
| `--release`        | `400`    | Ducking release time in ms                           |
| `--video`          | off      | Copy the video stream from the voice input (`-map 0:v -c:v copy`) |

### Example with a video voice input

```sh
python3 voiceover_duck.py clip.mp4 bed.mp3 -o voiceover.mp4 --video
```

This keeps the video track of `clip.mp4` and applies the ducked mix as its audio.

## How it works

The script runs ffmpeg with this ducking graph (`sidechaincompress`):

```
[1:a]volume=BGV,asplit=2[bg1][bg2];
[bg1][0:a]sidechaincompress=threshold=T:ratio=R:attack=A:release=REL[bduck];
[0:a][bduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]
```

The voice track feeds the compressor's *sidechain*, so the music only ducks when
the voice is present. The mix is encoded as AAC 192 kbps.

(Note: `asplit=2` emits a second `[bg2]` branch that is unused by the graph, so
ffmpeg requires it to be consumed — the tool routes it to a null sink. The
output audio is identical to the graph above.)

## Tests

```sh
cd voiceover-duck
python3 -m unittest -v test_voiceover_duck.py
```

The test synthesises two mono 44.1 kHz sine WAVs with the standard library
(`wave` + `math`), runs the mix and verifies a real output file is produced.
It is skipped automatically if ffmpeg is not installed.

## License

MIT — see the repository root [`LICENSE`](../LICENSE).
