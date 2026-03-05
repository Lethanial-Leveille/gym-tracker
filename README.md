# 🏋️ Gym Tracker API

A RESTful API for tracking gym workouts, exercises, and personal progress. Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

> Part of the [Gym Tracker](https://github.com/Lethanial-Leveille) project — a full-stack fitness tracking app with a React frontend and FastAPI backend.

---

## Live Demo

**API Base URL:** [https://gym-tracker-api-96ij.onrender.com](https://gym-tracker-api-96ij.onrender.com)

**Interactive Docs:** [https://gym-tracker-api-96ij.onrender.com/docs](https://gym-tracker-api-96ij.onrender.com/docs) (Swagger UI)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Database | PostgreSQL (prod) / SQLite (dev) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Auth | JWT (python-jose) + Argon2/bcrypt password hashing |
| Validation | Pydantic v2 |
| Deployment | Render |

---

## Features

- **User Authentication** — Register, login, JWT-based session management
- **Workout Sessions** — Start, track, and finish freestyle workout sessions
- **Exercise Library** — 15+ pre-seeded exercises with muscle group classification
- **Set Logging** — Log reps and weight per exercise per session with full CRUD
- **Exercise Stats** — Track personal records (best weight) and last-used weight per exercise
- **Session History** — Paginated list of completed sessions with full detail
- **Admin Controls** — Admin-only exercise management and data reset

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new account |
| POST | `/auth/login` | Login (returns JWT) |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions/start` | Start a new freestyle session |
| GET | `/sessions/active` | Get current active session |
| GET | `/sessions/{id}` | Get session detail with exercises and sets |
| GET | `/sessions` | List completed sessions (paginated) |
| PATCH | `/sessions/{id}/title` | Rename a session |
| POST | `/sessions/{id}/finish` | End session and calculate duration |
| POST | `/sessions/{id}/exercises` | Add an exercise to a live session |

### Sets
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/session-exercises/{id}/sets` | Log a set (reps + weight) |
| GET | `/session-exercises/{id}/sets` | List sets for an exercise |
| PUT | `/session-exercises/{id}/sets/{set_id}` | Update a set |
| DELETE | `/session-exercises/{id}/sets/{set_id}` | Delete a set |

### Exercises
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/exercises` | Search/filter exercise library |
| GET | `/exercises/{id}/stats` | Get personal stats for an exercise |
| POST | `/exercises` | Create exercise (admin only) |
| PATCH | `/exercises/{id}` | Update exercise (admin only) |
| DELETE | `/exercises/{id}` | Delete exercise (admin only) |

---

## Project Structure

```
gym-tracker/
├── alembic/                # Database migrations
│   ├── versions/           # Migration scripts
│   └── env.py              # Alembic environment config
├── app/
│   ├── routers/
│   │   └── auth.py         # Auth endpoints (register, login)
│   ├── scripts/
│   │   └── seed_exercises.py  # Pre-seed exercise library
│   ├── auth.py             # JWT + password hashing utilities
│   ├── crud.py             # Business logic / DB queries
│   ├── database.py         # SQLAlchemy engine + session
│   ├── db_models.py        # Table definitions (User, Workout, Session, etc.)
│   ├── deps.py             # FastAPI dependencies (auth, DB session)
│   ├── main.py             # App factory + all route definitions
│   └── schemas.py          # Pydantic request/response models
├── .env                    # Environment variables (not committed)
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Python dependencies
└── runtime.txt             # Python version for Render
```

---

## Architecture

The app follows a three-layer pattern:

```
Routes (main.py)  →  CRUD (crud.py)  →  Models (db_models.py)
   HTTP layer         Business logic       Database tables
```

- **Routes** handle HTTP methods, validate input, and return responses
- **CRUD** contains all database queries and business logic
- **Models** define the database schema via SQLAlchemy ORM

Every route depends on `get_current_user_id` — a FastAPI dependency that extracts the user from the JWT token. This ensures all data is scoped to the authenticated user.

---

## Data Model

```
User
 └── WorkoutSession (many)
      ├── title, started_at, ended_at, duration_minutes
      └── SessionExercise (many)
           ├── exercise_id → Exercise
           ├── order_index
           └── SetEntry (many)
                ├── set_number, reps, weight

Exercise (shared library)
 ├── name, primary_muscle, secondary_muscles
 └── classification (compound / isolation)
```

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL (or use SQLite for dev)

### Setup

```bash
# Clone the repo
git clone https://github.com/Lethanial-Leveille/gym-tracker.git
cd gym-tracker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run migrations
alembic upgrade head

# Seed exercise library
python -m app.scripts.seed_exercises

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user@localhost:5432/gym_tracker` |
| `SECRET_KEY` | JWT signing secret | `your-secret-key-here` |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) | `http://localhost:5173,https://your-app.com` |

---

## Deployment (Render)

1. Create a new **Web Service** on Render
2. Connect your GitHub repo
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (`DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`)
6. Migrations and seeding run automatically on startup

---

## Roadmap

- [x] User auth (JWT + Argon2)
- [x] Freestyle sessions (no templates required)
- [x] Exercise library with search and filters
- [x] Set logging with reps and weight
- [x] Session history
- [x] Personal records per exercise
- [ ] Progress charts (weight over time)
- [ ] Rest timer between sets
- [ ] Body weight / measurements tracking
- [ ] Workout streak / calendar view

---

## Built By

**Lethanial Leveille** — Computer Engineering, University of Florida

- [GitHub](https://github.com/Lethanial-Leveille)
