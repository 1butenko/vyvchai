import enum
import uuid
from datetime import datetime

from db.base import Base
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class SubjectEnum(str, enum.Enum):
    UKRAINIAN = "ukrainian"
    HISTORY = "history"
    ALGEBRA = "algebra"


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    subject = Column(Enum(SubjectEnum), nullable=False)
    grade = Column(Integer, nullable=False)
    topic_id = Column(String(255), nullable=False, index=True)
    topic_query = Column(Text)

    content = Column(Text, nullable=False)
    sources = Column(JSONB)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    quizzes = relationship("Quiz", back_populates="lesson")
