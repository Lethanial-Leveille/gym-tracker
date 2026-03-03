import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

from app.database import SessionLocal
from app.db_models import Exercise

DEFAULT_EXERCISES = [
    # Push
    {"name": "Bench Press", "primary_muscle": "chest", "secondary_muscles": "triceps,front_delts", "classification": "compound", "notes": None},
    {"name": "Incline Dumbbell Press", "primary_muscle": "chest", "secondary_muscles": "triceps,front_delts", "classification": "compound", "notes": None},
    {"name": "Overhead Press", "primary_muscle": "shoulders", "secondary_muscles": "triceps,upper_chest", "classification": "compound", "notes": None},
    {"name": "Lateral Raise", "primary_muscle": "shoulders", "secondary_muscles": None, "classification": "isolation", "notes": None},
    {"name": "Tricep Pushdown", "primary_muscle": "triceps", "secondary_muscles": None, "classification": "isolation", "notes": None},

    # Pull
    {"name": "Pull-Up", "primary_muscle": "lats", "secondary_muscles": "biceps,upper_back", "classification": "compound", "notes": None},
    {"name": "Lat Pulldown", "primary_muscle": "lats", "secondary_muscles": "biceps,upper_back", "classification": "compound", "notes": None},
    {"name": "Barbell Row", "primary_muscle": "upper_back", "secondary_muscles": "lats,biceps", "classification": "compound", "notes": None},
    {"name": "Seated Cable Row", "primary_muscle": "upper_back", "secondary_muscles": "lats,biceps", "classification": "compound", "notes": None},
    {"name": "Bicep Curl", "primary_muscle": "biceps", "secondary_muscles": None, "classification": "isolation", "notes": None},

    # Legs
    {"name": "Back Squat", "primary_muscle": "quads", "secondary_muscles": "glutes,core", "classification": "compound", "notes": None},
    {"name": "Trap Bar Deadlift", "primary_muscle": "glutes", "secondary_muscles": "quads,hamstrings,back", "classification": "compound", "notes": None},
    {"name": "Romanian Deadlift", "primary_muscle": "hamstrings", "secondary_muscles": "glutes,back", "classification": "compound", "notes": None},
    {"name": "Walking Lunge", "primary_muscle": "quads", "secondary_muscles": "glutes,hamstrings", "classification": "compound", "notes": None},
    {"name": "Calf Raise", "primary_muscle": "calves", "secondary_muscles": None, "classification": "isolation", "notes": None},
]

def seed_exercises():
    db = SessionLocal()
    try:
        created = 0
        for item in DEFAULT_EXERCISES:
            exists = db.query(Exercise).filter(Exercise.name == item["name"]).first()
            if exists:
                continue
            db.add(Exercise(**item))
            created += 1

        db.commit()
        print(f"Seed complete. Created {created} exercises.")
        return created
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()