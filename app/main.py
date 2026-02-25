from fastapi import FastAPI

app = FastAPI(title="Gym Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}