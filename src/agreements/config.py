from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "agreements-management"

    # Specialist agent URLs
    creator_agent_url: str = "http://localhost:8001"
    query_agent_url: str = "http://localhost:8002"
    modifier_agent_url: str = "http://localhost:8003"

    # Database
    database_url: str = "sqlite+aiosqlite:///./agreements.db"

    # LLM models — planner uses Claude, specialists use Llama 3.1 8B via Groq
    llm_model: str = "claude-sonnet-4-6"
    specialist_llm_model: str = "llama-3.1-8b-instant"


settings = Settings()
