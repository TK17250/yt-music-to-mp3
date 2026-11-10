# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-11-11

First open-source release.

### Added

- Installable package (`pip install` / `pipx install`) with `ytmusic-dl` and
  `yt-music-to-mp3` commands, plus `python -m ytmusic_dl`.
- `--version`, `--check` (verify yt-dlp/ffmpeg/deno), `--zip-path`, `--no-archive`,
  `--sleep`, `--cookies FILE`, `-q/--quiet`, `-v/--verbose`.
- `-f -` reads links from stdin; UTF-8 BOM in link files is handled.
- Meaningful exit codes (`0` ok, `1` partial failure, `2` usage/dependency error, `130` interrupted).
- Python library API: `DownloadConfig`, `download()`, `make_zip()`, `check_dependencies()`.
- Test suite, CI on Linux/macOS/Windows, English and Thai documentation,
  contributing guide and MIT license.

### Changed

- All CLI messages are now in English.

### Fixed

- Filenames no longer get an `NA` prefix. Singles were saved as `NATitle.mp3`, and album
  tracks lost their number (`NATitle.mp3` instead of `01 - Title.mp3`).
- `--zip` no longer crashes when the output folder is `.`, and keeps dotted folder names
  intact (`Music.v2` → `Music.v2.zip`).
- Zip archives use `/` separators on Windows and include files with upper-case extensions.

[Unreleased]: https://github.com/TK17250/yt-music-to-mp3/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/TK17250/yt-music-to-mp3/releases/tag/v1.0.0
