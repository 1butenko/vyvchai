import uuid
from datetime import datetime

from db.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    content = Column(Text, nullable=False)
    topics = Column(JSONB)
    exercises = Column(JSONB)

    based_on_attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
