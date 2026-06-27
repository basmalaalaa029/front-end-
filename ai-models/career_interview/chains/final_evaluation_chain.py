import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "final_evaluation_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f: return f.read()

def final_evaluation_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    llm = get_llm(temperature=0.2, max_tokens=3000, tier='main')
    def format_docs(docs): return "\n".join(d.page_content[:300] for d in docs)
    def get_context(query, user_id=None):
        from rag.cv_summary_cache import get_summary
        cached = get_summary(user_id or "") if user_id else ""
        if cached: return cached
        docs = retriever.invoke(query)
        return format_docs(docs)
    def build_inputs(inputs):
        docs = retriever.invoke("candidate skills experience background education")
        return {
            "context": format_docs(docs),
            "role_label": inputs.get("role_label", "Professional"),
            "level": inputs["level"],
            "transcript": inputs["transcript"],
            "technical_scores": inputs["technical_scores"],
            "competency_coverage": inputs.get("competency_coverage", ""),
            "bluff_incidents": inputs.get("bluff_incidents", "None."),
            "contradiction_log": inputs.get("contradiction_log", "None."),
            "soft_observations": inputs["soft_observations"],
            "audio_analysis": inputs["audio_analysis"],
            "video_analysis": inputs["video_analysis"],
            "actual_comm": inputs.get("actual_comm", "5.0"),
            "actual_conf": inputs.get("actual_conf", "5.0"),
            "actual_prob": inputs.get("actual_prob", "5.0"),
            "actual_hon":  inputs.get("actual_hon", "5.0"),
        }
    return build_inputs | prompt | llm | StrOutputParser()
