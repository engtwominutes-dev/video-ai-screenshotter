from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import subprocess
import zipfile
import uuid
import shutil

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
    uid = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{uid}_{file.filename}")
    output_dir = os.path.join(FRAMES_DIR, uid)
    zip_path = os.path.join(ZIP_DIR, f"{uid}.zip")

    os.makedirs(output_dir, exist_ok=True)

    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        os.path.join(output_dir, f"frame_%03d.{image_format}")
    ]

    subprocess.run(cmd, check=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in os.listdir(output_dir):
            zipf.write(os.path.join(output_dir, f), f)

    shutil.rmtree(output_dir)
    os.remove(video_path)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{uid}.zip"
    }

@app.get("/download/{zip_name}")
def download_zip(zip_name: str):
    file_path = os.path.join(ZIP_DIR, zip_name)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return FileResponse(file_path, filename=zip_name)
