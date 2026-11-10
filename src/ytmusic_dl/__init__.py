"""Download songs, albums and playlists from YouTube Music as tagged audio files."""

__version__ = "1.0.0"

from .core import (  # noqa: E402
    DownloadConfig,
    DownloadResult,
    MissingDependencyError,
    check_dependencies,
    download,
    make_zip,
)

__all__ = [
    "DownloadConfig",
    "DownloadResult",
    "MissingDependencyError",
    "__version__",
    "check_dependencies",
    "download",
    "make_zip",
]
