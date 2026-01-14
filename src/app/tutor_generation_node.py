import json
import os
from typing import List, TypedDict

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .vector_store import create_vector_store

# --- Pre-load dependencies ---
if os.environ.get("GOOGLE_API_KEY"):
    GENERATOR_LLM = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    # Enable JSON output mode for structured generation
    GENERATOR_LLM = GENERATOR_LLM.bind(response_mime_type="application/json")
    VECTOR_STORE = create_vector_store()
else:
    GENERATOR_LLM = None
    VECTOR_STORE = None
    print("WARNING: GOOGLE_API_KEY not set. Generation node will not work.")


# --- Data Structures for Structured Output ---
class Exercise(TypedDict):
    предмет: str
    клас: int
    тема: str
    складність: Literal["легка", "середня", "важка"]
    task_text: str
    answer_key: str


class GeneratedMaterial(TypedDict):
    summary: str
    exercises: List[Exercise]


# --- Prompt Engineering ---
PROMPT_TEMPLATE = """
Ти — AI-тьютор, експерт з Socratic Tutoring для учнів 8-9 класів.
Твоя мета — створити персоналізований навчальний матеріал на основі наданого контексту з підручника.

{custom_instructions}

--- КОНТЕКСТ З ПІДРУЧНИКА ---
{context}
--- КІНЕЦЬ КОНТЕКСТУ ---

Запит учня: "{user_query}"

Твоє завдання — згенерувати відповідь у форматі JSON, що містить два ключі: "summary" та "exercises".

1.  **summary**: Створи детальний конспект на основі запиту учня та наданого контексту.
    -   **ОБОВ'ЯЗКОВИЙ GROUNDING**: Кожне речення або абзац у конспекті ПОВИНЕН містити посилання на джерело у форматі `(стор. X)`.
    -   Базуй свою відповідь ТІЛЬКИ на наданому контексті. Не вигадуй інформацію.

2.  **exercises**: Створи 8-12 завдань для закріплення матеріалу.
    -   Кожне завдання має містити метадані: `предмет`, `клас`, `тема`, `складність`, `task_text`, `answer_key`.
    -   Складність завдань має відповідати рівню учня.

Приклад JSON-відповіді:
```json
{{
    "summary": "Штучний інтелект — це галузь комп'ютерних наук (стор. 15). Він включає в себе створення алгоритмів, здатних до навчання (стор. 16).",
    "exercises": [
        {{
            "предмет": "Інформатика",
            "клас": 9,
            "тема": "Основи ШІ",
            "складність": "легка",
            "task_text": "Що таке штучний інтелект?",
            "answer_key": "Галузь комп'ютерних наук, що займається створенням розумних машин."
        }}
    ]
}}
```
"""


# --- The Generation Node ---
def tutor_generation_node(state: dict) -> dict:
    """
    Generates a personalized lesson (summary + exercises) using LC-RAG.
    """
    print("---NODE: TUTOR GENERATION (LC-RAG)---")
    if GENERATOR_LLM is None or VECTOR_STORE is None:
        return {
            "generated_material": None,
            "messages": [HumanMessage(content="Помилка: Генератор не ініціалізовано.")],
        }

    # --- 1. Scoped Retrieval ---
    user_query = state["messages"][-1].content
    topic_details = state.get("topic_details")

    search_kwargs = {"k": 5}  # Retrieve more context for generation
    if topic_details:
        start_page = topic_details.get("topic_start_page")
        end_page = topic_details.get("topic_end_page")
        if start_page is not None and end_page is not None:
            print(f"Retrieving context within page range: {start_page}-{end_page}")
            search_kwargs["filter"] = {
                "book_page_number": {"$gte": start_page, "$lte": end_page}
            }

    results = VECTOR_STORE.similarity_search(user_query, **search_kwargs)
    context_str = "\n\n".join(
        [
            f"Джерело: стор. {doc.metadata.get('book_page_number', 'N/A')}\nТекст: {doc.page_content}"
            for doc in results
        ]
    )

    # --- 2. Prompt Engineering (Adaptive Instructions) ---
    custom_instructions = []
    if state.get("requires_recap"):
        custom_instructions.append(
            "УВАГА: Учень пропустив цю тему. Почни конспект з короткого, але змістовного огляду ключових понять."
        )

    if state.get("enable_scaffolding"):
        custom_instructions.append(
            "УВАГА: Учень має низький рівень майстерності. Використовуй Socratic Tutoring та Graduated Hinting. "
            "У конспекті пояснюй складні речі простими словами, використовуй аналогії. "
            "Не давай прямих відповідей на складні запитання, а став навідні запитання, щоб учень міг сам дійти до висновку."
        )

    # --- 3. Generate Material ---
    final_prompt = PROMPT_TEMPLATE.format(
        custom_instructions="\n".join(custom_instructions),
        context=context_str,
        user_query=user_query,
    )

    try:
        response = GENERATOR_LLM.invoke([HumanMessage(content=final_prompt)])
        generated_material = json.loads(response.content)

        # We can now pass the generated tasks to the solver/validator node
        return {
            "generated_material": generated_material,
            "generated_tasks": generated_material.get("exercises", []),
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"ERROR: Failed to generate or parse material. {e}")
        return {"generated_material": None, "generated_tasks": []}


# --- Example Usage ---
if __name__ == "__main__":
    # This example requires dummy data to be created by other node files
    pass
