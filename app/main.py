import os
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from alembic import command
from alembic.config import Config

from app import crud, schemas
from app.routers.auth import router as auth_router
from app.deps import (
    get_db,
    get_current_user_id,
    require_admin,
    get_current_user,
)
from app.db_models import (
    Workout,
    WorkoutExercise,
    WorkoutSession,
    SessionExercise,
    SetEntry,
)

# -------------------------
# Startup helpers
# -------------------------
def run_migrations():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("STARTUP: no DATABASE_URL, skipping migrations")
        return

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def run_seed() -> int:
    if not os.getenv("DATABASE_URL"):
        print("STARTUP: no DATABASE_URL, skipping seed")
        return 0
    from app.scripts.seed_exercises import seed_exercises
    return seed_exercises()


# -------------------------
# App
# -------------------------
app = FastAPI(title="Gym Tracker")
app.include_router(auth_router)

# CORS
origins_env = os.getenv("CORS_ORIGINS", "").strip()
if origins_env:
    origins_list = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    origins_list = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    print("STARTUP: running migrations + seed")
    run_migrations()
    created = run_seed()
    print(f"STARTUP: seed done, created={created}")


# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Welcome to the Gym Tracker API!"}


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
    result = crud.delete_workout(db, workout_id, user_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Workout not found")

    if result == "has_sessions":
        raise HTTPException(
            status_code=409,
            detail="Can't delete this workout because it has session history. Delete the sessions first (or keep it as history).",
        )

    return {"message": "Workout deleted successfully"}


# =========================
# Exercises (library)
# =========================
@app.post("/exercises", response_model=schemas.ExerciseResponse, status_code=201)
def create_exercise(
    ex: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    return crud.create_exercise(
        db,
        ex.name,
        ex.primary_muscle,
        ex.secondary_muscles,
        ex.classification,
        ex.notes,
    )


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


@app.patch("/exercises/{exercise_id}", response_model=schemas.ExerciseResponse)
def patch_exercise(
    exercise_id: int,
    payload: schemas.ExerciseUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided")

    ex = crud.update_exercise(db=db, exercise_id=exercise_id, updates=updates)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ex


@app.delete("/exercises/{exercise_id}")
def remove_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    ok = crud.delete_exercise(db=db, exercise_id=exercise_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {"message": "Exercise deleted"}


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
# Sessions (template-based start)
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
            detail={"message": "You already have an active session", "active_session_id": active.id},
        )

    return result


# ── FIX (Bug 1) ─────────────────────────────────────────────────────
# All routes below were MISSING.  crud.py had the logic but main.py
# never created HTTP endpoints for them.  The frontend was calling
# these URLs and getting 404 / 405 errors.
#
# ARCHITECTURE NOTE (for learning):
# FastAPI follows a common pattern: "routes → crud → models"
#   • Routes (this file):  handle HTTP, validate input, return responses
#   • CRUD (crud.py):      business logic, DB queries
#   • Models (db_models):  table definitions
# If any layer is missing, the chain breaks.  That's what happened here.
# ─────────────────────────────────────────────────────────────────────


# =========================
# Sessions (blank / freestyle)
# =========================
@app.post("/sessions/start", response_model=schemas.WorkoutSessionResponse, status_code=201)
def start_blank_session(
    payload: schemas.StartSessionRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Start a freestyle session (no template).  The frontend calls this
    from SessionPage when the user types a name and hits Start."""
    result = crud.start_blank_session(db, user_id, payload.title)

    if result == "active_session_exists":
        active = crud.get_active_session(db, user_id)
        raise HTTPException(
            status_code=409,
            detail={"message": "You already have an active session", "active_session_id": active.id},
        )

    return result


@app.patch("/sessions/{session_id}/title", response_model=schemas.WorkoutSessionResponse)
def update_session_title(
    session_id: int,
    payload: schemas.UpdateSessionTitleRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Rename an active session.  Frontend calls this from the title
    input + 'Save name' button on SessionPage."""
    session = crud.update_session_title(db, session_id, user_id, payload.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# =========================
# Add exercise to a live session
# =========================
@app.post(
    "/sessions/{session_id}/exercises",
    response_model=schemas.SessionExerciseResponse,
    status_code=201,
)
def add_exercise_to_session(
    session_id: int,
    payload: schemas.AddSessionExerciseRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Search for an exercise, then add it to the current session.
    Frontend calls this when the user taps 'Add' next to a search result."""
    result = crud.add_exercise_to_session(
        db=db,
        session_id=session_id,
        user_id=user_id,
        exercise_id=payload.exercise_id,
        order_index=payload.order_index,
        notes=payload.notes,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if result == "exercise_not_found":
        raise HTTPException(status_code=404, detail="Exercise not found")

    return result


# =========================
# Sets (log reps & weight inside a session)
# =========================
@app.post(
    "/session-exercises/{session_exercise_id}/sets",
    response_model=schemas.SetEntryResponse,
    status_code=201,
)
def add_set(
    session_exercise_id: int,
    payload: schemas.SetEntryCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Log one set (reps + optional weight).  Frontend calls this when
    the user hits 'Add set' under an exercise in SessionPage."""
    result = crud.add_set_entry(db, session_exercise_id, payload.reps, payload.weight, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return result


@app.get(
    "/session-exercises/{session_exercise_id}/sets",
    response_model=list[schemas.SetEntryResponse],
)
def list_sets(
    session_exercise_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.list_set_entries(db, session_exercise_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return result


@app.put(
    "/session-exercises/{session_exercise_id}/sets/{set_entry_id}",
    response_model=schemas.SetEntryResponse,
)
def update_set(
    session_exercise_id: int,
    set_entry_id: int,
    payload: schemas.SetEntryUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.update_set_entry(
        db, session_exercise_id, set_entry_id, user_id,
        reps=payload.reps, weight=payload.weight,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    if result == "set_not_found":
        raise HTTPException(status_code=404, detail="Set not found")
    return result


@app.delete("/session-exercises/{session_exercise_id}/sets/{set_entry_id}")
def delete_set(
    session_exercise_id: int,
    set_entry_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.delete_set_entry(db, session_exercise_id, set_entry_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Set not found")
    return {"message": "Set deleted"}


@app.delete("/session-exercises/{session_exercise_id}/sets")
def clear_sets(
    session_exercise_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = crud.clear_set_entries(db, session_exercise_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session exercise not found")
    return {"message": "All sets cleared"}


# =========================
# Session lifecycle (existing routes, unchanged)
# =========================
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
# Admin: reset my data (safe deletes)
# =========================
@app.delete("/admin/reset-my-data")
def reset_my_data(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    session_ids = [
        sid for (sid,) in db.query(WorkoutSession.id)
        .filter(WorkoutSession.user_id == user.id)
        .all()
    ]

    if session_ids:
        se_ids = [
            seid for (seid,) in db.query(SessionExercise.id)
            .filter(SessionExercise.session_id.in_(session_ids))
            .all()
        ]

        if se_ids:
            db.query(SetEntry).filter(SetEntry.session_exercise_id.in_(se_ids)).delete(synchronize_session=False)
            db.query(SessionExercise).filter(SessionExercise.id.in_(se_ids)).delete(synchronize_session=False)

        db.query(WorkoutSession).filter(WorkoutSession.id.in_(session_ids)).delete(synchronize_session=False)

    workout_ids = [
        wid for (wid,) in db.query(Workout.id)
        .filter(Workout.user_id == user.id)
        .all()
    ]

    if workout_ids:
        db.query(WorkoutExercise).filter(WorkoutExercise.workout_id.in_(workout_ids)).delete(synchronize_session=False)
        db.query(Workout).filter(Workout.id.in_(workout_ids)).delete(synchronize_session=False)

    db.commit()
    return {"message": "Reset complete"}
