import hashlib
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, aliased

from database import database as models

templates = Jinja2Templates(directory="templates")
app = FastAPI()

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "13c02580cb229e251c714f5dd2e9be10f526c9231340e3e0cd2bcd4e921e1f4f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# TODO: Update to use Routes
app.mount("/static", StaticFiles(directory="static"), name="static")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class Task(BaseModel):
    description: str
    status: models.Status
    created_by: str | None = "anonymous"
    id: int | None = None


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


def authenticate_user(username: str, password: str, db: Session):
    try:
        obj = aliased(models.User, name="obj")
        stmt = select(obj).where(obj.username == username)
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        return False
    if not verify_password(password, db_user.hashed_password):
        return False
    return db_user


def get_user_by_token(token: str, db: Session):
    pwd_hash = hashlib.md5(token.encode("utf-8")).hexdigest()
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.md5_password_hash == pwd_hash)
    try:
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        return
    return db_user


def get_all_todos(db: Session):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj)
    todos = [
        Task(
            id=i.id,
            description=i.description,
            status=i.status.value,
            created_by=i.created_by,
        )
        for i in db.scalars(stmt)
    ]
    return todos


def get_all_todos_for_user(username: str, db: Session):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.created_by == username)
    todos = [
        Task(
            id=i.id,
            description=i.description,
            status=i.status.value,
            created_by=i.created_by,
        )
        for i in db.scalars(stmt)
    ]
    return todos


def get_todo_by_status(
    status: models.Status,
    username: str | None,
    db: Session,
) -> list[models.Task]:
    obj = aliased(models.Task, name="obj")
    if username:
        stmt = select(obj).where(
            obj.status == status,
            obj.created_by == username,
        )
    else:
        stmt = select(obj).where(obj.status == status)
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in db.scalars(stmt)
    ]
    return todos


def get_todos_by_description(
    search: str,
    username: str | None,
    db: Session,
) -> list[models.Task]:
    obj = aliased(models.Task, name="obj")
    if username:
        stmt = select(obj).where(
            obj.description.contains(search), obj.created_by == username
        )
    else:
        stmt = select(obj).where(obj.description.contains(search))
    todos = [
        Task(id=i.id, description=i.description, status=i.status.value)
        for i in db.scalars(stmt)
    ]
    return todos


@app.post("/token")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(models.db_session),
):
    """
    You can login as user1 with password 12345

    If you want to create your own user, use the /user endpoint
    """

    user = authenticate_user(form_data.username, form_data.password, db)
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
def root(request: Request, db: Session = Depends(models.db_session)):
    todos = get_all_todos(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "todos": todos}
    )


@app.post("/tasks", status_code=201)
def create_task(task: Task, db: Session = Depends(models.db_session)):
    db_task = models.Task(**task.dict())
    try:
        db.add(db_task)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Task already exists")

    return Task(
        id=db_task.id,
        description=db_task.description,
        status=db_task.status,
        created_by=db_task.created_by,
    )


@app.get("/tasks", status_code=200)
def get_tasks(
    status: models.Status | None = None,
    search: str | None = None,
    username: str | None = None,
    db: Session = Depends(models.db_session),
):
    if status:
        todos = get_todo_by_status(status, username, db)
    elif search:
        todos = get_todos_by_description(search, username, db)
    elif username:
        todos = get_all_todos_for_user(username, db)
    else:
        todos = get_all_todos(db)
    return todos


@app.put("/tasks/{task_id}/in-progress", include_in_schema=False)
def set_in_progress(task_id: int, db: Session = Depends(models.db_session)):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = db.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.IN_PROGRESS
    db.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}/draft", include_in_schema=False)
def set_draft(task_id: int, db: Session = Depends(models.db_session)):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = db.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.DRAFT
    db.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}/complete", include_in_schema=False)
def set_Complete(task_id: int, db: Session = Depends(models.db_session)):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).filter_by(id=task_id)
    try:
        db_task = db.execute(stmt).scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"task {task_id} not found",
        )
    db_task.status = models.Status.COMPLETE
    db.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task: Task,
    db: Session = Depends(models.db_session),
):
    obj = aliased(models.Task, name="obj")
    db_task = db.execute(select(obj).filter_by(id=task_id)).scalar_one()
    db_task.description = task.description
    db_task.status = task.status
    db.commit()

    return {
        "id": db_task.id,
        "description": db_task.description,
        "status": db_task.status,
    }


@app.get("/tasks/{task_id}")
def get_task(
    task_id: int, response: Response, db: Session = Depends(models.db_session)
):
    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.id == task_id)
    try:
        db_task = db.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {}

    return {"description": db_task.description, "status": db_task.status}


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    response: Response,
    token: User = Depends(oauth2_scheme),
    db: Session = Depends(models.db_session),
):
    if not token:
        username = "anonymous"
    else:
        user = get_current_user(token, db)
        username = user.username

    obj = aliased(models.Task, name="obj")
    stmt = select(obj).where(obj.id == task_id, obj.created_by == username)
    try:
        db_task = db.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": f"could not delete task {task_id}"}

    db.delete(db_task)
    db.commit()

    return {"deleted": True}


def get_current_user(
    token: Annotated[User, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(models.db_session)],
):
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
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        raise credentials_exception
    return db_user


@app.get("/user/me")
def get_user_me(
    token: Annotated[User, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(models.db_session)],
):
    current_user = get_current_user(token, db)

    return {"username": current_user.username}


@app.get("/user/admin", response_model=None)
def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    if current_user.username == "admin":
        return {"Success": "You accessed this endpoint!"}
    else:
        raise HTTPException(
            status_code=403, detail="This user cannot access this endpoint"
        )


@app.get("/user")
def get_users(db: Session = Depends(models.db_session)):
    obj = aliased(models.User, name="obj")
    stmt = select(obj)
    users = [
        User(
            id=i.id,
            username=i.username,
            email=i.email,
            full_name=i.full_name,
        )
        for i in db.scalars(stmt)
    ]

    return users


@app.get("/user/{username}")
def get_user(
    username: str,
    response: Response,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(models.db_session)],
):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == username)
    try:
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {}

    return {"id": db_user.id, "username": db_user.username}


@app.post("/user")
def create_user(user: UserCreate, db: Session = Depends(models.db_session)):
    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == user.username)
    try:
        db_user = db.scalars(stmt).one()
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
    db.add(db_user)
    db.commit()

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
    db: Annotated[Session, Depends(models.db_session)],
):
    current_user = get_current_user(token, db)
    # TODO: Add support for admin user to modify others
    if not current_user.username == username and username != "admin":
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to modify this user",
        )

    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.username == username)
    try:
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"The user {username} does not exist"
        )
    db_user.hashed_password = create_password_hash(user.password)
    db_user.email = user.email
    db_user.full_name = user.full_name
    db.commit()

    return {
        "username": db_user.username,
        "pwd": db_user.hashed_password,
        "email": db_user.email,
    }


@app.delete("/user/{user_id}")
def delete_user(
    user_id: int,
    response: Response,
    token: User = Depends(oauth2_scheme),
    db: Session = Depends(models.db_session),
):
    if not token:
        username = "anonymous"
    else:
        user = get_current_user(token, db)
        username = user.username

    obj = aliased(models.User, name="obj")
    stmt = select(obj).where(obj.id == user_id)
    try:
        db_user = db.scalars(stmt).one()
    except NoResultFound:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": f"could not delete user {user_id}"}

    db.delete(db_user)
    db.commit()

    return {"deleted": True}
