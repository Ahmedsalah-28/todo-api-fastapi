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

# tasks = [
#     {
#         "id": 1,
#         "title": "Learn FastAPI",
#         "done": False
#     },
#     {
#         "id": 2,
#         "title": "Build CRUD API",
#         "done": False
#     },
#     {
#         "id": 3,
#         "title": "Submit Assignment",
#         "done": True
#     }
# ]





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

    cursor.execute("SELECT * FROM tasks")

    rows = cursor.fetchall()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        })
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
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        }

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.post("/tasks", status_code=201,summary="Create a new task")
def create_task(task: TaskCreate):

    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, False))
    connection.commit()

    new_id = cursor.lastrowid

    return {
        "id": new_id,
        "title": task.title,
        "done": False
    }



@app.put("/tasks/{task_id}",summary="Update a specific task")
def update_task(task_id: int, updated_task: TaskUpdate):

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (updated_task.title, updated_task.done, task_id))
    connection.commit()
    return {
        "id": task_id,
        "title": updated_task.title,
        "done": updated_task.done
    }

@app.delete("/tasks/{task_id}", status_code=204,summary="Delete a specific task")
def delete_task(task_id: int):
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    connection.commit()

    return Response(status_code=204)


@app.get("/stats")
def get_stats():

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    done = cursor.fetchone()[0]

    open_tasks = total - done

    return {
        "total": total,
        "done": done,
        "open": open_tasks
    }