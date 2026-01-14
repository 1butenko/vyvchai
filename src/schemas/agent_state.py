from enum import Enum
from typing import Dict, List, Optional, TypedDict


class SubjectEnum(str, Enum):
    UKRAINIAN = "ukrainian"
    HISTORY = "history"
    ALGEBRA = "algebra"


class AgentState(TypedDict):
    """LangGraph state schema."""

    # Req context
    request_id: str
    class_id: str
    student_id: str
    teacher_id: str
    grade: int
    subject: SubjectEnum
    topic_query: str

    student_profile: Optional[Dict]

    # RAG pipeline
    matched_topics: List[str]
    retrieved_docs: List[Dict]

    # Generation
    lesson_content: str
    lesson_sources: List[str]
    quiz: List[Dict]

    # Validation
    solver_feedback: Dict
    validation_passed: bool
    regeneration_count: int

    # Grading & recommendations
    student_answers: Optional[List[str]]
    grading_result: Optional[Dict]
    recommendations: Optional[Dict]

    # Telemetry
    trace_id: str
    step_logs: List[str]
    errors: List[str]
