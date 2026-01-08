from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import uuid
import zipfile
import shutil

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRAMES_DIR = os.path.join(BASE_DIR, "frames")
ZIPS_DIR = os.path.join(BASE_DIR, "zips")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(ZIPS_DIR, exist_ok=True)


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
    zip_path = os.path.join(ZIPS_DIR, f"{job_id}.zip")

    os.makedirs(frame_path, exist_ok=True)

    # Save uploaded file
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        f"{frame_path}/frame_%03d.{image_format}"
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "FFmpeg failed", "details": str(e)}
        )

    # Zip screenshots
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_name in os.listdir(frame_path):
            zipf.write(
                os.path.join(frame_path, file_name),
                arcname=file_name
            )

    # Cleanup
    os.remove(video_path)
    shutil.rmtree(frame_path)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{job_id}"
    }


@app.get("/download/{job_id}")
def download_zip(job_id: str):
    zip_path = os.path.join(ZIPS_DIR, f"{job_id}.zip")

    if not os.path.exists(zip_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    return FileResponse(zip_path, filename=f"screenshots_{job_id}.zip")
