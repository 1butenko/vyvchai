from . import schemas
from .models.models_db import Class, Question, Student, Teacher, Test
from sqlalchemy.orm import Session


def create_student(db: Session, student: schemas.StudentRegister) -> Student:
    # Hash password in a real app
    db_student = Student(
        name=student.name,
        email=student.email,
        password=student.password,  # Security check: Password should be hashed
        type="student",
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def create_teacher(db: Session, teacher: schemas.TeacherRegister) -> Teacher:
    # Hash password in a real app
    db_teacher = Teacher(
        name=teacher.name,
        email=teacher.email,
        password=teacher.password,  # Security check: Password should be hashed
        subject=teacher.subject,
        type="teacher",
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def create_test(db: Session, test: schemas.TestCreate) -> Test:
    db_test = Test(name=test.name, class_id=test.class_id)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)

    # If questions are provided at creation
    if test.questions:
        for q in test.questions:
            # Override test_id just in case
            q.test_id = db_test.id
            create_question(db, q)

    db.refresh(db_test)
    return db_test


def create_question(db: Session, question: schemas.QuestionCreate) -> Question:
    db_question = Question(
        question=question.question,
        answer=question.answer,
        possible_answers=question.possible_answers,
        test_id=question.test_id,
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_questions_by_test_id(db: Session, test_id: str):
    return db.query(Question).filter(Question.test_id == test_id).all()


def get_test(db: Session, test_id: str):
    return db.query(Test).filter(Test.id == test_id).first()


def create_class(db: Session, class_: schemas.ClassCreate) -> Class:
    db_class = Class(name=class_.name, teacher_id=class_.teacher_id)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


def get_user(db: Session, user_id: str):
    from src.app.models.models_db import User

    return db.query(User).filter(User.id == user_id).first()
