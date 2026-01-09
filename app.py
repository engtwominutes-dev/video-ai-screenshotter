import ffmpeg_static
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
import zipfile
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.getcwd()
UPLOADS = os.path.join(BASE, "uploads")
FRAMES = os.path.join(BASE, "frames")
ZIPS = os.path.join(BASE, "zips")

os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(ZIPS, exist_ok=True)

FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"

@app.get("/")
def health():
    return {"status": "ok"}

def get_duration(video_path):
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    result = subprocess.check_output(cmd)
    return float(json.loads(result)["format"]["duration"])

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    screenshot_count: int = Form(...),
    image_format: str = Form(...)
):
    uid = str(uuid.uuid4())
    video_path = os.path.join(UPLOADS, f"{uid}_{file.filename}")
    out_dir = os.path.join(FRAMES, uid)
    zip_path = os.path.join(ZIPS, f"{uid}.zip")

    os.makedirs(out_dir, exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(await file.read())

    duration = get_duration(video_path)
    interval = duration / screenshot_count

    for i in range(screenshot_count):
        timestamp = interval * i
        output = os.path.join(out_dir, f"shot_{i+1}.{image_format}")

        subprocess.run([
            FFMPEG,
            "-ss", str(timestamp),
            "-i", video_path,
            "-frames:v", "1",
            output
        ], check=True)

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in os.listdir(out_dir):
            zipf.write(os.path.join(out_dir, f), f)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{uid}.zip"
    }

@app.get("/download/{name}")
def download(name: str):
    return FileResponse(os.path.join(ZIPS, name), filename=name)
