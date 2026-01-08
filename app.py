from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
import subprocess
import zipfile
import uuid

app = FastAPI()

# CORS (this is correct and required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return {"status": "backend running"}

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = Form(...),
    image_format: str = Form(...)
):
    job_id = str(uuid.uuid4())

    video_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    frame_path = os.path.join(FRAMES_DIR, job_id)
    zip_path = os.path.join(ZIP_DIR, f"{job_id}.zip")

    os.makedirs(frame_path, exist_ok=True)

    # Save uploaded video
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Generate screenshots with FFmpeg
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        os.path.join(frame_path, f"frame_%03d.{image_format}")
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    # Zip screenshots
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(frame_path):
            full_path = os.path.join(frame_path, filename)
            zipf.write(full_path, arcname=filename)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{job_id}"
    }

@app.get("/download/{job_id}")
def download_zip(job_id: str):
    zip_path = os.path.join(ZIP_DIR, f"{job_id}.zip")
    if not os.path.exists(zip_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(zip_path, filename=f"{job_id}.zip")
