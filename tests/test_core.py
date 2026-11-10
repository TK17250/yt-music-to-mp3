import zipfile
from pathlib import Path

import pytest

from ytmusic_dl import core
from ytmusic_dl.core import (
    DownloadConfig,
    build_cli_args,
    build_ydl_options,
    default_zip_path,
    find_audio_files,
    make_zip,
    parse_url_lines,
    read_url_file,
)


def test_parse_url_lines_skips_blanks_and_comments():
    lines = ["  https://a  ", "", "# comment", "   ", "https://b", "  # indented comment"]
    assert parse_url_lines(lines) == ["https://a", "https://b"]


def test_read_url_file_handles_utf8_bom(tmp_path):
    f = tmp_path / "links.txt"
    f.write_bytes("﻿https://a\n# x\nhttps://b\n".encode())
    assert read_url_file(f) == ["https://a", "https://b"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"audio_format": "wav"}, "audio_format"),
        ({"bitrate": "999"}, "bitrate"),
        ({"sleep_requests": -1}, "sleep_requests"),
    ],
)
def test_config_validation(kwargs, message):
    with pytest.raises(ValueError, match=message):
        DownloadConfig(**kwargs)


def test_config_coerces_paths():
    cfg = DownloadConfig(out_dir="x", zip_path="y.zip", cookies_file="c.txt")
    assert cfg.out_dir == Path("x")
    assert cfg.zip_path == Path("y.zip")
    assert cfg.cookies_file == Path("c.txt")


def test_default_cli_args():
    args = build_cli_args(DownloadConfig(out_dir=Path("Music")))
    assert args[:5] == ["-f", "bestaudio/best", "-x", "--audio-format", "mp3"]
    assert "--yes-playlist" in args
    assert "--embed-thumbnail" in args
    assert args[args.index("--audio-quality") + 1] == "192K"
    assert args[args.index("--download-archive") + 1] == str(Path("Music") / "downloaded.txt")
    assert args[args.index("--sleep-requests") + 1] == "1"
    assert "--cookies-from-browser" not in args


def test_cli_args_options():
    cfg = DownloadConfig(
        audio_format="m4a",
        single=True,
        embed_cover=False,
        cookies_from_browser="firefox",
        cookies_file=Path("c.txt"),
        use_archive=False,
        sleep_requests=0,
        quiet=True,
    )
    args = build_cli_args(cfg)
    assert "--no-playlist" in args and "--yes-playlist" not in args
    assert "--audio-quality" not in args  # bitrate only applies to mp3
    assert "--embed-thumbnail" not in args
    assert "--download-archive" not in args
    assert "--sleep-requests" not in args
    assert args[args.index("--cookies-from-browser") + 1] == "firefox"
    assert args[args.index("--cookies") + 1] == "c.txt"
    assert "--quiet" in args


def test_build_ydl_options_is_accepted_by_yt_dlp(tmp_path):
    pytest.importorskip("yt_dlp")
    opts = build_ydl_options(DownloadConfig(out_dir=tmp_path, cookies_from_browser="chrome"))
    assert opts["format"] == "bestaudio/best"
    assert opts["ignoreerrors"] is True
    assert opts["download_archive"] == str(tmp_path / "downloaded.txt")
    assert opts["cookiesfrombrowser"][0] == "chrome"
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" in keys
    assert "EmbedThumbnail" in keys


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"data")
    return path


def test_find_audio_files_filters_extensions(tmp_path):
    _touch(tmp_path / "A" / "Album" / "01 - x.mp3")
    _touch(tmp_path / "A" / "Album" / "02 - y.M4A")
    _touch(tmp_path / "A" / "Album" / "03 - z.mp3.part")
    _touch(tmp_path / "downloaded.txt")
    (tmp_path / "weird.mp3").mkdir()
    names = [f.name for f in find_audio_files(tmp_path)]
    assert names == ["01 - x.mp3", "02 - y.M4A"]


def test_make_zip_keeps_layout(tmp_path):
    out = tmp_path / "Music"
    _touch(out / "Artist" / "Album" / "01 - Song.mp3")
    _touch(out / "Artist" / "Singles" / "Other.opus")
    _touch(out / "downloaded.txt")
    zip_path = tmp_path / "nested" / "Music.zip"

    assert make_zip(out, zip_path) == 2
    with zipfile.ZipFile(zip_path) as zf:
        assert sorted(zf.namelist()) == [
            "Artist/Album/01 - Song.mp3",
            "Artist/Singles/Other.opus",
        ]


def test_default_zip_path_handles_dot_and_dotted_names(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert default_zip_path(Path(".")) == tmp_path.resolve().parent / f"{tmp_path.name}.zip"
    assert default_zip_path(Path("Music.v2")) == tmp_path.resolve() / "Music.v2.zip"


def test_download_requires_urls():
    with pytest.raises(ValueError):
        core.download([])


def test_download_requires_ffmpeg(monkeypatch):
    monkeypatch.setattr(core.shutil, "which", lambda name: None)
    with pytest.raises(core.MissingDependencyError, match="ffmpeg"):
        core.download(["https://music.youtube.com/watch?v=x"])


def test_download_flow_with_fake_yt_dlp(tmp_path, monkeypatch):
    monkeypatch.setattr(core.shutil, "which", lambda name: f"/usr/bin/{name}")
    out = tmp_path / "Music"
    calls = {}

    class FakeYDL:
        def __init__(self, opts):
            calls["opts"] = opts

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def download(self, urls):
            calls["urls"] = urls
            _touch(out / "Artist" / "Album" / "01 - Song.mp3")
            return 1  # simulate a partial failure

    class FakeModule:
        YoutubeDL = FakeYDL

    monkeypatch.setattr(core, "_import_yt_dlp", lambda: FakeModule)
    monkeypatch.setattr(core, "build_ydl_options", lambda cfg: {"fake": True})

    result = core.download(["u1", "u2"], DownloadConfig(out_dir=out, make_zip=True))
    assert calls["urls"] == ["u1", "u2"]
    assert result.ok is False and result.errors
    assert result.zip_path == tmp_path.resolve() / "Music.zip"
    assert result.zipped_files == 1


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"title": "Song", "artist": "A"}, "A/Singles/Song.mp3"),
        (
            {"title": "Song", "artist": "A", "album": "Alb", "playlist_index": 3},
            "A/Alb/03 - Song.mp3",
        ),
        (
            {"title": "Song", "artists": ["B", "C"], "album": "Alb", "track_number": 12},
            "B/Alb/12 - Song.mp3",
        ),
        ({"title": "Song", "uploader": "U"}, "U/Singles/Song.mp3"),
        ({"title": "Song"}, "Unknown Artist/Singles/Song.mp3"),
    ],
)
def test_output_filename(info, expected):
    """Regression: missing track numbers used to produce 'NASong.mp3' / 'NA' prefixes."""
    yt_dlp = pytest.importorskip("yt_dlp")
    from yt_dlp.postprocessor.metadataparser import MetadataParserPP

    ydl = yt_dlp.YoutubeDL({"quiet": True, "outtmpl": core.OUTPUT_TEMPLATE})
    info = dict(info, id="x", ext="mp3")
    pp = MetadataParserPP(
        ydl, [(MetadataParserPP.interpretter, core.TRACK_NUMBER_FROM, "%(track_number)s")]
    )
    _, info = pp.run(info)
    assert Path(ydl.prepare_filename(info)).as_posix() == expected
