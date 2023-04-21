import os
from dataclasses import asdict, dataclass

import database.database as models
from fastapi import FastAPI, Form, Request, Response, status
# from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import aliased, sessionmaker
from sqlalchemy.orm.exc import UnmappedInstanceError

engine = create_engine(os.environ["DATABASE_URL"])

Session = sessionmaker(bind=engine)
session = Session()

templates = Jinja2Templates(directory="templates")
app = FastAPI()

# TODO: Update to use Routes
app.mount("/static", StaticFiles(directory="static"), name="static")


@dataclass
class Task:
    description: str
    status: models.Status


@app.get("/")
def root(request: Request):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj)
    todos = [i.id for i in session.scalars(stmt)]
    return templates.TemplateResponse("index.html", 
                                      {"request": request, "todos": todos})


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    db_task = models.Task(**asdict(task))
    session.add(db_task)
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.post("/add", status_code=201)
def add_task(request: Request, task: str = Form(...)):

    internal_task = Task(description=task,
                status=models.Status.DRAFT)

    created_task = create_task(internal_task)
    return str(created_task["description"])
    # return RedirectResponse(url=app.url_path_for("root"), 
    #                         status_code=status.HTTP_303_SEE_OTHER)
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
