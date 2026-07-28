import sqlite3
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic.main import BaseModel

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    done: bool

class TaskCreate(BaseModel):
    title: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

SEED_TASKS = [
    {"id": 1, "title": "Task 1", "done": True},
    {"id": 2, "title": "Task 2", "done": False},
    {"id": 3, "title": "Task 3", "done": True},
]

tasks = [task.copy() for task in SEED_TASKS]

def init_db():
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, done INTEGER)")
    
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    if count == 0:
        for task in SEED_TASKS:
            cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task["title"], task["done"]))
    con.commit()
    con.close()

init_db()

def row_to_task(row):
    return {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2]),
    }

@app.get("/")
async def root():
    """
    Root endpoint for the Task API.
    Returns a dictionary with the name, version, and endpoints of the API.
    """
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def health():
    """Health check endpoint.
    Returns a dictionary with the status of the API.
    """
    return {"status": "ok"}

@app.post("/reset")
async def reset_tasks_list():
    """Reset the tasks list."""
    global tasks
    tasks = [task.copy() for task in SEED_TASKS]
    return JSONResponse(status_code=200, content={"message": "Tasks list reset successfully."})

@app.get("/tasks")
async def get_tasks():
# async def get_tasks(done: bool | None = None, search: str | None = None):
    """List all tasks."""
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM tasks")
    tasks = cur.fetchall()
    # filtered_tasks = tasks
    # if done is not None:
    #     filtered_tasks = [task for task in filtered_tasks if task["done"] == done]
    # if search is not None:
    #     filtered_tasks = [task for task in filtered_tasks if search.lower() in task["title"].lower()]
    return [row_to_task(row) for row in tasks]

@app.get("/tasks/stats")
async def get_tasks_stats():
    """Get the statistics of the tasks."""
    return {
        "total": len(tasks),
        "done": sum(1 for task in tasks if task["done"]),
        "pending": sum(1 for task in tasks if not task["done"])
    }

@app.get("/tasks/{id}")
async def get_tasks_by_id(id: int):
    """Get a task by its ID."""
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    task = cur.fetchone()
    if task:
        return row_to_task(task)
    else:
        return JSONResponse(status_code=404,content={"error": f"Task {id} not found"})

@app.post("/tasks", status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task."""
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()
    new_task = None
    if not task.title:
        return JSONResponse(status_code=400, content={"error": "Title is required."})

    cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, False))
    con.commit()
    new_id = cur.lastrowid
    cur.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    new_task = cur.fetchone()
    con.close()

    return row_to_task(new_task)

@app.put("/tasks/{id}")
async def update_task(id: int, task: TaskUpdate):
    """Update a task by its ID."""
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()

    cur.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    currentValue = cur.fetchone()
    if task.title is None and task.done is None:
        return JSONResponse(status_code=400, content={"error": "At least one field to update is required."})

    if task.title is None:
        task.title = currentValue[1]
    if task.done is None:
        task.done = currentValue[2]

    cur.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (task.title, task.done, id))
    con.commit()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    updated_task = cur.fetchone()
    con.close()

    return row_to_task(updated_task)

@app.delete("/tasks/{id}", status_code=204)
async def delete_task_by_id(id: int):
    """Delete a task by its ID."""
    con = sqlite3.connect("tasks.db")
    cur = con.cursor()
   
    cur.execute("DELETE FROM tasks WHERE id = ?", (id,))
    con.commit()

    if cur.rowcount == 0:
        con.close()
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})
    
    con.close()
    return Response(status_code=204)
