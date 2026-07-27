from fastapi import FastAPI
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

tasks = [
    {"id": 1, "title": "Task 1", "done": True},
    {"id": 2, "title": "Task 2", "done": False},
    {"id": 3, "title": "Task 3", "done": True},
]

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

@app.get("/tasks")
async def get_tasks():
    """List all tasks."""
    return tasks

@app.get("/tasks/{id}")
async def get_tasks_by_id(id: int):
    """Get a task by its ID."""
    for task in tasks:
        if task["id"] == id:
            return task
    
    return JSONResponse(status_code=404,content={"error": f"Task {id} not found"})

@app.post("/tasks", status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task."""
    if not task.title:
        return JSONResponse(status_code=400, content={"error": "Title is required."})
    next_id = max(task["id"] for task in tasks) + 1
    new_task = {"id": next_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{id}")
async def update_task(id: int, task: TaskUpdate):
    """Update a task by its ID."""
    if task.title is None and task.done is None:
        return JSONResponse(status_code=400, content={"error": "At least one field to update is required."})
    for t in tasks:
        if t["id"] == id:
            if task.title is not None:
                t["title"] = task.title

            if task.done is not None:
                t["done"] = task.done
            return t
    
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.delete("/tasks/{id}", status_code=204)
async def delete_task_by_id(id: int):
    """Delete a task by its ID."""
    for task in tasks:
        if task["id"] == id:
            tasks.remove(task)
            return JSONResponse(status_code=204, content={"message": f"Task {id} deleted successfully."})
    
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})