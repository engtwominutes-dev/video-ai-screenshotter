from fastapi import FastAPI, UploadFile, File, Form
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
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = Form(...),
    image_format: str = Form(...)
):
    try:
        job_id = str(uuid.uuid4())
        video_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        frames_path = os.path.join(FRAMES_DIR, job_id)
        zip_path = os.path.join(ZIP_DIR, f"{job_id}.zip")

        os.makedirs(frames_path, exist_ok=True)

        with open(video_path, "wb") as f:
            f.write(await file.read())

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={screenshot_count}",
            os.path.join(frames_path, f"frame_%03d.{image_format}")
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            return JSONResponse(
                status_code=400,
                content={"error": "FFmpeg failed", "details": result.stderr.decode()}
            )

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for filename in os.listdir(frames_path):
                zipf.write(
                    os.path.join(frames_path, filename),
                    arcname=filename
                )

        return {
            "message": "Success",
            "download_url": f"/download/{job_id}.zip"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/download/{zip_name}")
def download(zip_name: str):
    path = os.path.join(ZIP_DIR, zip_name)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(path, filename=zip_name)
