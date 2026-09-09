"""LangGraph simple RAG state machine graph."""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from app.rag.retriever import retrieve_context
from app.llm.llm_manager import llm_manager


# import os

# # Set your LangSmith API key and project name directly in the file
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = "your_actual_api_key_here"
# os.environ["LANGCHAIN_PROJECT"] = "your_project_name_here"  # Optional, defaults to 'default'



# 1. Define simple LangGraph state
class RAGState(TypedDict):
    question: str
    context: List[Dict[str, Any]]
    answer: str
    sources: List[str]

# 2. Node 1: Retrieve documents
def retrieve_node(state: RAGState) -> Dict[str, Any]:
    question = state["question"]
    docs = retrieve_context(question)
    
    sources = []
    for d in docs:
        sources.append(f"{d['doc_name']} — page {d['page_number']} \ncontent :\n{d['content']}")
        
    return {"context": docs, "sources": sources}

# 3. Node 2: Generate Answer
def generate_node(state: RAGState) -> Dict[str, Any]:
    question = state["question"]
    context = state["context"]
    
    context_text = "\n\n".join(
        [f"[Source: {c['doc_name']} (Page {c['page_number']})]\n{c['content']}" for c in context]
    )
    
    prompt = (
        "Answer the user's question accurately using ONLY the provided document context.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )
    
    answer = llm_manager.ask(prompt)
    return {"answer": answer}

# 4. Construct LangGraph Workflow
builder = StateGraph(RAGState)
builder.add_node("retrieve_documents", retrieve_node)
builder.add_node("generate_answer", generate_node)

builder.add_edge(START, "retrieve_documents")
builder.add_edge("retrieve_documents", "generate_answer")
builder.add_edge("generate_answer", END)

rag_graph = builder.compile()

def ask_question(question: str) -> Dict[str, Any]:
    """Public wrapper function to invoke the RAG graph."""
    initial_state = {
        "question": question,
        "context": [],
        "answer": "",
        "sources": []
    }
    result = rag_graph.invoke(initial_state)
    return result