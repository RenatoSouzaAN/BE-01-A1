# Task API

FastAPI CRUD to-do list (in-memory) done as an exercise for the AI Back-end track.

## Requirements

- Python 3.10+

## Install & run

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info (name, version, endpoints) |
| GET | `/health` | Health check |
| POST | `/reset` | Restore the 3 seed tasks |
| GET | `/tasks` | List all tasks (?done=true|false, ?search=...) |
| GET | `/tasks/stats` | Counts: total, done, pending |
| GET | `/tasks/{id}` | Get a task by ID |
| POST | `/tasks` | Create a new task |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## Example

```bash
curl -i http://localhost:8000/tasks
```

```
HTTP/1.1 200 OK
date: Mon, 27 Jul 2026 15:16:07 GMT
server: uvicorn
content-length: 116
content-type: application/json

[{"id":1,"title":"Task 1","done":true},{"id":2,"title":"Task 2","done":false},{"id":3,"title":"Task 3","done":true}]
```

## Swagger UI

![Swagger UI](docs.png)
