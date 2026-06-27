import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "question_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f: return f.read()

def generate_question_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    llm = get_llm(temperature=0.45, max_tokens=180, tier='fast')
    def format_docs(docs): return "\n".join(d.page_content[:350] for d in docs)
    def get_context(query, user_id=None):
        from rag.cv_summary_cache import get_summary
        cached = get_summary(user_id or "") if user_id else ""
        if cached: return cached
        docs = retriever.invoke(query)
        return format_docs(docs)
    def build_inputs(inputs):
        docs = retriever.invoke("candidate background skills experience projects technologies")
        return {
            "context": format_docs(docs),
            "level": inputs.get("level", "mid"),
            "topics_covered": inputs.get("topics_covered", "None yet."),
            "role_label": inputs.get("role_label", "Professional"),
            "role_description": inputs.get("role_description", ""),
            "primary_domain": inputs.get("primary_domain", "technology"),
            "detected_technologies": inputs.get("detected_technologies", "not specified"),
            "role_guidelines": inputs.get("role_guidelines", ""),
            "domain_lock": inputs.get("domain_lock", ""),
            "interview_phase": inputs.get("interview_phase", "technical"),
            "current_competency": inputs.get("current_competency", "core knowledge"),
            "question_category": inputs.get("question_category", "technical"),
            "difficulty_hint": inputs.get("difficulty_hint", "MAINTAIN difficulty."),
            "candidate_strengths": inputs.get("candidate_strengths", "none observed"),
            "candidate_weaknesses": inputs.get("candidate_weaknesses", "none observed"),
            "unverified_claims": inputs.get("unverified_claims", "none"),
            "last_transition_note": inputs.get("last_transition_note", ""),
            "job_description": inputs.get("job_description", "Not provided"),
            "asked_concepts": inputs.get("asked_concepts", "none"),
            "jd_term":        inputs.get("jd_term", ""),
        }
    return build_inputs | prompt | llm | StrOutputParser()
