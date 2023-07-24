import os
from enum import Enum
from typing import Optional

from sqlalchemy import Integer, create_engine, select
from sqlalchemy.exc import OperationalError
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


def db_session():
    uri = os.getenv("DATABASE_URL")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    if ":memory:" in uri:
        engine = create_engine(uri, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(uri)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        temp_session = Session()
        obj = aliased(Task, name="obj")
        stmt = select(obj)
        _ = temp_session.scalars(stmt).one()
    except OperationalError:
        Base.metadata.create_all(engine)

    with Session() as session:
        yield session
