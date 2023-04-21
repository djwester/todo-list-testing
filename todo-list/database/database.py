import os
from enum import Enum

from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import (Mapped, declarative_base, mapped_column,
                            sessionmaker)

engine = create_engine(
    os.environ["DATABASE_URL"]
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Status(Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class Task(Base):
    __tablename__ = 'task'

    id = mapped_column(Integer, primary_key=True)

    description: Mapped[str]
    status: Mapped[Status]
