from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.get("/")
def root():
    return {"status": "backend running"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }
