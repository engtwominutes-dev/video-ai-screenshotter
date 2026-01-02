from fastapi import FastAPI, File, UploadFile
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"status": "backend running"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
