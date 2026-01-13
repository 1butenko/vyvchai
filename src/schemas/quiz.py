from typing import Dict, List, Optional, TypedDict


class QuizQuestion(TypedDict):
    question: str
    type: str
    options: Optional[List[str]]
    correct_answer: str
    difficulty: Optional[str]
    topic_id: str
    subtopic_id: Optional[str]
    page_reference: List[int]
    metadata: Dict
