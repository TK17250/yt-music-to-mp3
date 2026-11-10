"""
ytmusic_dl.py - Download songs from YouTube Music as audio files using yt-dlp.
Use only with music you have the rights to.

Why download from YouTube Music
  Most links on music.youtube.com point to the album audio version (Topic / Art Track),
  without the dialogue or sound effects from music videos, and yt-dlp gets more complete
  artist, album and track number metadata.

Features
  - Supports song, album and playlist links from music.youtube.com
  - Organizes files as  Artist/Album/01 - Title.mp3
  - Embeds title, artist, album, track number and cover art (cropped to a square)
  - Skips songs that were already downloaded (tracked in downloaded.txt)
  - Can bundle everything into a zip (--zip)

Requirements
  pip install -U "yt-dlp[default]"
  ffmpeg : winget install ffmpeg   | brew install ffmpeg   | sudo apt install ffmpeg
  deno   : winget install DenoLand.Deno | brew install deno  (required by recent yt-dlp for YouTube)

Usage
  python ytmusic_dl.py "https://music.youtube.com/watch?v=..."
  python ytmusic_dl.py "https://music.youtube.com/playlist?list=OLAK5uy_..."   (whole album)
  python ytmusic_dl.py -f links.txt --zip
  python ytmusic_dl.py URL --format m4a                (no re-encoding, better quality if your player supports it)
  python ytmusic_dl.py URL --cookies-from chrome       (if you get "Sign in to confirm you're not a bot")
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit('ยังไม่ได้ติดตั้ง yt-dlp  ->  pip install -U "yt-dlp[default]"')

# Artist/Album/Track - Title   (songs without album info go into the Singles folder)
OUTTMPL = (
    "%(artists.0,artist,uploader|Unknown Artist)s/"
    "%(album|Singles)s/"
    "%(track_number,playlist_index&{:02d} - |)s%(title)s.%(ext)s"
)

# Crop YouTube's 16:9 thumbnail to a square, like an album cover
SQUARE_COVER = (
    "ThumbnailsConvertor+FFmpeg_o:-c:v mjpeg -qmin 1 -qscale:v 1 "
    "-vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""
)


def read_urls(args) -> list[str]:
    urls = list(args.urls)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def build_options(args, out_dir: Path) -> dict:
    cli = [
        "-f", "bestaudio/best",
        "-x", "--audio-format", args.format,
        "-P", str(out_dir),
        "-o", OUTTMPL,
        "--windows-filenames",
        "--embed-metadata",
        # Fall back to the playlist position as the track number if YouTube doesn't provide one
        "--parse-metadata", "%(track_number,playlist_index)s:%(track_number)s",
        "--download-archive", str(out_dir / "downloaded.txt"),
        "--ignore-errors",
        "--sleep-requests", "1",          # throttle requests to avoid getting blocked on bulk downloads
    ]
    if args.format == "mp3":
        cli += ["--audio-quality", f"{args.bitrate}K"]
    cli += ["--no-playlist"] if args.single else ["--yes-playlist"]
    if not args.no_cover:
        cli += ["--embed-thumbnail", "--convert-thumbnails", "jpg", "--ppa", SQUARE_COVER]
    if args.cookies_from:
        cli += ["--cookies-from-browser", args.cookies_from]
    return yt_dlp.parse_options(cli).ydl_opts


def make_zip(out_dir: Path, zip_path: Path) -> int:
    files = sorted(f for f in out_dir.rglob("*") if f.suffix in (".mp3", ".m4a", ".opus"))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:  # audio is already compressed
        for f in files:
            zf.write(f, f.relative_to(out_dir))
    return len(files)


def main():
    p = argparse.ArgumentParser(description="โหลดเพลงจาก YouTube Music ด้วย yt-dlp")
    p.add_argument("urls", nargs="*", help="ลิงก์เพลง/อัลบั้ม/เพลย์ลิสต์")
    p.add_argument("-f", "--file", help="ไฟล์ข้อความที่มีลิงก์บรรทัดละ 1 ลิงก์")
    p.add_argument("-o", "--out", default="Music", help="โฟลเดอร์ปลายทาง (ค่าเริ่มต้น: Music)")
    p.add_argument("--format", default="mp3", choices=["mp3", "m4a", "opus"],
                   help="ชนิดไฟล์ (ค่าเริ่มต้น: mp3 เปิดได้ทุกเครื่อง)")
    p.add_argument("--bitrate", default="192", choices=["128", "192", "256", "320"],
                   help="บิตเรต MP3 (ต้นฉบับ YouTube Music ราว 128-160k ตั้งสูงกว่า 192 แทบไม่ต่าง)")
    p.add_argument("--single", action="store_true",
                   help="โหลดแค่เพลงเดียว แม้ลิงก์จะมี &list= ติดมา")
    p.add_argument("--no-cover", action="store_true", help="ไม่ฝังภาพปก")
    p.add_argument("--cookies-from", metavar="BROWSER",
                   help="ใช้คุกกี้จากเบราว์เซอร์ เช่น chrome, firefox, edge")
    p.add_argument("--zip", action="store_true", help="รวมไฟล์ทั้งหมดเป็น zip เมื่อเสร็จ")
    args = p.parse_args()

    urls = read_urls(args)
    if not urls:
        p.error("ใส่ลิงก์อย่างน้อย 1 ลิงก์ หรือใช้ -f links.txt")
    if shutil.which("ffmpeg") is None:
        sys.exit("ไม่พบ ffmpeg - ติดตั้งก่อน (ดูวิธีที่หัวไฟล์)")
    if shutil.which("deno") is None:
        print("คำเตือน: ไม่พบ deno - YouTube อาจโหลดไม่ได้หรือได้คุณภาพต่ำ (ดูวิธีติดตั้งที่หัวไฟล์)")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"กำลังโหลด {len(urls)} ลิงก์ -> {out_dir.resolve()}")
    with yt_dlp.YoutubeDL(build_options(args, out_dir)) as ydl:
        failed = ydl.download(urls)

    if args.zip:
        zip_path = out_dir.with_suffix(".zip")
        n = make_zip(out_dir, zip_path)
        print(f"สร้าง {zip_path} แล้ว ({n} เพลง)")

    print("เสร็จแล้ว" + (" (บางเพลงโหลดไม่สำเร็จ ดูข้อความด้านบน)" if failed else ""))


if __name__ == "__main__":
    main()
