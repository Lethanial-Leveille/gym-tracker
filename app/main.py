from fastapi import FastAPI

app = FastAPI(title="Gym Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}