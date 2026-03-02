from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.db_models import Workout as WorkoutDB
from app import crud

app = FastAPI(title="Gym Tracker")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id():
    return 1  # Placeholder for user authentication logic


class WorkoutCreate(BaseModel):
    title: str
    duration_minutes: int

class WorkoutResponse(BaseModel):
    id: int
    title: str
    duration_minutes: int

    class Config:
        from_attributes = True

class WorkoutsListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[WorkoutResponse]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}


@app.get("/workouts", response_model=WorkoutsListResponse)
def get_workouts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    title: str | None = None,
    min_duration: int | None = Query(None, ge=0),
    max_duration: int | None = Query(None, ge=0),
):
    return crud.get_workouts(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        title=title,
        min_duration=min_duration,
        max_duration=max_duration,
    )


@app.post("/workouts", response_model=WorkoutResponse, status_code=201)
def create_workout(
    workout: WorkoutCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return crud.create_workout(db, workout.title, workout.duration_minutes, user_id)

@app.put("/workouts/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: int,
    updated: WorkoutCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    workout = crud.update_workout(db, workout_id, updated.title, updated.duration_minutes, user_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout

@app.delete("/workouts/{workout_id}")
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    deleted = crud.delete_workout(db, workout_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout deleted successfully"}
