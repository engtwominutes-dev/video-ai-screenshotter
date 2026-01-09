from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import shutil
import subprocess
import uuid

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


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = 5,
    image_format: str = "jpg"
):
    video_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    output_dir = os.path.join(FRAMES_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        os.path.join(output_dir, f"frame_%03d.{image_format}")
    ]

    subprocess.run(cmd, check=True)

    zip_path = os.path.join(ZIP_DIR, f"{video_id}.zip")
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", output_dir)

    return {
        "message": "Screenshots created",
        "download_url": f"/download/{video_id}.zip"
    }


@app.get("/download/{filename}")
def download(filename: str):
    file_path = os.path.join(ZIP_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, filename=filename)
