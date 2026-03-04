from datetime import datetime
import math

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db_models import (
    Workout,
    Exercise,
    WorkoutExercise,
    WorkoutSession,
    SessionExercise,
    SetEntry,
    User,
)

from app.auth import hash_password, verify_password

# =========================
# Helpers
# =========================
def _get_workout_if_owned(db: Session, workout_id: int, user_id: int):
    return (
        db.query(Workout)
        .filter(Workout.id == workout_id, Workout.user_id == user_id)
        .first()
    )


def _get_session_if_owned(db: Session, session_id: int, user_id: int):
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
        .first()
    )


def _get_session_exercise_if_owned(db: Session, session_exercise_id: int, user_id: int):
    return (
        db.query(SessionExercise)
        .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
        .filter(SessionExercise.id == session_exercise_id, WorkoutSession.user_id == user_id)
        .first()
    )

def get_active_session(db: Session, user_id: int):
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == user_id, WorkoutSession.ended_at.is_(None))
        .order_by(WorkoutSession.started_at.desc())
        .first()
    )

# =========================
# Workouts (plan)
# =========================
def get_workouts(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    title: str | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
):
    query = db.query(Workout).filter(Workout.user_id == user_id)

    if title:
        query = query.filter(Workout.title.ilike(f"%{title}%"))
    if min_duration is not None:
        query = query.filter(Workout.duration_minutes >= min_duration)
    if max_duration is not None:
        query = query.filter(Workout.duration_minutes <= max_duration)

    total = query.count()
    items = (
        query.order_by(Workout.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"total": total, "skip": skip, "limit": limit, "items": items}


def get_workout_detail(db: Session, workout_id: int, user_id: int):
    workout = _get_workout_if_owned(db, workout_id, user_id)
    if not workout:
        return None

    workout.exercises.sort(key=lambda x: x.order_index)
    return workout


def create_workout(db: Session, title: str, duration_minutes: int, user_id: int):
    workout = Workout(title=title, duration_minutes=max(0, duration_minutes), user_id=user_id)
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def update_workout(db: Session, workout_id: int, title: str, duration_minutes: int, user_id: int):
    workout = _get_workout_if_owned(db, workout_id, user_id)
    if not workout:
        return None

    workout.title = title
    workout.duration_minutes = max(0, duration_minutes)

    db.commit()
    db.refresh(workout)
    return workout


def delete_workout(db, workout_id: int, user_id: int) -> str | bool:
    workout = (
        db.query(Workout)
        .filter(Workout.id == workout_id, Workout.user_id == user_id)
        .first()
    )
    if not workout:
        return False

    sessions_count = (
        db.query(func.count(WorkoutSession.id))
        .filter(WorkoutSession.workout_id == workout_id, WorkoutSession.user_id == user_id)
        .scalar()
    )

    if sessions_count and int(sessions_count) > 0:
        return "has_sessions"

    db.query(WorkoutExercise).filter(WorkoutExercise.workout_id == workout_id).delete()

    db.delete(workout)
    db.commit()
    return True


# =========================
# Exercises (library)
# =========================
def create_exercise(
    db: Session,
    name: str,
    primary_muscle: str | None,
    secondary_muscles: str | None,
    classification: str | None,
    notes: str | None,
):
    exercise = Exercise(
        name=name,
        primary_muscle=primary_muscle,
        secondary_muscles=secondary_muscles,
        classification=classification,
        notes=notes,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def list_exercises(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    q: str | None = None,
    primary_muscle: str | None = None,
    classification: str | None = None,
):
    query = db.query(Exercise)

    if q:
        query = query.filter(func.lower(Exercise.name).contains(q.lower()))
    if primary_muscle:
        query = query.filter(Exercise.primary_muscle == primary_muscle)
    if classification:
        query = query.filter(Exercise.classification == classification)

    total = query.count()
    items = query.order_by(Exercise.name.asc()).offset(skip).limit(limit).all()
    return total, items


def get_exercise(db: Session, exercise_id: int):
    return db.query(Exercise).filter(Exercise.id == exercise_id).first()

def update_exercise(
    db: Session,
    exercise_id: int,
    updates: dict,
):
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        return None

    allowed = {"name", "primary_muscle", "secondary_muscles", "classification", "notes"}
    for key, value in updates.items():
        if key in allowed:
            setattr(ex, key, value)

    db.commit()
    db.refresh(ex)
    return ex


def delete_exercise(db: Session, exercise_id: int) -> bool:
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        return False

    db.delete(ex)
    db.commit()
    return True


def get_exercise_stats(db: Session, exercise_id: int, user_id: int):
    best_weight = (
        db.query(func.max(SetEntry.weight))
        .select_from(SetEntry)
        .join(SessionExercise, SetEntry.session_exercise_id == SessionExercise.id)
        .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == user_id,
            SessionExercise.exercise_id == exercise_id,
            SetEntry.weight.isnot(None),
        )
        .scalar()
    )

    last_weight = (
        db.query(SetEntry.weight)
        .select_from(SetEntry)
        .join(SessionExercise, SetEntry.session_exercise_id == SessionExercise.id)
        .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == user_id,
            SessionExercise.exercise_id == exercise_id,
            SetEntry.weight.isnot(None),
        )
        .order_by(desc(WorkoutSession.started_at), desc(SetEntry.id))
        .limit(1)
        .scalar()
    )

    return {"exercise_id": exercise_id, "last_weight": last_weight, "best_weight": best_weight}


