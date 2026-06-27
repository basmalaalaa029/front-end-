import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "decision_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f: return f.read()

def decide_next_action_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    llm = get_llm(temperature=0.1, max_tokens=200, tier='fast')
    def build_inputs(inputs):
        return {
            "role_label": inputs.get("role_label", "Professional"),
            "level": inputs.get("level", "mid"),
            "interview_phase": inputs.get("interview_phase", "technical"),
            "questions_asked": inputs.get("questions_asked", "0"),
            "min_q": inputs.get("min_q", "5"),
            "max_q": inputs.get("max_q", "12"),
            "difficulty_hint": inputs.get("difficulty_hint", "MAINTAIN current difficulty."),
            "competency_coverage": inputs.get("competency_coverage", ""),
            "saturation_status": inputs.get("saturation_status", ""),
            "history": inputs.get("history", ""),
            "question": inputs.get("question", ""),
            "answer": inputs.get("answer", "")[:200],
            "score": inputs.get("score", "0"),
            "bluff_detected": inputs.get("bluff_detected", "False"),
            "consecutive_followups": inputs.get("consecutive_followups", "0"),
            "unverified_claims": inputs.get("unverified_claims", "none"),
            "candidate_strengths": inputs.get("candidate_strengths", "none"),
            "candidate_weaknesses": inputs.get("candidate_weaknesses", "none"),
        }
    return build_inputs | prompt | llm | StrOutputParser()
