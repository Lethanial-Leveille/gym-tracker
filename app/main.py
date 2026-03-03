from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.auth import create_access_token, decode_access_token
from app.db_models import User
from app.database import Base, engine, SessionLocal
from app import crud, schemas

app = FastAPI(title="Gym Tracker")


# ---------- Dependencies ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    return user.id


# ---------- Health ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}



@app.post("/auth/register", response_model=schemas.UserResponse, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return crud.create_user(db, payload.email, payload.password)


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}

# =========================
# Workouts (plan)
# =========================
@app.post("/workouts", response_model=schemas.WorkoutResponse, status_code=201)
def create_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return crud.create_workout(db, workout.title, workout.duration_minutes, user_id)


@app.get("/workouts", response_model=schemas.WorkoutsListResponse)
def list_workouts(
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


@app.get("/workouts/{workout_id}", response_model=schemas.WorkoutDetailResponse)
def get_workout_detail(
    workout_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    workout = crud.get_workout_detail(db, workout_id, user_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@app.put("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
def update_workout(
    workout_id: int,
    updated: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    workout = crud.update_workout(db, workout_id, updated.title, updated.duration_minutes, user_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@app.delete("/workouts/{workout_id}")
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    deleted = crud.delete_workout(db, workout_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"message": "Workout deleted successfully"}


# =========================
# Exercises (library)
# =========================
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
    total, items = crud.list_exercises(
        db=db,
        skip=skip,
        limit=limit,
        q=q,
        primary_muscle=primary_muscle,
        classification=classification,
    )
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@app.get("/exercises/{exercise_id}/stats", response_model=schemas.ExerciseStatsResponse)
def get_exercise_stats(
    exercise_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    ex = crud.get_exercise(db, exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return crud.get_exercise_stats(db=db, exercise_id=exercise_id, user_id=user_id)


# =========================
# Attach exercise to workout plan
# =========================
@app.post("/workouts/{workout_id}/exercises", response_model=schemas.WorkoutExerciseResponse, status_code=201)
def add_exercise_to_workout(
    workout_id: int,
    payload: schemas.WorkoutExerciseCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.add_exercise_to_workout(
        db=db,
        workout_id=workout_id,
        user_id=user_id,
        exercise_id=payload.exercise_id,
        order_index=payload.order_index,
        notes=payload.notes,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    if result == "exercise_not_found":
        raise HTTPException(status_code=404, detail="Exercise not found")

    return result


# =========================
# Sessions
# =========================
@app.post("/workouts/{workout_id}/start", response_model=schemas.WorkoutSessionResponse)
def start_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.start_workout_session(db, workout_id, user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Workout not found")

    if result == "active_session_exists":
        active = crud.get_active_session(db, user_id)
        raise HTTPException(
            status_code=409,
            detail={"message": "You already have an active session", "active_session_id": active.id}
        )

    return result

@app.get("/sessions/active", response_model=schemas.WorkoutSessionResponse | None)
def get_active_session(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return crud.get_active_session(db, user_id)

@app.post("/sessions/{session_id}/finish", response_model=schemas.WorkoutSessionResponse)
def finish_session(
    session_id: int,
    payload: schemas.FinishSessionRequest | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    duration_override = payload.duration_minutes if payload else None

    session = crud.finish_workout_session(
        db=db,
        session_id=session_id,
        user_id=user_id,
        duration_minutes_override=duration_override,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/sessions/active/finish", response_model=schemas.WorkoutSessionResponse)
def finish_active_session(
    payload: schemas.FinishSessionRequest | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    active = crud.get_active_session(db, user_id)
    if not active:
        raise HTTPException(status_code=404, detail="No active session")

    duration_override = payload.duration_minutes if payload else None
    finished = crud.finish_workout_session(
    db=db,
    session_id=active.id,
    user_id=user_id,
    duration_minutes_override=duration_override,
)
    return finished


@app.get("/sessions/{session_id}", response_model=schemas.WorkoutSessionDetailResponse)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    session = crud.get_workout_session_detail(db, session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# =========================
# Sets (session exercise)
# =========================
@app.post("/session-exercises/{session_exercise_id}/sets", response_model=schemas.SetEntryResponse, status_code=201)
def create_set_entry(
    session_exercise_id: int,
    payload: schemas.SetEntryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    entry = crud.add_set_entry(
        db=db,
        session_exercise_id=session_exercise_id,
        reps=payload.reps,
        weight=payload.weight,
        user_id=user_id,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return entry


@app.get("/session-exercises/{session_exercise_id}/sets", response_model=list[schemas.SetEntryResponse])
def list_sets(
    session_exercise_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    items = crud.list_set_entries(db=db, session_exercise_id=session_exercise_id, user_id=user_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return items


@app.patch("/session-exercises/{session_exercise_id}/sets/{set_entry_id}", response_model=schemas.SetEntryResponse)
def patch_set_entry(
    session_exercise_id: int,
    set_entry_id: int,
    payload: schemas.SetEntryUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    updated = crud.update_set_entry(
        db=db,
        session_exercise_id=session_exercise_id,
        set_entry_id=set_entry_id,
        user_id=user_id,
        reps=payload.reps,
        weight=payload.weight,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    if updated == "set_not_found":
        raise HTTPException(status_code=404, detail="Set entry not found")
    return updated


@app.delete("/session-exercises/{session_exercise_id}/sets/{set_entry_id}")
def delete_set_entry(
    session_exercise_id: int,
    set_entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    deleted = crud.delete_set_entry(
        db=db,
        session_exercise_id=session_exercise_id,
        set_entry_id=set_entry_id,
        user_id=user_id,
    )
    if deleted is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    if deleted is False:
        raise HTTPException(status_code=404, detail="Set entry not found")
    return {"message": "Set entry deleted"}


@app.delete("/session-exercises/{session_exercise_id}/sets")
def clear_sets(
    session_exercise_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    ok = crud.clear_set_entries(db=db, session_exercise_id=session_exercise_id, user_id=user_id)
    if ok is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return {"message": "All sets cleared"}
