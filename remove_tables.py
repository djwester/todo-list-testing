import os
from enum import Enum
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Status(Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in progress"
    COMPLETE = "complete"


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


uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
engine = create_engine(uri)

Base.metadata.drop_all(engine)
