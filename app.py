from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
import zipfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRAMES_DIR = os.path.join(BASE_DIR, "frames")
ZIP_DIR = os.path.join(BASE_DIR, "zips")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(ZIP_DIR, exist_ok=True)

FFMPEG_PATH = "/usr/bin/ffmpeg"

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = Form(...),
    image_format: str = Form(...)
):
    uid = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_dir = os.path.join(FRAMES_DIR, uid)
    zip_path = os.path.join(ZIP_DIR, f"{uid}.zip")

    os.makedirs(output_dir, exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(await file.read())

    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        os.path.join(output_dir, f"shot_%03d.{image_format}")
    ]

    subprocess.run(cmd, check=True)

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for img in os.listdir(output_dir):
            zipf.write(os.path.join(output_dir, img), img)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{uid}.zip"
    }

@app.get("/download/{zip_name}")
def download(zip_name: str):
    return FileResponse(os.path.join(ZIP_DIR, zip_name), filename=zip_name)
