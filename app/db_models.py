from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)

    # link to workout_exercises rows
    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, index=True)

    # Optional fields I might grow later
    primary_muscle = Column(String, nullable=True, index=True)
    secondary_muscles = Column(String, nullable=True)  # simple comma string for now
    classification = Column(String, nullable=True, index=True)  # weighted, bodyweight, machine, etc
    notes = Column(Text, nullable=True)

    # link to workout_exercises rows
    workouts = relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)

    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)

    # “log” fields for this exercise in THIS workout
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)  # keep int for now, can change later
    order_index = Column(Integer, nullable=False, default=0, index=True)
    notes = Column(Text, nullable=True)

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workouts")
