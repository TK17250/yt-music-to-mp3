# yt-music-to-mp3 (ภาษาไทย)

[English README](README.md)

เครื่องมือบรรทัดคำสั่ง (CLI) สำหรับโหลดเพลง อัลบั้ม และเพลย์ลิสต์จาก **YouTube Music**
เป็นไฟล์ **MP3 / M4A / Opus** พร้อมข้อมูลเพลงและภาพปก จัดเก็บเป็นโฟลเดอร์ และรวมเป็นไฟล์ **zip** ได้
ทำงานบน [yt-dlp](https://github.com/yt-dlp/yt-dlp) และ [ffmpeg](https://ffmpeg.org/)

> **โปรดใช้กับเพลงที่คุณมีสิทธิ์เท่านั้น** การดาวน์โหลดเนื้อหาที่มีลิขสิทธิ์อาจขัดต่อข้อตกลงของ YouTube
> และกฎหมายในประเทศของคุณ ผู้ใช้เป็นผู้รับผิดชอบการใช้งานเอง

## ความสามารถ

- รองรับลิงก์เพลง อัลบั้ม และเพลย์ลิสต์จาก `music.youtube.com`
- จัดไฟล์เป็น `ศิลปิน/อัลบั้ม/01 - ชื่อเพลง.mp3` (เพลงที่ไม่มีอัลบั้มจะอยู่ในโฟลเดอร์ `Singles`)
- ฝังชื่อเพลง ศิลปิน อัลบั้ม ลำดับเพลง และภาพปก (ครอปเป็นสี่เหลี่ยมจัตุรัส)
- ข้ามเพลงที่เคยโหลดแล้ว (บันทึกไว้ใน `downloaded.txt`)
- รวมทุกไฟล์เป็น zip ด้วย `--zip`

## สิ่งที่ต้องมี

- Python 3.10 ขึ้นไป
- ffmpeg: `brew install ffmpeg` · `sudo apt install ffmpeg` · `winget install ffmpeg`
- deno (แนะนำ จำเป็นสำหรับ yt-dlp รุ่นใหม่): `brew install deno` · `winget install DenoLand.Deno`

## ติดตั้ง

```bash
pipx install git+https://github.com/TK17250/yt-music-to-mp3.git
# หรือ
pip install git+https://github.com/TK17250/yt-music-to-mp3.git
```

ตรวจสอบว่าติดตั้งครบ:

```bash
ytmusic-dl --check
```

## วิธีใช้

```bash
ytmusic-dl "https://music.youtube.com/watch?v=..."              # เพลงเดียว
ytmusic-dl "https://music.youtube.com/playlist?list=OLAK5uy_..." # ทั้งอัลบั้ม
ytmusic-dl -f links.txt --zip                                     # หลายลิงก์จากไฟล์ แล้วรวมเป็น zip
ytmusic-dl URL --format m4a                                       # ไม่แปลงไฟล์ คุณภาพเท่าต้นฉบับ
ytmusic-dl URL --cookies-from chrome                              # ถ้าเจอ "Sign in to confirm you're not a bot"
```

ดูตัวเลือกทั้งหมดได้ด้วย `ytmusic-dl --help` หรือใน [README ภาษาอังกฤษ](README.md#options)

## สัญญาอนุญาต

[MIT](LICENSE)
