from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import uuid
import zipfile
import imageio_ffmpeg
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.getcwd()
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
FRAMES_DIR = os.path.join(BASE_DIR, "frames")
ZIPS_DIR = os.path.join(BASE_DIR, "zips")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(ZIPS_DIR, exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


@app.get("/")
def health():
    return {"status": "ok"}


def get_video_duration(video_path: str) -> float:
    result = subprocess.run(
        [
            FFMPEG_PATH,
            "-i", video_path
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    for line in result.stderr.splitlines():
        if "Duration" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = time_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

    raise RuntimeError("Could not read video duration")


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    screenshot_count: int = Form(...),
    image_format: str = Form(...)
):
    uid = str(uuid.uuid4())

    video_path = os.path.join(UPLOADS_DIR, f"{uid}_{file.filename}")
    frame_dir = os.path.join(FRAMES_DIR, uid)
    zip_path = os.path.join(ZIPS_DIR, f"{uid}.zip")

    os.makedirs(frame_dir, exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(await file.read())

    duration = get_video_duration(video_path)
    step = duration / screenshot_count

    for i in range(screenshot_count):
        timestamp = step * i
        output_path = os.path.join(
            frame_dir,
            f"screenshot_{i + 1}.{image_format}"
        )

        subprocess.run(
            [
                FFMPEG_PATH,
                "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                output_path
            ],
            check=True
        )

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(frame_dir):
            zipf.write(
                os.path.join(frame_dir, filename),
                arcname=filename
            )

    return JSONResponse({
        "message": "Screenshots generated successfully",
        "download_url": f"/download/{uid}.zip"
    })


@app.get("/download/{filename}")
def download(filename: str):
    file_path = os.path.join(ZIPS_DIR, filename)

    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(
        file_path,
        media_type="application/zip",
        filename=filename
    )
