import uuid
from typing import Any

from ..settings import Base
from sqlalchemy import ARRAY, Column, ForeignKey, String, Table
from sqlalchemy.orm import relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


# Association table for Student <-> Class (Many-to-Many)
student_class_association = Table(
    "student_class_association",
    Base.metadata,
    Column("student_id", String, ForeignKey("students.id"), primary_key=True),
    Column("class_id", String, ForeignKey("classes.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    type = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }


class Teacher(User):
    __tablename__ = "teachers"

    id = Column(String, ForeignKey("users.id"), primary_key=True)
    subject: Any = Column(ARRAY(String))

    __mapper_args__ = {"polymorphic_identity": "teacher"}


class Student(User):
    __tablename__ = "students"

    id = Column(String, ForeignKey("users.id"), primary_key=True)

    classes = relationship(
        "Class",
        secondary=student_class_association,
        back_populates="students",
    )

    __mapper_args__ = {"polymorphic_identity": "student"}


class Class(Base):
    __tablename__ = "classes"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    teacher_id = Column(String, ForeignKey("teachers.id"))

    teacher = relationship("Teacher", backref="classes")
    students = relationship(
        "Student",
        secondary=student_class_association,
        back_populates="classes",
    )


class Test(Base):
    __tablename__ = "tests"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    class_id = Column(String, ForeignKey("classes.id"))

    class_ = relationship("Class", backref="tests")
    questions = relationship("Question", backref="test")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=generate_uuid)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    possible_answers: Any = Column(ARRAY(String))
    test_id = Column(String, ForeignKey("tests.id"))
