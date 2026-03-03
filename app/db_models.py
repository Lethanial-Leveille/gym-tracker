from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import text


from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_admin = Column(Boolean, nullable=False, server_default=text("false"))

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    # Store "last duration" or a default, sessions are the real source of truth
    duration_minutes = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, nullable=False, index=True)

    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)

    primary_muscle = Column(String, nullable=True, index=True)
    secondary_muscles = Column(String, nullable=True)
    classification = Column(String, nullable=True, index=True)
    notes = Column(Text, nullable=True)

    workouts = relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )


class WorkoutExercise(Base):
    """
    Links an Exercise into a Workout plan (template).
    """
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)

    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)

    order_index = Column(Integer, nullable=False, default=0, index=True)
    notes = Column(Text, nullable=True)

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workouts")


class WorkoutSession(Base):
    """
    A real workout run. Created when user presses Start.
    """
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Store computed minutes for convenience
    duration_minutes = Column(Integer, nullable=True)

    workout = relationship("Workout")
    session_exercises = relationship(
        "SessionExercise",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class SessionExercise(Base):
    """
    Snapshot of exercises for a particular session.
    This is cloned from WorkoutExercise at Start.
    """
    __tablename__ = "session_exercises"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("workout_sessions.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)

    order_index = Column(Integer, nullable=False, default=0, index=True)
    notes = Column(Text, nullable=True)

    planned_reps = Column(Integer, nullable=True)
    planned_weight = Column(Integer, nullable=True)

    session = relationship("WorkoutSession", back_populates="session_exercises")
    exercise = relationship("Exercise")

    set_entries = relationship(
        "SetEntry",
        back_populates="session_exercise",
        cascade="all, delete-orphan",
    )


class SetEntry(Base):
    __tablename__ = "set_entries"

    id = Column(Integer, primary_key=True, index=True)

    session_exercise_id = Column(
        Integer,
        ForeignKey("session_exercises.id"),
        nullable=False,
        index=True,
    )

    set_number = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=True)

    session_exercise = relationship("SessionExercise", back_populates="set_entries")