from typing import TypedDict, List, Dict


class StudentProfile(TypedDict):
    student_id: str
    grade: int
    subject_scores: Dict[str, float]
    attendance_rate: float
    weak_topics: List[str]
    strong_topics: List[str]
    peer_percentile: float
    recommendations: List[str]
