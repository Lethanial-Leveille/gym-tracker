from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import crud, schemas

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}

# ----- Workout Functions -----

@app.get("/workouts", response_model=schemas.WorkoutsListResponse)
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


@app.post("/workouts", response_model=schemas.WorkoutResponse, status_code=201)
def create_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return crud.create_workout(db, workout.title, workout.duration_minutes, user_id)


@app.put("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
def update_workout(
    workout_id: int,
    updated: schemas.WorkoutCreate,
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


# ----- Exercises Library -----

@app.post("/exercises", response_model=schemas.ExerciseResponse, status_code=201)
def create_exercise(
    ex: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
):
    return crud.create_exercise(db, ex.name, ex.primary_muscle, ex.secondary_muscles, ex.classification, ex.notes)


@app.get("/exercises")
def list_exercises(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: str | None = None,
    primary_muscle: str | None = None,
    classification: str | None = None,
):
    total, items = crud.list_exercises(db, skip=skip, limit=limit, q=q,
                                      primary_muscle=primary_muscle, classification=classification)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


# ----- Attach exercise to a workout -----

@app.post("/workouts/{workout_id}/exercises", response_model=schemas.WorkoutExerciseResponse, status_code=201)
def add_exercise_to_workout(
    workout_id: int,
    payload: schemas.WorkoutExerciseCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    result = crud.add_exercise_to_workout(
        db=db,
        workout_id=workout_id,
        user_id=user_id,
        exercise_id=payload.exercise_id,
        sets=payload.sets,
        reps=payload.reps,
        weight=payload.weight,
        order_index=payload.order_index,
        notes=payload.notes,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    if result == "exercise_not_found":
        raise HTTPException(status_code=404, detail="Exercise not found")

    return result


@app.get("/workouts/{workout_id}", response_model=schemas.WorkoutDetailResponse)
def get_workout_detail(
    workout_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    workout = crud.get_workout_detail(db, workout_id, user_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout