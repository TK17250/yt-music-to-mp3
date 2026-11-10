# yt-music-to-mp3

[![CI](https://github.com/TK17250/yt-music-to-mp3/actions/workflows/ci.yml/badge.svg)](https://github.com/TK17250/yt-music-to-mp3/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

A small command-line tool that downloads songs, albums and playlists from
**YouTube Music** as properly tagged **MP3 / M4A / Opus** files with cover art,
organizes them into folders, and can bundle everything into a **zip**.

It is a thin, opinionated wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp)
and [ffmpeg](https://ffmpeg.org/).

[ภาษาไทย (Thai README)](README.th.md)

> **Only download music you have the rights to.** Downloading copyrighted content
> may violate YouTube's Terms of Service and the law in your country. You are
> responsible for how you use this tool.

## Features

- Works with **song, album and playlist** links from `music.youtube.com`
- Organizes files as `Artist/Album/01 - Title.mp3` (tracks without an album go into `Artist/Singles/`)
- Embeds **title, artist, album, track number and square cover art**
- **Skips songs already downloaded** (tracked in `<out>/downloaded.txt`), so re-running is cheap
- Optional **zip** of the whole library (`--zip`)
- Batch mode: read links from a file or stdin (`-f links.txt`, `-f -`)
- Useful exit codes for scripting, and a `--check` command to verify dependencies
- Usable as a **Python library** too

### Why YouTube Music links?

Most `music.youtube.com` links point to the official album audio ("Topic" / Art Track)
rather than the music video, so you get audio without intros, dialogue or sound effects,
and yt-dlp receives more complete artist, album and track-number metadata.

## Requirements

| Tool | Why | Install |
| --- | --- | --- |
| Python 3.10+ | runs the tool | <https://www.python.org/downloads/> |
| ffmpeg | audio conversion, tagging, cover art | `brew install ffmpeg` · `sudo apt install ffmpeg` · `winget install ffmpeg` |
| deno *(recommended)* | recent yt-dlp versions need a JS runtime for YouTube | `brew install deno` · `winget install DenoLand.Deno` · <https://deno.com> |

`yt-dlp` is installed automatically as a dependency.

## Installation

With [pipx](https://pipx.pypa.io/) (recommended for CLI tools):

```bash
pipx install git+https://github.com/TK17250/yt-music-to-mp3.git
```

Or with pip:

```bash
pip install git+https://github.com/TK17250/yt-music-to-mp3.git
```

Or from a local clone:

```bash
git clone https://github.com/TK17250/yt-music-to-mp3.git
cd yt-music-to-mp3
pip install .
```

This installs two equivalent commands: **`ytmusic-dl`** and **`yt-music-to-mp3`**.
You can also run `python -m ytmusic_dl`.

Verify your setup:

```console
$ ytmusic-dl --check
yt-dlp  ok                     2026.10.26
ffmpeg  ok                     /opt/homebrew/bin/ffmpeg
deno    ok                     /opt/homebrew/bin/deno
```

## Usage

```bash
# One song
ytmusic-dl "https://music.youtube.com/watch?v=VIDEO_ID"

# A whole album or playlist
ytmusic-dl "https://music.youtube.com/playlist?list=OLAK5uy_..."

# Many links from a file, then zip everything
ytmusic-dl -f links.txt --zip

# Pipe links in
cat links.txt | ytmusic-dl -f -

# Keep the original AAC audio (no re-encoding) as .m4a
ytmusic-dl URL --format m4a

# Higher bitrate MP3, custom output folder and zip location
ytmusic-dl URL --bitrate 320 -o ~/Music/YTM --zip-path ~/Desktop/ytm.zip

# Got "Sign in to confirm you're not a bot"? Use your browser's cookies
ytmusic-dl URL --cookies-from chrome
```

`links.txt` contains one link per line; blank lines and lines starting with `#` are ignored:

```text
# Albums
https://music.youtube.com/playlist?list=OLAK5uy_xxxxxxxx
# Singles
https://music.youtube.com/watch?v=xxxxxxxxxxx
```

Resulting layout:

```text
Music/
├── downloaded.txt
└── Artist Name/
    ├── Album Name/
    │   ├── 01 - First Song.mp3
    │   └── 02 - Second Song.mp3
    └── Singles/
        └── Some Single.mp3
Music.zip            # with --zip
```

### Options

| Option | Description |
| --- | --- |
| `URL ...` | Song, album or playlist link(s) |
| `-f, --file PATH` | Text file with one link per line (`-` reads stdin) |
| `-o, --out DIR` | Output folder (default: `Music`) |
| `--format {mp3,m4a,opus}` | Audio format (default: `mp3`) |
| `--bitrate {128,192,256,320}` | MP3 bitrate in kbps (default: `192`). Sources are ~128–160 kbps, so higher rarely helps |
| `--no-cover` | Don't embed cover art |
| `--zip` | Zip all audio in the output folder when done (`<out>.zip` next to the folder) |
| `--zip-path PATH` | Where to write the zip (implies `--zip`) |
| `--single` | Only download the song even if the link contains `&list=` |
| `--no-archive` | Re-download songs already listed in `downloaded.txt` |
| `--sleep SECONDS` | Pause between requests to avoid rate limits (default: `1`, `0` disables) |
| `--cookies-from BROWSER` | Use cookies from `chrome`, `firefox`, `edge`, `safari`, … |
| `--cookies FILE` | Use a Netscape-format `cookies.txt` |
| `-q, --quiet` / `-v, --verbose` | Less / more output |
| `--check` | Check that yt-dlp, ffmpeg and deno are installed |
| `-V, --version` | Show the version |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Everything downloaded (or `--check` passed) |
| `1` | Some tracks failed (others were still downloaded), or `--check` found a missing required tool |
| `2` | Usage error or missing dependency (e.g. ffmpeg) |
| `130` | Interrupted with Ctrl+C |

## Use as a library

```python
from pathlib import Path
from ytmusic_dl import DownloadConfig, download

result = download(
    ["https://music.youtube.com/playlist?list=OLAK5uy_..."],
    DownloadConfig(out_dir=Path("Music"), audio_format="m4a", make_zip=True),
)
print(result.ok, result.zip_path, result.zipped_files)
```

## Troubleshooting

- **`Sign in to confirm you're not a bot`**: pass `--cookies-from <browser>` (be logged in to YouTube in that browser) or `--cookies cookies.txt`.
- **Downloads fail or only low-quality formats are found**: install `deno`, and update yt-dlp: `pipx upgrade yt-music-to-mp3` or `pip install -U yt-dlp`. YouTube changes often; an outdated yt-dlp is the most common cause.
- **A song is skipped**: it's recorded in `<out>/downloaded.txt`. Use `--no-archive` or remove its line.
- **`ffmpeg was not found`**: install ffmpeg and make sure it's on your `PATH` (`ytmusic-dl --check`).

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md). Please also read the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE) © TK17250

This project is not affiliated with, endorsed by, or sponsored by YouTube or Google.
