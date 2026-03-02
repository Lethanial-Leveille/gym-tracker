from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)

    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan"
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
        cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)

    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)

    order_index = Column(Integer, nullable=False, default=0, index=True)
    notes = Column(Text, nullable=True)

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workouts")

    set_entries = relationship(
        "SetEntry",
        back_populates="workout_exercise",
        cascade="all, delete-orphan"
    )


class SetEntry(Base):
    __tablename__ = "set_entries"

    id = Column(Integer, primary_key=True, index=True)

    workout_exercise_id = Column(
        Integer,
        ForeignKey("workout_exercises.id"),
        nullable=False,
        index=True
    )

    set_number = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=True)

    workout_exercise = relationship("WorkoutExercise", back_populates="set_entries")