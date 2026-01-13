from db.base import Base
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    grade = Column(Integer, nullable=False)  # 8 or 9
    class_name = Column(String(50))

    profile_data = Column(JSON)

    user = relationship("User")
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
