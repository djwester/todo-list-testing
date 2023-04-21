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
    __tablename__ = 'task'
    metadata = meta
    id = mapped_column(Integer, primary_key=True)

    description: Mapped[str]
    status: Mapped[Status]


engine = create_engine(
    os.environ["DATABASE_URL"]
)


meta.create_all(engine)
