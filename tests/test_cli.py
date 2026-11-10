import io
import subprocess
import sys
from pathlib import Path

import pytest

from ytmusic_dl import __version__, cli
from ytmusic_dl.core import DependencyStatus, DownloadResult


@pytest.fixture
def fake_download(monkeypatch):
    captured = {}

    def _download(urls, config):
        captured["urls"] = urls
        captured["config"] = config
        return DownloadResult(ok=captured.get("ok", True), out_dir=config.out_dir)

    monkeypatch.setattr(cli, "download", _download)
    return captured


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_urls_is_usage_error(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2
    assert "at least one URL" in capsys.readouterr().err


def test_negative_sleep_rejected():
    with pytest.raises(SystemExit) as exc:
        cli.main(["--sleep", "-1", "https://x"])
    assert exc.value.code == 2


def test_missing_file_is_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli.main(["-f", str(tmp_path / "nope.txt")])
    assert exc.value.code == 2


def test_quiet_and_verbose_are_exclusive():
    with pytest.raises(SystemExit):
        cli.main(["-q", "-v", "https://x"])


def test_maps_arguments_to_config(fake_download, tmp_path):
    links = tmp_path / "links.txt"
    links.write_text("https://b\n# skip\nhttps://c\n", encoding="utf-8")
    code = cli.main(
        [
            "https://a",
            "-f",
            str(links),
            "-o",
            str(tmp_path / "out"),
            "--format",
            "opus",
            "--single",
            "--no-cover",
            "--no-archive",
            "--sleep",
            "0",
            "--cookies-from",
            "firefox",
            "--zip-path",
            str(tmp_path / "x.zip"),
            "-q",
        ]
    )
    assert code == 0
    assert fake_download["urls"] == ["https://a", "https://b", "https://c"]
    cfg = fake_download["config"]
    assert cfg.out_dir == tmp_path / "out"
    assert cfg.audio_format == "opus"
    assert cfg.single and not cfg.embed_cover and not cfg.use_archive
    assert cfg.sleep_requests == 0
    assert cfg.cookies_from_browser == "firefox"
    assert cfg.make_zip and cfg.zip_path == tmp_path / "x.zip"
    assert cfg.quiet


def test_reads_urls_from_stdin(fake_download, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("https://a\n\nhttps://b\n"))
    assert cli.main(["-f", "-", "-q"]) == 0
    assert fake_download["urls"] == ["https://a", "https://b"]


def test_partial_failure_exit_code(fake_download):
    fake_download["ok"] = False
    assert cli.main(["https://a", "-q"]) == 1


def test_missing_dependency_exit_code(monkeypatch, capsys):
    from ytmusic_dl.core import MissingDependencyError

    def boom(urls, config):
        raise MissingDependencyError("ffmpeg was not found")

    monkeypatch.setattr(cli, "download", boom)
    assert cli.main(["https://a", "-q"]) == 2
    assert "ffmpeg" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([DependencyStatus("ffmpeg", True, True, "/bin/ffmpeg")], 0),
        ([DependencyStatus("deno", False, False, "hint")], 0),
        ([DependencyStatus("ffmpeg", False, True, "hint")], 1),
    ],
)
def test_check(monkeypatch, capsys, statuses, expected):
    monkeypatch.setattr(cli, "check_dependencies", lambda: statuses)
    assert cli.main(["--check"]) == expected
    assert statuses[0].name in capsys.readouterr().out


def test_python_dash_m_entry_point():
    proc = subprocess.run(
        [sys.executable, "-m", "ytmusic_dl", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout
