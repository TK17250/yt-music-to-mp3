"""Command-line interface: ``ytmusic-dl`` / ``yt-music-to-mp3`` / ``python -m ytmusic_dl``."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .core import (
    AUDIO_FORMATS,
    MP3_BITRATES,
    DownloadConfig,
    MissingDependencyError,
    check_dependencies,
    download,
    parse_url_lines,
    read_url_file,
)

EPILOG = """\
examples:
  %(prog)s "https://music.youtube.com/watch?v=VIDEO_ID"
  %(prog)s "https://music.youtube.com/playlist?list=OLAK5uy_..."   # whole album
  %(prog)s -f links.txt --zip                                      # many links, then zip
  %(prog)s URL --format m4a                                        # no re-encoding
  %(prog)s URL --cookies-from chrome                               # "confirm you're not a bot"
  %(prog)s --check                                                 # verify ffmpeg/deno/yt-dlp

Only download music you have the rights to.
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ytmusic-dl",
        description="Download songs, albums and playlists from YouTube Music as tagged "
        "audio files (MP3/M4A/Opus) with cover art, organized as Artist/Album/NN - Title.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("urls", nargs="*", metavar="URL", help="song, album or playlist link(s)")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    src = p.add_argument_group("input")
    src.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        help="text file with one link per line ('#' comments allowed); use '-' for stdin",
    )

    out = p.add_argument_group("output")
    out.add_argument(
        "-o", "--out", default="Music", metavar="DIR", help="output folder (default: %(default)s)"
    )
    out.add_argument(
        "--format",
        default="mp3",
        choices=AUDIO_FORMATS,
        help="audio format (default: %(default)s - plays everywhere)",
    )
    out.add_argument(
        "--bitrate",
        default="192",
        choices=MP3_BITRATES,
        help="MP3 bitrate in kbps (default: %(default)s). YouTube Music sources are "
        "~128-160k, so going above 192 rarely helps",
    )
    out.add_argument("--no-cover", action="store_true", help="do not embed cover art")
    out.add_argument(
        "--zip",
        action="store_true",
        help="bundle all audio in the output folder into a zip when done",
    )
    out.add_argument(
        "--zip-path",
        metavar="PATH",
        help="where to write the zip (default: <out>.zip next to the folder); implies --zip",
    )

    dl = p.add_argument_group("download")
    dl.add_argument(
        "--single",
        action="store_true",
        help="download only the song, even if the link contains &list=",
    )
    dl.add_argument(
        "--no-archive",
        action="store_true",
        help="re-download songs even if they are listed in <out>/downloaded.txt",
    )
    dl.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="pause between requests to avoid rate limits (default: %(default)s)",
    )
    dl.add_argument(
        "--cookies-from",
        metavar="BROWSER",
        help="use cookies from a browser, e.g. chrome, firefox, edge, safari",
    )
    dl.add_argument("--cookies", metavar="FILE", help="use a Netscape-format cookies.txt file")

    misc = p.add_argument_group("misc")
    verbosity = misc.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true", help="only print errors")
    verbosity.add_argument("-v", "--verbose", action="store_true", help="print yt-dlp debug output")
    misc.add_argument(
        "--check",
        action="store_true",
        help="check that yt-dlp, ffmpeg and deno are installed, then exit",
    )
    return p


def collect_urls(args: argparse.Namespace) -> list[str]:
    urls = list(args.urls)
    if args.file == "-":
        urls += parse_url_lines(sys.stdin)
    elif args.file:
        urls += read_url_file(args.file)
    return urls


def run_check() -> int:
    ok = True
    for dep in check_dependencies():
        if dep.found:
            mark = "ok"
        elif dep.required:
            mark = "MISSING"
            ok = False
        else:
            mark = "missing (recommended)"
        print(f"{dep.name:<7} {mark:<22} {dep.detail}")
    return 0 if ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check:
        return run_check()

    if args.sleep < 0:
        parser.error("--sleep must be 0 or greater")
    try:
        urls = collect_urls(args)
    except OSError as exc:
        parser.error(f"cannot read --file: {exc}")
    if not urls:
        parser.error("give at least one URL, or use -f links.txt")

    config = DownloadConfig(
        out_dir=Path(args.out),
        audio_format=args.format,
        bitrate=args.bitrate,
        single=args.single,
        embed_cover=not args.no_cover,
        cookies_from_browser=args.cookies_from,
        cookies_file=Path(args.cookies) if args.cookies else None,
        use_archive=not args.no_archive,
        sleep_requests=args.sleep,
        make_zip=args.zip or bool(args.zip_path),
        zip_path=Path(args.zip_path) if args.zip_path else None,
        quiet=args.quiet,
        verbose=args.verbose,
    )

    def info(msg: str) -> None:
        if not args.quiet:
            print(msg)

    if shutil.which("deno") is None and not args.quiet:
        print(
            "warning: deno not found - YouTube downloads may fail or be low quality. "
            "Run `ytmusic-dl --check` for install hints.",
            file=sys.stderr,
        )

    info(f"Downloading {len(urls)} link(s) -> {config.out_dir.resolve()}")
    try:
        result = download(urls, config)
    except MissingDependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    if result.zip_path is not None:
        info(f"Created {result.zip_path} ({result.zipped_files} track(s))")
    if result.ok:
        info("Done.")
        return 0
    print("Done, but some tracks failed to download (see messages above).", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
