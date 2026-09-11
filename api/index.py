from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/health")
@app.get("/health")
@app.get("/api")
def health():
    return {"status": "ok", "message": "Garage VTV Backend is LIVE"}
