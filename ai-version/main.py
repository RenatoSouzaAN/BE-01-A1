from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    description="In-memory to-do list CRUD API (AI rematch version).",
    version="1.0",
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

tasks: list[dict] = [task.copy() for task in SEED_TASKS]


def _find_task(task_id: int) -> dict | None:
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def _next_id() -> int:
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


@app.get("/", summary="API info")
async def root():
    """Return API name, version, and available endpoints."""
    return {
        "name": "Task API",
        "version": "1.0",
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
    """Restore the in-memory task list to the original three seed tasks."""
    global tasks
    tasks = [task.copy() for task in SEED_TASKS]
    return {"message": "Tasks list reset successfully."}


@app.get("/tasks", summary="List tasks")
async def list_tasks(done: bool | None = None, search: str | None = None):
    """List all tasks, optionally filtered by done status and/or title search."""
    result = tasks
    if done is not None:
        result = [task for task in result if task["done"] is done]
    if search is not None:
        needle = search.lower()
        result = [task for task in result if needle in task["title"].lower()]
    return result


@app.get("/tasks/stats", summary="Task stats")
async def task_stats():
    """Return total, done, and pending task counts."""
    done_count = sum(1 for task in tasks if task["done"])
    return {
        "total": len(tasks),
        "done": done_count,
        "pending": len(tasks) - done_count,
    }


@app.get("/tasks/{task_id}", summary="Get task")
async def get_task(task_id: int):
    """Return a single task by ID, or 404 if it does not exist."""
    task = _find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    return task


@app.post("/tasks", status_code=201, summary="Create task")
async def create_task(payload: TaskCreate):
    """Create a new task with the next free ID and done=false."""
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title is required."})

    new_task = {"id": _next_id(), "title": payload.title.strip(), "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{task_id}", summary="Update task")
async def update_task(task_id: int, payload: TaskUpdate):
    """Update title and/or done for an existing task."""
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "At least one field to update is required."},
        )
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail={"error": "Title cannot be empty."})

    task = _find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})

    if payload.title is not None:
        task["title"] = payload.title.strip()
    if payload.done is not None:
        task["done"] = payload.done
    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete task")
async def delete_task(task_id: int):
    """Delete a task by ID. Returns 204 with an empty body on success."""
    task = _find_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"error": f"Task {task_id} not found"})
    tasks.remove(task)
    return Response(status_code=204)
