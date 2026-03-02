from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db_models import Workout, Exercise, WorkoutExercise, SetEntry

# ----- Workouts -----

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

    # filtering
    if title:
        query = query.filter(Workout.title.ilike(f"%{title}%"))

    if min_duration is not None:
        query = query.filter(Workout.duration_minutes >= min_duration)

    if max_duration is not None:
        query = query.filter(Workout.duration_minutes <= max_duration)

    total = query.count()

    # pagination
    items = (
        query.order_by(Workout.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"total": total, "skip": skip, "limit": limit, "items": items}


def get_workout(db: Session, workout_id: int, user_id: int):
    return db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == user_id
    ).first()


def create_workout(db: Session, title: str, duration_minutes: int, user_id: int):
    new_workout = Workout(
        title=title,
        duration_minutes=duration_minutes,
        user_id=user_id
    )
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    return new_workout


def update_workout(db: Session, workout_id: int, title: str, duration_minutes: int, user_id: int):
    workout = get_workout(db, workout_id, user_id)
    if not workout:
        return None

    workout.title = title
    workout.duration_minutes = duration_minutes

    db.commit()
    db.refresh(workout)
    return workout


def delete_workout(db: Session, workout_id: int, user_id: int) -> bool:
    workout = get_workout(db, workout_id, user_id)
    if not workout:
        return False

    db.delete(workout)
    db.commit()
    return True

# ----- Exercises -----

def create_exercise(db: Session, name: str, primary_muscle: str | None, secondary_muscles: str | None,
                    classification: str | None, notes: str | None):
    exercise = Exercise(
        name=name,
        primary_muscle=primary_muscle,
        secondary_muscles=secondary_muscles,
        classification=classification,
        notes=notes
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def list_exercises(db: Session, skip: int = 0, limit: int = 20, q: str | None = None,
                   primary_muscle: str | None = None, classification: str | None = None):
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


# ----- Link exercise into workout -----

def add_exercise_to_workout(
    db: Session,
    workout_id: int,
    user_id: int,
    exercise_id: int,
    order_index: int,
    notes: str | None
):
    workout = db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()
    if not workout:
        return None

    exercise = get_exercise(db, exercise_id)
    if not exercise:
        return "exercise_not_found"

    we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        order_index=order_index,
        notes=notes
    )
    db.add(we)
    db.commit()
    db.refresh(we)
    return we


def get_workout_detail(db: Session, workout_id: int, user_id: int):
    workout = db.query(Workout).filter(Workout.id == workout_id, Workout.user_id == user_id).first()
    if not workout:
        return None

    # order the join rows
    workout.exercises.sort(key=lambda x: x.order_index)
    return workout

# ----- Sets -----

def add_set_entry(
    db: Session,
    workout_exercise_id: int,
    reps: int,
    weight: int | None,
    user_id: int
):
    # Make sure the workout_exercise exists and belongs to this user
    we = (
        db.query(WorkoutExercise)
        .join(Workout, WorkoutExercise.workout_id == Workout.id)
        .filter(
            WorkoutExercise.id == workout_exercise_id,
            Workout.user_id == user_id
        )
        .first()
    )
    if not we:
        return None

    # auto set_number = max + 1
    current_max = (
        db.query(func.coalesce(func.max(SetEntry.set_number), 0))
        .filter(SetEntry.workout_exercise_id == workout_exercise_id)
        .scalar()
    )
    next_set_number = current_max + 1

    entry = SetEntry(
        workout_exercise_id=workout_exercise_id,
        set_number=next_set_number,
        reps=reps,
        weight=weight
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_set_entries(
    db: Session,
    workout_exercise_id: int,
    user_id: int
):
    # Same ownership check
    we = (
        db.query(WorkoutExercise)
        .join(Workout, WorkoutExercise.workout_id == Workout.id)
        .filter(
            WorkoutExercise.id == workout_exercise_id,
            Workout.user_id == user_id
        )
        .first()
    )
    if not we:
        return None

    items = (
        db.query(SetEntry)
        .filter(SetEntry.workout_exercise_id == workout_exercise_id)
        .order_by(SetEntry.set_number.asc())
        .all()
    )
    return items