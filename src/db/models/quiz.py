import uuid
from datetime import datetime

from db.base import Base
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)

    title = Column(JSONB, nullable=False)
    questions = Column(JSONB, nullable=False)

    validation_passed = Column(Boolean, default=False)
    solver_feedback = Column(JSONB)

    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)

    lesson = relationship("Lesson", back_populates="quizzes")
    quiz_attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    answers = Column(JSONB, nullable=False)

    score = Column(Float)
    feedback = Column(JSONB)

    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    graded_at = Column(DateTime)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")
