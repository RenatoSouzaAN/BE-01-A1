from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

task1 = {"id": 1, "title": "Task 1", "done": True}
task2 = {"id": 2, "title": "Task 2", "done": False}
task3 = {"id": 3, "title": "Task 3", "done": True}

@app.get("/")
async def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/tasks")
async def get_tasks():
    return [task1, task2, task3]

@app.get("/tasks/{id}")
async def get_tasks_by_id(id: int):
    for task in [task1, task2, task3]:
        if task["id"] == id:
            return task
    
    return JSONResponse(status_code=404,content={"error": f"Task {id} not found"})
