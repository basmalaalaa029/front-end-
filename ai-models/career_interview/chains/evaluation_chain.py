import os, logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

log = logging.getLogger("eval_chain")
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "evaluation_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f:
        return f.read()

def evaluate_answer_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    # Increase max_tokens: JSON evaluation response needs ~400-700 tokens
    llm = get_llm(temperature=0.3, max_tokens=2048, tier='main')

    def format_docs(docs):
        return "\n".join(d.page_content[:200] for d in docs)

    def build_inputs(inputs):
        answer = inputs.get("answer", "").strip()
        question = inputs.get("question", "").strip()

        # Log what we receive — critical for debugging silent failures
        log.info(f"[eval] Q: {question[:80]}...")
        log.info(f"[eval] A ({len(answer)} chars): {answer[:120]}...")

        if not answer:
            log.warning("[eval] Empty answer received — returning default")
            return {
                "context": "", "question": question,
                "answer": "(no answer provided)",
                "role_label": inputs.get("role_label", "Professional"),
                "level": inputs.get("level", "mid"),
                "question_category": inputs.get("question_category", "technical"),
            }

        # Use context passed in (already fetched in nodes.py)
        # Fall back to retriever if not provided
        context = inputs.get("context", "")
        if not context and retriever:
            try:
                docs = retriever.invoke(question[:150])
                context = format_docs(docs)
            except Exception:
                context = ""

        jd = inputs.get("job_description", "").strip()
        return {
            "context":           context[:300],
            "question":          question[:250],
            "answer":            answer[:900],
            "role_label":        inputs.get("role_label", "Professional"),
            "level":             inputs.get("level", "mid"),
            "question_category": inputs.get("question_category", "technical"),
            "job_description":   jd[:200] if jd else "Not provided",
        }

    return build_inputs | prompt | llm | StrOutputParser()
