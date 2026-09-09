"""PageIndex tree-reasoning retriever without vector databases."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from app.config import Config
from app.llm.llm_manager import llm_manager

logger = logging.getLogger(__name__)

def load_all_indexes() -> List[Dict[str, Any]]:
    """Loads all generated local PageIndex files from data/indexes/."""
    index_files = list(Config.INDEXES_DIR.glob("*_index.json"))
    loaded_trees = []
    
    for idx_file in index_files:
        try:
            with open(idx_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                loaded_trees.append(data)
        except Exception as e:
            logger.error(f"Failed to load index file {idx_file}: {e}")
            
    return loaded_trees

def retrieve_context(query: str) -> List[Dict[str, Any]]:
    """Reason over document tree structures to locate exact relevant pages.
    
    Vectorless RAG uses tree-traversal reasoning instead of distance metrics.
    """
    trees = load_all_indexes()
    if not trees:
        logger.warning("No indexes found. Please index documents first.")
        return []

    retrieved_results = []

    for tree in trees:
        doc_name = tree.get("doc_name", "Unknown Document")
        pages = tree.get("pages", [])
        
        # Use PageIndex tree reasoning: ask LLM which pages contain information to answer the query
        reasoning_prompt = (
            f"You are navigating a document tree for '{doc_name}'.\n"
            f"Question: '{query}'\n"
            f"Document outline:\n{tree.get('llm_tree_raw')}\n\n"
            "Which page numbers are most likely to contain the exact answer? "
            "Reply with ONLY page numbers separated by commas (e.g. 1, 3)."
        )
        
        relevant_pages_str = llm_manager.ask(reasoning_prompt)
        
        # Extract matches
        for page in pages:
            p_num = str(page["page_number"])
            if p_num in relevant_pages_str:
                retrieved_results.append({
                    "doc_name": doc_name,
                    "page_number": page["page_number"],
                    "content": page["text"]
                })

    # Fallback: If reasoning is strict, grab page 1 as context default
    if not retrieved_results and trees:
        first_doc = trees[0]
        if first_doc.get("pages"):
            first_page = first_doc["pages"][0]
            retrieved_results.append({
                "doc_name": first_doc["doc_name"],
                "page_number": first_page["page_number"],
                "content": first_page["text"]
            })

    return retrieved_results