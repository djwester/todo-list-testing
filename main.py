import os
from typing import Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import aliased, sessionmaker
from sqlalchemy.orm.exc import UnmappedInstanceError

from database import database as models

uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
engine = create_engine(uri)

Session = sessionmaker(bind=engine)
session = Session()

templates = Jinja2Templates(directory="templates")
app = FastAPI()


# TODO: Update to use Routes
app.mount("/static", StaticFiles(directory="static"), name="static")


class Task(BaseModel):
    description: str
    status: models.Status
    id: Optional[int] = None


def get_all_todos():
    obj = aliased(models.Task, name="obj")
    stmt = select(obj)
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in session.scalars(stmt)
    ]
    return todos


@app.get("/")
def root(request: Request):
    todos = get_all_todos()
    print(todos[0].status)
    return templates.TemplateResponse(
        "index.html", {"request": request, "todos": todos}
    )


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    db_task = models.Task(**task.dict())
    session.add(db_task)
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.get("/tasks", status_code=200)
def get_tasks():
    todos = get_all_todos()

    return todos


@app.put("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: models.Status):
    obj = aliased(models.Task, name="obj")
    db_task = session.execute(select(obj).filter_by(id=task_id)).scalar_one()
    db_task.status = status
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    obj = aliased(models.Task, name="obj")
    db_task = session.execute(select(obj).filter_by(id=task_id)).scalar_one()
    db_task.description = task.description
    db_task.status = task.status
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.get("/tasks/{task_id}")
def get_task(task_id, response: Response):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.id == task_id)
    try:
        db_task = session.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {}

    return {"description": db_task.description, "status": db_task.status}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, response: Response):
    try:
        db_task = session.get(models.Task, task_id)
        session.delete(db_task)
        session.commit()
    except UnmappedInstanceError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": f"could not delete task {task_id}"}

    return {"deleted": True}
