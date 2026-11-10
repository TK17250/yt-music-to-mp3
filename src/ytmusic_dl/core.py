"""Core download logic, usable as a library independently of the CLI.

Example::

    from ytmusic_dl import DownloadConfig, download

    result = download(["https://music.youtube.com/watch?v=..."], DownloadConfig(make_zip=True))
    print(result.ok, result.zip_path)
"""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

AUDIO_FORMATS = ("mp3", "m4a", "opus")
MP3_BITRATES = ("128", "192", "256", "320")
ARCHIVE_FILENAME = "downloaded.txt"

# Artist/Album/NN - Title.ext   (tracks without album info go into a "Singles" folder)
OUTPUT_TEMPLATE = (
    "%(artists.0,artist,uploader|Unknown Artist)s/"
    "%(album|Singles)s/"
    "%(track_number,playlist_index&{:0>2} - |)s%(title)s.%(ext)s"
)

# Source for the track-number fallback. The empty default ("|") matters: without it yt-dlp
# writes the literal string "NA" into track_number for tracks outside any album/playlist.
TRACK_NUMBER_FROM = "%(track_number,playlist_index|)s"

# Crop YouTube's 16:9 thumbnail to a centered square, like an album cover.
SQUARE_COVER_ARGS = (
    "ThumbnailsConvertor+FFmpeg_o:-c:v mjpeg -qmin 1 -qscale:v 1 "
    "-vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""
)


class MissingDependencyError(RuntimeError):
    """Raised when a required external dependency (yt-dlp, ffmpeg) is missing."""


@dataclass
class DownloadConfig:
    """Options controlling a download run."""

    out_dir: Path = Path("Music")
    audio_format: str = "mp3"
    bitrate: str = "192"
    single: bool = False
    embed_cover: bool = True
    cookies_from_browser: str | None = None
    cookies_file: Path | None = None
    use_archive: bool = True
    sleep_requests: float = 1.0
    make_zip: bool = False
    zip_path: Path | None = None
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        self.out_dir = Path(self.out_dir)
        if self.zip_path is not None:
            self.zip_path = Path(self.zip_path)
        if self.cookies_file is not None:
            self.cookies_file = Path(self.cookies_file)
        if self.audio_format not in AUDIO_FORMATS:
            raise ValueError(
                f"audio_format must be one of {AUDIO_FORMATS}, got {self.audio_format!r}"
            )
        if self.bitrate not in MP3_BITRATES:
            raise ValueError(f"bitrate must be one of {MP3_BITRATES}, got {self.bitrate!r}")
        if self.sleep_requests < 0:
            raise ValueError("sleep_requests must be >= 0")


@dataclass
class DownloadResult:
    """Outcome of a download run."""

    ok: bool
    out_dir: Path
    zip_path: Path | None = None
    zipped_files: int = 0
    errors: list[str] = field(default_factory=list)


def parse_url_lines(lines: Iterable[str]) -> list[str]:
    """Return non-empty, non-comment lines (``#`` starts a comment), stripped."""
    urls = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def read_url_file(path: str | Path) -> list[str]:
    """Read URLs from a text file, one per line. Blank lines and ``#`` comments are ignored."""
    return parse_url_lines(Path(path).read_text(encoding="utf-8-sig").splitlines())


def default_zip_path(out_dir: Path) -> Path:
    """``Music`` -> ``Music.zip`` next to the folder (works for ``.`` and dotted names too)."""
    resolved = Path(out_dir).resolve()
    return resolved.parent / f"{resolved.name}.zip"