# =========================
# WorkoutExercises (plan items)
# =========================
def add_exercise_to_workout(
    db: Session,
    workout_id: int,
    user_id: int,
    exercise_id: int,
    order_index: int,
    notes: str | None,
):
    workout = _get_workout_if_owned(db, workout_id, user_id)
    if not workout:
        return None

    exercise = get_exercise(db, exercise_id)
    if not exercise:
        return "exercise_not_found"

    we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        order_index=order_index,
        notes=notes,
    )
    db.add(we)
    db.commit()
    db.refresh(we)
    return we


# =========================
# Sessions
# =========================
def start_workout_session(db: Session, workout_id: int, user_id: int):
    workout = _get_workout_if_owned(db, workout_id, user_id)
    if not workout:
        return None

    active = get_active_session(db, user_id)
    if active:
        return "active_session_exists"

    # ── FIX (Bug 3) ─────────────────────────────────────────────────
    # Previously: title was never set here, so it defaulted to "Workout"
    #             for every template-started session.
    # Fix:        Copy the workout template's title into the session.
    # Why:        The frontend displays session.title, so the user sees
    #             "Push A" instead of generic "Workout".
    # ────────────────────────────────────────────────────────────────
    session = WorkoutSession(
        user_id=user_id,
        workout_id=workout_id,
        title=workout.title,          # <-- THE FIX
        started_at=datetime.utcnow(),
        ended_at=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    plan_items = sorted(workout.exercises, key=lambda x: x.order_index)
    for we in plan_items:
        se = SessionExercise(
            session_id=session.id,
            exercise_id=we.exercise_id,
            order_index=we.order_index,
            notes=we.notes,
            planned_reps=None,
            planned_weight=None,
        )
        db.add(se)

    db.commit()
    db.refresh(session)
    return session


def finish_workout_session(db: Session, session_id: int, user_id: int, duration_minutes_override: int | None = None):
    session = _get_session_if_owned(db, session_id, user_id)
    if not session:
        return None

    if session.ended_at is None:
        session.ended_at = datetime.utcnow()

    if duration_minutes_override is not None:
        duration = max(0, duration_minutes_override)
    else:
        seconds = (session.ended_at - session.started_at).total_seconds()
        duration = max(0, int(math.ceil(seconds / 60)))

    session.duration_minutes = duration

    workout = db.query(Workout).filter(Workout.id == session.workout_id).first()
    if workout:
        workout.duration_minutes = duration

    db.commit()
    db.refresh(session)
    return session


def get_workout_session_detail(db: Session, session_id: int, user_id: int):
    session = _get_session_if_owned(db, session_id, user_id)
    if not session:
        return None

    session.session_exercises.sort(key=lambda x: x.order_index)
    return session


# ── NEW: list finished sessions (for History page) ──────
def list_sessions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
):
    """Return completed sessions (ended_at IS NOT NULL), newest first."""
    query = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.ended_at.isnot(None),
    )
    total = query.count()
    items = (
        query.order_by(WorkoutSession.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": total, "skip": skip, "limit": limit, "items": items}

def start_blank_session(db: Session, user_id: int, title: str):
    active = get_active_session(db, user_id)
    if active:
        return "active_session_exists"

    session = WorkoutSession(
        user_id=user_id,
        workout_id=None,
        title=title.strip() or "Workout",
        started_at=datetime.utcnow(),
        ended_at=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session_title(db: Session, session_id: int, user_id: int, title: str):
    session = _get_session_if_owned(db, session_id, user_id)
    if not session:
        return None

    session.title = title.strip() or session.title
    db.commit()
    db.refresh(session)
    return session


def add_exercise_to_session(db: Session, session_id: int, user_id: int, exercise_id: int, order_index: int | None, notes: str | None):
    session = _get_session_if_owned(db, session_id, user_id)
    if not session:
        return None

    ex = get_exercise(db, exercise_id)
    if not ex:
        return "exercise_not_found"

    if order_index is None:
        current_max = (
            db.query(func.coalesce(func.max(SessionExercise.order_index), -1))
            .filter(SessionExercise.session_id == session_id)
            .scalar()
        )
        order_index = int(current_max) + 1

    se = SessionExercise(
        session_id=session.id,
        exercise_id=exercise_id,
        order_index=order_index,
        notes=notes,
        planned_reps=None,
        planned_weight=None,
    )
    db.add(se)
    db.commit()
    db.refresh(se)
    return se

# =========================
# Sets (session-based)
# =========================
def add_set_entry(db: Session, session_exercise_id: int, reps: int, weight: int | None, user_id: int):
    se = _get_session_exercise_if_owned(db, session_exercise_id, user_id)
    if not se:
        return None

    current_max = (
        db.query(func.coalesce(func.max(SetEntry.set_number), 0))
        .filter(SetEntry.session_exercise_id == session_exercise_id)
        .scalar()
    )
    next_set_number = int(current_max) + 1

    entry = SetEntry(
        session_exercise_id=session_exercise_id,
        set_number=next_set_number,
        reps=reps,
        weight=weight,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_set_entries(db: Session, session_exercise_id: int, user_id: int):
    se = _get_session_exercise_if_owned(db, session_exercise_id, user_id)
    if not se:
        return None

    return (
        db.query(SetEntry)
        .filter(SetEntry.session_exercise_id == session_exercise_id)
        .order_by(SetEntry.set_number.asc())
        .all()
    )


def update_set_entry(db: Session, session_exercise_id: int, set_entry_id: int, user_id: int, reps: int | None = None, weight: int | None = None):
    se = _get_session_exercise_if_owned(db, session_exercise_id, user_id)
    if not se:
        return None

    entry = (
        db.query(SetEntry)
        .filter(SetEntry.id == set_entry_id, SetEntry.session_exercise_id == session_exercise_id)
        .first()
    )
    if not entry:
        return "set_not_found"

    if reps is not None:
        entry.reps = reps
    if weight is not None:
        entry.weight = weight

    db.commit()
    db.refresh(entry)
    return entry


def delete_set_entry(db: Session, session_exercise_id: int, set_entry_id: int, user_id: int) -> bool | None:
    se = _get_session_exercise_if_owned(db, session_exercise_id, user_id)
    if not se:
        return None

    entry = (
        db.query(SetEntry)
        .filter(SetEntry.id == set_entry_id, SetEntry.session_exercise_id == session_exercise_id)
        .first()
    )
    if not entry:
        return False

    db.delete(entry)
    db.commit()
    return True


def clear_set_entries(db: Session, session_exercise_id: int, user_id: int) -> bool | None:
    se = _get_session_exercise_if_owned(db, session_exercise_id, user_id)
    if not se:
        return None

    db.query(SetEntry).filter(SetEntry.session_exercise_id == session_exercise_id).delete()
    db.commit()
    return True

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user