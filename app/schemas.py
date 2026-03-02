from pydantic import BaseModel


# ----- Sets -----
class SetEntryCreate(BaseModel):
    reps: int
    weight: int | None = None


class SetEntryResponse(BaseModel):
    id: int
    set_number: int
    reps: int
    weight: int | None = None

    class Config:
        from_attributes = True


# ----- Exercise -----
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

# ----- Workout -----
class WorkoutCreate(BaseModel):
    title: str
    duration_minutes: int


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


# ----- WorkoutExercise (exercise inside a workout) -----
class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order_index: int = 0
    notes: str | None = None


class WorkoutExerciseResponse(BaseModel):
    id: int
    order_index: int
    notes: str | None = None
    exercise: ExerciseResponse
    set_entries: list["SetEntryResponse"]

    class Config:
        from_attributes = True


class WorkoutDetailResponse(WorkoutResponse):
    exercises: list[WorkoutExerciseResponse]

WorkoutExerciseResponse.model_rebuild()
WorkoutDetailResponse.model_rebuild()