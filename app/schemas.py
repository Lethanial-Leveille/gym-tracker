from pydantic import BaseModel


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


# ----- WorkoutExercise (adding exercises into workouts) -----

class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    sets: int | None = None
    reps: int | None = None
    weight: int | None = None
    order_index: int = 0
    notes: str | None = None


class WorkoutExerciseResponse(BaseModel):
    id: int
    order_index: int
    sets: int | None = None
    reps: int | None = None
    weight: int | None = None
    notes: str | None = None
    exercise: ExerciseResponse

    class Config:
        from_attributes = True


class WorkoutDetailResponse(WorkoutResponse):
    exercises: list[WorkoutExerciseResponse]