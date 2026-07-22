from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator,Field
from typing import Optional
import sqlite3

connection = sqlite3.connect(
    "tasks.db",
    check_same_thread=False
)

cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL
)
""")

connection.commit()

cursor.execute("SELECT COUNT(*) FROM tasks")

count = cursor.fetchone()[0]
if count == 0:
    cursor.executemany(
        """
        INSERT INTO tasks (title, done)
        VALUES (?, ?)
        """,
        [
            ("Learn FastAPI", False),
            ("Study SQL", False),
            ("Build REST API", True)
        ]
    )

    connection.commit()
    

class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):

        if not value.strip():
            raise ValueError("Title cannot be empty")

        return value

class TaskUpdate(BaseModel):
    title: str = Field(min_length=1)
    done: bool


app = FastAPI()
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid request body"
        }
    )

tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Build CRUD API",
        "done": False
    },
    {
        "id": 3,
        "title": "Submit Assignment",
        "done": True
    }
]





@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/tasks",
            "/stats",
            "/health"
        ]
    }


@app.get("/health",summary="Health check endpoint")
def health():
    return {
        "status": "ok"
    }


# @app.get("/tasks",summary="Get all tasks")
# def get_tasks():
#     return tasks



@app.get("/tasks")
def get_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None
):
    result = tasks

    # Filter by done status
    if done is not None:
        result = [task for task in result if task["done"] == done]

    # Search by title
    if search:
        result = [
            task
            for task in result
            if search.lower() in task["title"].lower()
        ]

    return result

@app.get("/tasks/{task_id}",summary="Get a specific task")

def get_task(task_id: int):

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )

@app.post("/tasks", status_code=201,summary="Create a new task")
def create_task(task: TaskCreate):
    new_id = max(task["id"] for task in tasks) + 1 if tasks else 1
    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }
    tasks.append(new_task)
    return new_task



@app.put("/tasks/{task_id}",summary="Update a specific task")
def update_task(task_id: int, updated_task: TaskUpdate):

    for task in tasks:

        if task["id"] == task_id:

            task["title"] = updated_task.title
            task["done"] = updated_task.done

            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )

@app.delete("/tasks/{task_id}", status_code=204,summary="Delete a specific task")
def delete_task(task_id: int):

    for index, task in enumerate(tasks):

        if task["id"] == task_id:

            tasks.pop(index)

            return Response(status_code=204)

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.get("/stats")
def get_stats():

    total = len(tasks)
    done = sum(task["done"] for task in tasks)
    open_tasks = total - done

    return {
        "total": total,
        "done": done,
        "open": open_tasks
    }