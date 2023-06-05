import os
from enum import Enum

from sqlalchemy import Integer, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Status(Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in progress"
    COMPLETE = "complete"


meta = MetaData()


class Task(Base):
    __tablename__ = "task"
    metadata = meta
    id = mapped_column(Integer, primary_key=True)

    description: Mapped[str]
    status: Mapped[Status]


uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
engine = create_engine(uri)


meta.create_all(engine)
