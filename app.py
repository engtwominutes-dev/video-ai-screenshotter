from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import subprocess
import zipfile

app = FastAPI()

# CORS FIX — EXPLICIT
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://video-ai-screenshotter-production.up.railway.app"
    ],
    allow_credentials=True,
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


@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return JSONResponse(status_code=200)


@app.get("/")
def root():
    return {"status": "backend running"}


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = 5,
    image_format: str = "jpg"
):
    video_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")

    with open(video_path, "wb") as f:
        f.write(await file.read())

    frames_path = os.path.join(FRAMES_DIR, video_id)
    os.makedirs(frames_path, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={screenshot_count}",
            os.path.join(frames_path, f"shot_%03d.{image_format}")
        ],
        check=True
    )

    zip_path = os.path.join(ZIPS_DIR, f"{video_id}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for name in os.listdir(frames_path):
            zipf.write(os.path.join(frames_path, name), arcname=name)

    return {
        "message": "Screenshots generated",
        "download_url": f"/download/{video_id}"
    }


@app.get("/download/{video_id}")
def download_zip(video_id: str):
    zip_path = os.path.join(ZIPS_DIR, f"{video_id}.zip")
    if not os.path.exists(zip_path):
        return JSONResponse({"error": "ZIP not found"}, status_code=404)
    return FileResponse(zip_path, filename=f"{video_id}.zip")
