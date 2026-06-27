import os, re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "followup_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f: return f.read()

def _extract_highlights(answer: str) -> str:
    """Extract specific things the candidate mentioned: tools, techniques, numbers, decisions."""
    if not answer or len(answer) < 20:
        return answer.strip()
    # Pull the first 300 chars which usually have the core claim
    excerpt = answer[:300].strip()
    # Find capitalized terms (likely tools/frameworks), numbers, and "I X'd" patterns
    tools = re.findall(r'\b[A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+)*\b', excerpt)
    actions = re.findall(r'\bI\s+(?:used|built|implemented|designed|created|developed|trained|deployed|integrated|applied|leveraged|wrote|worked)\s+\S+(?:\s+\S+){0,3}', excerpt, re.IGNORECASE)
    specifics = re.findall(r'\b\d+[%xkmb]?\b|\b(?:first|then|finally|because|by using|in order to)\b', excerpt, re.IGNORECASE)
    highlights = []
    if tools:     highlights.append("Tools/frameworks mentioned: " + ", ".join(dict.fromkeys(tools[:5])))
    if actions:   highlights.append("Actions they described: " + "; ".join(actions[:3]))
    if specifics: highlights.append("Specific details: " + ", ".join(dict.fromkeys(specifics[:4])))
    return "\n".join(highlights) if highlights else f"Main claim: {excerpt[:150]}"

def generate_followup_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    llm = get_llm(temperature=0.35, max_tokens=120, tier='fast')
    def format_docs(docs): return "\n".join(d.page_content[:300] for d in docs)
    def build_inputs(inputs):
        answer = inputs.get("answer", "")
        docs = retriever.invoke(f"{inputs.get('question','')} {answer}".strip()[:250])
        return {
            "context": format_docs(docs),
            "question": inputs["question"],
            "answer": answer[:500],
            "answer_highlights": _extract_highlights(answer),
            "role_label": inputs.get("role_label", "Professional"),
            "level": inputs.get("level", "mid"),
            "bluff_signals": inputs.get("bluff_signals", "None detected."),
            "unverified_claims": inputs.get("unverified_claims", "none"),
        }
    return build_inputs | prompt | llm | StrOutputParser()
