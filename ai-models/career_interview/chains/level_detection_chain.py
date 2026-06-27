import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from chains.llm_factory import get_llm

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "level_detection_prompt.txt")

def _load_prompt():
    with open(os.path.normpath(_PROMPT_PATH)) as f: return f.read()

def detect_level_chain(retriever):
    prompt = ChatPromptTemplate.from_template(_load_prompt())
    llm = get_llm(temperature=0.1, max_tokens=150, tier='fast')
    def format_docs(docs): return "\n".join(d.page_content[:400] for d in docs)
    def build_inputs(inputs):
        docs = retriever.invoke("experience education skills work history years")
        return {"context": format_docs(docs), "job_description": inputs.get("job_description", "Not provided")}
    return build_inputs | prompt | llm | StrOutputParser()
