# Contributing

Thanks for your interest in improving yt-music-to-mp3! Bug reports, feature ideas,
documentation fixes and pull requests are all welcome.

## Reporting bugs

Please [open an issue](https://github.com/TK17250/yt-music-to-mp3/issues/new/choose) and include:

- the command you ran (remove any private links or cookies)
- the output of `ytmusic-dl --version` and `ytmusic-dl --check`
- your OS and Python version
- the full error output (re-run with `-v` for more detail)

Many download failures are caused by YouTube changes and are fixed by updating
yt-dlp (`pip install -U yt-dlp`). Please try that first.

## Development setup

```bash
git clone https://github.com/TK17250/yt-music-to-mp3.git
cd yt-music-to-mp3
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff check .          # lint
ruff format .         # format
pytest                # tests (no network access needed)
```

- Keep changes focused; one feature or fix per pull request.
- Add or update tests for behaviour changes. Tests must not hit the network.
- Update `README.md` (and `CHANGELOG.md` under "Unreleased") for user-facing changes.
- Use [Conventional Commits](https://www.conventionalcommits.org/) style messages
  (`feat:`, `fix:`, `docs:`, ...).

## Project layout

```text
src/ytmusic_dl/
  core.py      download logic, yt-dlp options, zip creation (library API)
  cli.py       argument parsing and terminal output
  __main__.py  `python -m ytmusic_dl`
tests/         pytest suite
```

## Releasing (maintainers)

1. Bump `__version__` in `src/ytmusic_dl/__init__.py` and update `CHANGELOG.md`.
2. Commit, tag `vX.Y.Z`, push the tag, and publish a GitHub Release.
3. The `release` workflow builds the package and publishes it to PyPI
   (requires [trusted publishing](https://docs.pypi.org/trusted-publishers/) to be configured).
