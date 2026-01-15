import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# LapaLLM Configuration defaults
DEFAULT_BASE_URL = "http://146.59.127.106:4000"
DEFAULT_API_KEY = "sk-dummy"
DEFAULT_MODEL = "lapa"
DEFAULT_EMBEDDING_MODEL = "text-embedding-qwen"

def get_lapa_llm(temperature: float = 0.7) -> ChatOpenAI:
    """
    Returns a ChatOpenAI instance configured for LapaLLM.
    """
    base_url = os.getenv("LAPA_LLM_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.getenv("LAPA_LLM_API_KEY", DEFAULT_API_KEY)
    model = os.getenv("LAPA_LLM_MODEL", DEFAULT_MODEL)

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
    )

def get_lapa_embeddings() -> OpenAIEmbeddings:
    """
    Returns an OpenAIEmbeddings instance configured for LapaLLM.
    """
    base_url = os.getenv("LAPA_LLM_BASE_URL", DEFAULT_BASE_URL)
    api_key = os.getenv("LAPA_LLM_API_KEY", DEFAULT_API_KEY)
    model = os.getenv("LAPA_LLM_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    return OpenAIEmbeddings(
        base_url=base_url,
        api_key=api_key,
        model=model,
        check_embedding_ctx_length=False, # Often needed for custom endpoints
    )
