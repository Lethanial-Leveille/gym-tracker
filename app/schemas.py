from datetime import datetime
from pydantic import BaseModel


# =========================
# Sets
# =========================
class SetEntryCreate(BaseModel):
    reps: int
    weight: int | None = None


class SetEntryUpdate(BaseModel):
    reps: int | None = None
    weight: int | None = None


class SetEntryResponse(BaseModel):
    id: int
    set_number: int
    reps: int
    weight: int | None = None

    class Config:
        from_attributes = True


# =========================
# Exercises
# =========================
class ExerciseCreate(BaseModel):
    name: str
    primary_muscle: str | None = None
    secondary_muscles: str | None = None
    classification: str | None = None
    notes: str | None = None


class ExerciseResponse(BaseModel):
    id: int
    name: str
    primary_muscle: str | None = None
    secondary_muscles: str | None = None
    classification: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True


class ExerciseStatsResponse(BaseModel):
    exercise_id: int
    last_weight: int | None = None
    best_weight: int | None = None

    class Config:
        from_attributes = True


# =========================
# Workouts (plan)
# =========================
class WorkoutCreate(BaseModel):
    title: str
    # allow creating a workout without knowing duration yet
    duration_minutes: int = 0


class WorkoutResponse(BaseModel):
    id: int
    title: str
    duration_minutes: int

    class Config:
        from_attributes = True


class WorkoutsListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[WorkoutResponse]


# =========================
# WorkoutExercise (plan item)
# =========================
class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order_index: int = 0
    notes: str | None = None


class WorkoutExerciseResponse(BaseModel):
    id: int
    order_index: int
    notes: str | None = None
    exercise: ExerciseResponse

    class Config:
        from_attributes = True


class WorkoutDetailResponse(WorkoutResponse):
    exercises: list[WorkoutExerciseResponse]

    class Config:
        from_attributes = True


# =========================
# Sessions
# =========================
class WorkoutSessionResponse(BaseModel):
    id: int
    workout_id: int
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None

    class Config:
        from_attributes = True


class FinishWorkoutRequest(BaseModel):
    duration_minutes: int | None = None


class SessionExerciseResponse(BaseModel):
    id: int
    order_index: int
    notes: str | None = None
    exercise: ExerciseResponse
    set_entries: list[SetEntryResponse] = []

    class Config:
        from_attributes = True


class WorkoutSessionDetailResponse(BaseModel):
    id: int
    workout_id: int
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    session_exercises: list[SessionExerciseResponse]

    class Config:
        from_attributes = True


# rebuild forward refs
WorkoutExerciseResponse.model_rebuild()
WorkoutDetailResponse.model_rebuild()
SessionExerciseResponse.model_rebuild()
WorkoutSessionDetailResponse.model_rebuild()