def build_cli_args(config: DownloadConfig) -> list[str]:
    """Translate a :class:`DownloadConfig` into yt-dlp command-line arguments."""
    out_dir = config.out_dir
    # fmt: off
    args = [
        "-f", "bestaudio/best",
        "-x", "--audio-format", config.audio_format,
        "-P", str(out_dir),
        "-o", OUTPUT_TEMPLATE,
        "--windows-filenames",
        "--embed-metadata",
        # Fall back to the playlist position as the track number if YouTube doesn't provide one.
        # TRACK_NUMBER_FROM is empty (not "NA") when neither field exists, so nothing is set.
        "--parse-metadata", f"{TRACK_NUMBER_FROM}:%(track_number)s",
        "--ignore-errors",
    ]
    # fmt: on
    if config.sleep_requests > 0:
        # Throttle requests to avoid getting rate-limited on bulk downloads
        args += ["--sleep-requests", f"{config.sleep_requests:g}"]
    if config.use_archive:
        args += ["--download-archive", str(out_dir / ARCHIVE_FILENAME)]
    if config.audio_format == "mp3":
        args += ["--audio-quality", f"{config.bitrate}K"]
    args += ["--no-playlist"] if config.single else ["--yes-playlist"]
    if config.embed_cover:
        args += ["--embed-thumbnail", "--convert-thumbnails", "jpg", "--ppa", SQUARE_COVER_ARGS]
    if config.cookies_from_browser:
        args += ["--cookies-from-browser", config.cookies_from_browser]
    if config.cookies_file:
        args += ["--cookies", str(config.cookies_file)]
    if config.quiet:
        args += ["--quiet", "--no-warnings"]
    if config.verbose:
        args += ["--verbose"]
    return args


def _import_yt_dlp():
    try:
        import yt_dlp
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise MissingDependencyError(
            'yt-dlp is not installed. Install it with:  pip install -U "yt-dlp[default]"'
        ) from exc
    return yt_dlp


def build_ydl_options(config: DownloadConfig) -> dict:
    """Return the options dict to pass to ``yt_dlp.YoutubeDL``."""
    yt_dlp = _import_yt_dlp()
    return yt_dlp.parse_options(build_cli_args(config)).ydl_opts


def find_audio_files(out_dir: Path) -> list[Path]:
    """All finished audio files under ``out_dir`` (sorted, partial downloads excluded)."""
    suffixes = {f".{fmt}" for fmt in AUDIO_FORMATS}
    return sorted(
        f for f in Path(out_dir).rglob("*") if f.is_file() and f.suffix.lower() in suffixes
    )


def make_zip(out_dir: Path, zip_path: Path) -> int:
    """Zip every audio file in ``out_dir`` into ``zip_path``, keeping the folder layout.

    Returns the number of files written. Audio is already compressed, so files are stored as-is.
    """
    out_dir = Path(out_dir)
    zip_path = Path(zip_path)
    files = find_audio_files(out_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
        for f in files:
            zf.write(f, f.relative_to(out_dir).as_posix())
    return len(files)


@dataclass
class DependencyStatus:
    name: str
    found: bool
    required: bool
    detail: str


def check_dependencies() -> list[DependencyStatus]:
    """Report on yt-dlp, ffmpeg and deno availability."""
    statuses = []
    try:
        yt_dlp = _import_yt_dlp()
        statuses.append(DependencyStatus("yt-dlp", True, True, yt_dlp.version.__version__))
    except MissingDependencyError:
        statuses.append(DependencyStatus("yt-dlp", False, True, 'pip install -U "yt-dlp[default]"'))

    ffmpeg = shutil.which("ffmpeg")
    statuses.append(
        DependencyStatus(
            "ffmpeg",
            ffmpeg is not None,
            True,
            ffmpeg or "brew install ffmpeg | sudo apt install ffmpeg | winget install ffmpeg",
        )
    )
    deno = shutil.which("deno")
    statuses.append(
        DependencyStatus(
            "deno",
            deno is not None,
            False,
            deno or "brew install deno | winget install DenoLand.Deno | https://deno.com",
        )
    )
    return statuses


def download(urls: Iterable[str], config: DownloadConfig | None = None) -> DownloadResult:
    """Download ``urls`` according to ``config`` and optionally zip the result."""
    config = config or DownloadConfig()
    urls = list(urls)
    if not urls:
        raise ValueError("no URLs given")
    if shutil.which("ffmpeg") is None:
        raise MissingDependencyError(
            "ffmpeg was not found on PATH. Install it first "
            "(brew install ffmpeg | sudo apt install ffmpeg | winget install ffmpeg)."
        )
    yt_dlp = _import_yt_dlp()

    config.out_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    with yt_dlp.YoutubeDL(build_ydl_options(config)) as ydl:
        retcode = ydl.download(urls)
    if retcode:
        errors.append("one or more tracks failed to download (see messages above)")

    result = DownloadResult(ok=not errors, out_dir=config.out_dir, errors=errors)
    if config.make_zip:
        result.zip_path = config.zip_path or default_zip_path(config.out_dir)
        result.zipped_files = make_zip(config.out_dir, result.zip_path)
    return result
