import os
from enum import Enum
from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy import ForeignKey, Integer, UniqueConstraint, create_engine, select
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    aliased,
    mapped_column,
    relationship,
    sessionmaker,
)


class Base(DeclarativeBase):
    pass


class Status(Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class User(Base):
    __tablename__ = "profile"
    __table_args__ = (UniqueConstraint("username"),)

    id = mapped_column(Integer, primary_key=True)

    username: Mapped[str]
    hashed_password: Mapped[str]
    email: Mapped[Optional[str]]
    full_name: Mapped[Optional[str]]
    disabled: Mapped[Optional[bool]]
    tasks: Mapped[List["Task"]] = relationship()


class Task(Base):
    __tablename__ = "task"

    id = mapped_column(Integer, primary_key=True)

    description: Mapped[str]
    status: Mapped[Status]
    created_by: Mapped[int] = mapped_column(ForeignKey("profile.username"))


def create_password_hash(password: str):
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return password_context.hash(password)


def maybe_initialize_db(db, engine):
    try:
        obj = aliased(User, name="obj")
        stmt = select(obj)
        users = db.scalars(stmt)
        obj = aliased(Task, name="obj")
        stmt = select(obj)
        tasks = db.scalars(stmt)
    except OperationalError:
        Base.metadata.create_all(engine)
    except NoResultFound:
        users = [
            ("user1", "User One"),
            ("user2", "User Two"),
            ("admin", "Admin User"),
            ("anonymous", "Anonymous User"),
        ]
        for user in users:
            db_user = User(
                username=user[0],
                hashed_password=create_password_hash("12345"),
                email=f"{user[0]}@test.com",
                full_name=user[1],
                disabled=False,
            )
            db.add(db_user)
            db.commit()
    except Exception:
        Base.metadata.create_all(engine)


def db_session():
    uri = os.getenv("DATABASE_URL")
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    engine = create_engine(uri)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    maybe_initialize_db(db, engine)
    with Session() as session:
        yield session
        session.close()
