from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import uuid

print("APP IMPORT STARTED")

app = FastAPI()

# CORS (needed for browser uploads)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = "uploads"
SCREENSHOT_DIR = "screenshots"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"status": "backend running"}

# ========= UPLOAD + SCREENSHOT GENERATION =========
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    screenshot_count: int = 5,
    image_format: str = "jpg"
):
    # Generate unique ID per upload
    video_id = str(uuid.uuid4())

    # Save uploaded video
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}_{file.filename}")
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Create screenshot output folder
    output_dir = os.path.join(SCREENSHOT_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)

    # FFmpeg output pattern
    output_pattern = os.path.join(output_dir, f"shot_%03d.{image_format}")

    # FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={screenshot_count}",
        output_pattern
    ]

    # Run FFmpeg
    subprocess.run(ffmpeg_cmd, check=True)

    return {
        "message": "Screenshots generated",
        "video_id": video_id,
        "screenshots": screenshot_count,
        "format": image_format
    }

# ========= LIST UPLOADED VIDEOS =========
@app.get("/files")
async def list_files():
    return {"files": os.listdir(UPLOAD_DIR)}

# ========= DOWNLOAD ORIGINAL VIDEO =========
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, filename=filename)

# ========= LIST SCREENSHOTS FOR A VIDEO =========
@app.get("/screenshots/{video_id}")
async def list_screenshots(video_id: str):
    path = os.path.join(SCREENSHOT_DIR, video_id)
    if not os.path.exists(path):
        return {"error": "No screenshots found"}
    return {"screenshots": os.listdir(path)}

# ========= DOWNLOAD A SINGLE SCREENSHOT =========
@app.get("/screenshots/{video_id}/{filename}")
async def download_screenshot(video_id: str, filename: str):
    file_path = os.path.join(SCREENSHOT_DIR, video_id, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, filename=filename)
