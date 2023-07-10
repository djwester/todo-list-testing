import hashlib
import os
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError, NoResultFound
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

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "13c02580cb229e251c714f5dd2e9be10f526c9231340e3e0cd2bcd4e921e1f4f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# TODO: Update to use Routes
app.mount("/static", StaticFiles(directory="static"), name="static")


class Task(BaseModel):
    description: str
    status: models.Status
    id: Optional[int] = None


class User(BaseModel):
    username: str
    hashed_password: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None


def create_access_token(username: str, expires: timedelta | None = None):
    data = {"sub": username}
    if expires:
        expire = datetime.utcnow() + expires
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_password(password: str, password_hash: str):
    return password_context.verify(password, password_hash)


def create_password_hash(password: str):
    return password_context.hash(password)


def authenticate_user(username: str, password: str):
    try:
        obj = aliased(models.User, name="obj")
        stmt = select(obj).where(obj.username == username)
        db_user = session.scalars(stmt).one()
    except NoResultFound:
        return False
    if not verify_password(password, db_user.hashed_password):
        return False
    return db_user


def get_user_by_token(token: str):
    pwd_hash = hashlib.md5(token.encode("utf-8")).hexdigest()
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.md5_password_hash == pwd_hash)
    try:
        db_user = session.scalars(stmt).one()
    except NoResultFound:
        return
    return db_user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_all_todos():
    obj = aliased(models.Task, name="obj")
    stmt = select(obj)
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in session.scalars(stmt)
    ]
    return todos


def get_todo_by_status(status: models.Status) -> list[models.Task]:
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.status == status)
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in session.scalars(stmt)
    ]
    return todos


def get_todos_by_description(search: str) -> list[models.Task]:
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.description == search)
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in session.scalars(stmt)
    ]
    return todos


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    You can login as user1 with password 12345

    If you want to create your own user, use the /user endpoint
    """

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user name or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.username, expires=expires)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/", include_in_schema=False)
def root(request: Request):
    todos = get_all_todos()
    return templates.TemplateResponse(
        "index.html", {"request": request, "todos": todos}
    )


@app.post("/tasks", status_code=201)
def create_task(task: Task):
    db_task = models.Task(**task.dict())
    try:
        session.add(db_task)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Task already exists")

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.get("/tasks", status_code=200)
def get_tasks(status: models.Status | None = None, search: str | None = None):
    if status:
        todos = get_todo_by_status(status)
    elif search:
        todos = get_todos_by_description(search)
    else:
        todos = get_all_todos()
    return todos


@app.put("/tasks/{task_id}/in-progress", include_in_schema=False)
def set_in_progress(task_id: int):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = session.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.IN_PROGRESS
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}/draft", include_in_schema=False)
def set_draft(task_id: int):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = session.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.DRAFT
    session.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}/complete", include_in_schema=False)
def set_Complete(task_id: int):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = session.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.COMPLETE
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
def get_task(task_id: int, response: Response):
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


@app.get("/user/me")
def get_user_me(token: Annotated[User, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == username)
    try:
        db_user = session.scalars(stmt).one()
    except NoResultFound:
        raise credentials_exception
    return {"username": db_user.username}


@app.get("/user/admin")
def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == "admin")
    admin_user = session.scalars(stmt).one()
    if current_user.md5_password_hash == admin_user.md5_password_hash:
        return {"Success": "You accessed this endpoint!"}
    else:
        raise HTTPException(
            status_code=403, detail="This user cannot access this endpoint"
        )


@app.get("/user")
def get_users():
    obj = aliased(models.User, name="obj")
    stmt = select(obj)
    users = [
        User(
            id=i.id,
            username=i.username,
            md5_password_hash=i.md5_password_hash,
        )
        for i in session.scalars(stmt)
    ]

    return users


@app.get("/user/{username}")
def get_user(
    username: str,
    response: Response,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == username)
    try:
        db_user = session.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {}

    return {"id": db_user.id, "username": db_user.username}


@app.post("/user")
def create_user(user: UserCreate):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == user.username)
    try:
        db_user = session.scalars(stmt).one()
        raise HTTPException(
            status_code=409, detail=f"The user {user.username} already exists"
        )
    except NoResultFound:
        pass

    db_user = models.User(
        username=user.username,
        hashed_password=create_password_hash(user.password),
        email=user.email,
        full_name=user.full_name,
        disabled=False,
    )
    session.add(db_user)
    session.commit()

    return {
        "username": db_user.username,
        "pwd": db_user.hashed_password,
        "email": db_user.email,
    }


@app.put("/user/{username}")
def update_user(
    username: str,
    user: UserCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == username)
    try:
        db_user = session.scalars(stmt).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"The user {username} does not exist"
        )
    db_user.hashed_password = create_password_hash(user.password)
    db_user.email = user.email
    db_user.full_name = user.full_name
    session.commit()

    return {
        "username": db_user.username,
        "pwd": db_user.hashed_password,
        "email": db_user.email,
    }
