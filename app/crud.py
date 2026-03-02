from sqlalchemy.orm import Session
from app.db_models import Workout


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