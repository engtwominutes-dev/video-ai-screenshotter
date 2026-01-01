from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "backend running"}
@app.get("/health")
def health():
    return {"health": "ok"}
from fastapi import UploadFile, File

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "type": file.content_type
    }

