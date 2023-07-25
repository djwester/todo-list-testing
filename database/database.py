import os
from enum import Enum
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import Integer, create_engine, select
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, aliased, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Status(Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class Task(Base):
    __tablename__ = "task"

    id = mapped_column(Integer, primary_key=True)

    description: Mapped[str]
    status: Mapped[Status]


class User(Base):
    __tablename__ = "profile"

    id = mapped_column(Integer, primary_key=True)

    username: Mapped[str]
    hashed_password: Mapped[str]
    email: Mapped[Optional[str]]
    full_name: Mapped[Optional[str]]
    disabled: Mapped[Optional[bool]]


def create_password_hash(password: str):
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return password_context.hash(password)


def maybe_initialize_db(db, engine):
    try:
        obj = aliased(User, name="obj")
        stmt = select(obj)
        _ = db.scalars(stmt).one()
    except OperationalError:
        Base.metadata.create_all(engine)
    except NoResultFound:
        db_user = User(
            username="user1",
            hashed_password=create_password_hash("12345"),
            email="user1@test.com",
            full_name="User One",
            disabled=False,
        )
        db.add(db_user)
        db.commit()
        db_user = User(
            username="admin",
            hashed_password=create_password_hash("123456"),
            email="admin@test.com",
            full_name="Admin User",
            disabled=False,
        )
        db.add(db_user)
        db.commit()


def db_session(initialize=False):
    print(initialize)
    uri = os.getenv("DATABASE_URL")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    if ":memory:" in uri:
        engine = create_engine(uri, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(uri)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    maybe_initialize_db(db, engine)
    with Session() as session:
        yield session
