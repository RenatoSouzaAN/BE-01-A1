from datetime import datetime
import sqlite3

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

DB_PATH = "tasks.db"

app = FastAPI(
    title="Task API",
    description="SQLite to-do list CRUD API (AI rematch A2 version).",
    version="2.0",
)


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


SEED_TASKS: list[dict] = [
    {"id": 1, "title": "Task 1", "done": True},
    {"id": 2, "title": "Task 2", "done": False},
    {"id": 3, "title": "Task 3", "done": True},
]


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def row_to_task(row: tuple) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2]),
    }


def init_db() -> None:
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute("SELECT COUNT(*) FROM tasks")
    if cur.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        for task in SEED_TASKS:
            cur.execute(
                "INSERT INTO tasks (id, title, done, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (task["id"], task["title"], int(task["done"]), now, now),
            )
    con.commit()
    con.close()


init_db()


@app.get("/", summary="API info")
async def root():
    """Return API name, version, and available endpoints."""
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "sqlite3",
        "endpoints": [
            "/health",
            "/reset",
            "/tasks",
            "/tasks/stats",
            "/tasks/{id}",
        ],
    }


@app.get("/health", summary="Health check")
async def health():
    """Return a simple status payload used to verify the server is alive."""
    return {"status": "ok"}


@app.post("/reset", summary="Reset tasks")
async def reset_tasks():
    """Delete all tasks and restore the original three seed tasks."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM tasks")
    cur.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
    now = datetime.now().isoformat()
    for task in SEED_TASKS:
        cur.execute(
            "INSERT INTO tasks (id, title, done, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (task["id"], task["title"], int(task["done"]), now, now),
        )
    con.commit()
    con.close()
    return {"message": "Tasks list reset successfully."}


@app.get("/tasks", summary="List tasks")
async def list_tasks(done: bool | None = None, search: str | None = None):
    """List all tasks, optionally filtered by done status and/or title search."""
    con = get_connection()
    cur = con.cursor()

    clauses: list[str] = []
    params: list = []

    if done is not None:
        clauses.append("done = ?")
        params.append(int(done))

    if search is not None:
        clauses.append("LOWER(title) LIKE LOWER(?)")
        params.append(f"%{search}%")

    query = "SELECT id, title, done, created_at, updated_at FROM tasks"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    cur.execute(query, params)
    rows = cur.fetchall()
    con.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/stats", summary="Task stats")
async def task_stats():
    """Return total, done, and pending task counts from the database."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), SUM(done), SUM(CASE WHEN done = 0 THEN 1 ELSE 0 END) FROM tasks")
    total, done_count, pending = cur.fetchone()
    con.close()
    return {
        "total": total or 0,
        "done": done_count or 0,
        "pending": pending or 0,
    }


@app.get("/tasks/{task_id}", summary="Get task")
async def get_task(task_id: int):
    """Return a single task by ID, or 404 if it does not exist."""
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cur.fetchone()
    con.close()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    return row_to_task(row)


@app.post("/tasks", status_code=201, summary="Create task")
async def create_task(payload: TaskCreate):
    """Create a new task with done=false and current timestamps."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required."})

    now = datetime.now().isoformat()
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (payload.title.strip(), 0, now, now),
    )
    con.commit()
    new_id = cur.lastrowid
    cur.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (new_id,),
    )
    row = cur.fetchone()
    con.close()
    return row_to_task(row)


@app.put("/tasks/{task_id}", summary="Update task")
async def update_task(task_id: int, payload: TaskUpdate):
    """Update title and/or done for an existing task; touches updated_at."""
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "At least one field to update is required."},
        )
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title cannot be empty."})

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cur.fetchone()
    if row is None:
        con.close()
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})

    title = payload.title.strip() if payload.title is not None else row[1]
    done = int(payload.done) if payload.done is not None else row[2]
    now = datetime.now().isoformat()

    cur.execute(
        "UPDATE tasks SET title = ?, done = ?, updated_at = ? WHERE id = ?",
        (title, done, now, task_id),
    )
    con.commit()
    cur.execute(
        "SELECT id, title, done, created_at, updated_at FROM tasks WHERE id = ?",
        (task_id,),
    )
    updated = cur.fetchone()
    con.close()
    return row_to_task(updated)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete task")
async def delete_task(task_id: int):
    """Delete a task by ID. Returns 204 with an empty body on success."""
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    con.commit()
    deleted = cur.rowcount
    con.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    return Response(status_code=204)
