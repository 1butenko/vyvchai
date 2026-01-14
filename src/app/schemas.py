from typing import List, Optional

from pydantic import BaseModel


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class StudentRegister(UserRegister):
    pass


class TeacherRegister(UserRegister):
    subject: List[str]


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    type: str

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    test_id: str
    question: str
    answer: str
    possible_answers: List[str]


class QuestionResponse(QuestionCreate):
    id: str

    class Config:
        from_attributes = True


class TestCreate(BaseModel):
    name: str
    class_id: str
    questions: Optional[List[QuestionCreate]] = []


class TestResponse(BaseModel):
    id: str
    name: str
    class_id: str
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    name: str
    teacher_id: str


class ClassResponse(BaseModel):
    id: str
    name: str
    teacher_id: str

    class Config:
        from_attributes = True
