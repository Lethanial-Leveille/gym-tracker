from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.db_models import Workout as WorkoutDB

app = FastAPI(title="Gym Tracker")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WorkoutCreate(BaseModel):
    title: str
    duration_minutes: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}


@app.get("/workouts")
def get_workouts(db: Session = Depends(get_db)):
    return db.query(WorkoutDB).all()


@app.post("/workouts")
def create_workout(workout: WorkoutCreate, db: Session = Depends(get_db)):
    new_workout = WorkoutDB(
        title=workout.title,
        duration_minutes=workout.duration_minutes
    )

    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)

    return new_workout

@app.put("/workouts/{workout_id}")
def update_workout(workout_id: int, updated: WorkoutCreate, db: Session = Depends(get_db)):
    workout = db.query(WorkoutDB).filter(WorkoutDB.id == workout_id).first()
    if not workout:
        return {"error": "Workout not found"}

    workout.title = updated.title
    workout.duration_minutes = updated.duration_minutes
    db.commit()
    db.refresh(workout)

    return workout

@app.delete("/workouts/{workout_id}")
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(WorkoutDB).filter(WorkoutDB.id == workout_id).first()

    if not workout:
        return {"error": "Workout not found"}

    db.delete(workout)
    db.commit()

    return {"message": "Workout deleted successfully"}
