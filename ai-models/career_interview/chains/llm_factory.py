"""
llm_factory.py — Smart LLM routing.
Uses faster/smaller model for question generation,
reserves larger model for evaluation and final report.
"""
from langchain_groq import ChatGroq
from config import Config

# Model tiers
FAST_MODEL  = "llama-3.1-8b-instant"    # Fast, cheap — questions & decisions
MAIN_MODEL  = "llama-3.3-70b-versatile" # Smart — evaluation & final report

def get_llm(temperature: float = None, max_tokens: int = 1024, tier: str = "main") -> ChatGroq:
    """
    tier="fast"  → llama-3.1-8b-instant  (questions, decisions, follow-ups)
    tier="main"  → llama-3.3-70b-versatile (evaluation, final report)
    """
    model = FAST_MODEL if tier == "fast" else MAIN_MODEL
    # Override with env var if set
    if Config.LLM_MODEL_NAME and tier == "main":
        model = Config.LLM_MODEL_NAME
    return ChatGroq(
        model=model,
        temperature=temperature if temperature is not None else Config.TEMPERATURE,
        max_tokens=max_tokens,
        api_key=Config.GROQ_API_KEY,
    )
