"""PageIndex local tree indexing module."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import pageindex
from app.config import Config
from app.utils.pdf_loader import extract_pdf_pages
from app.llm.llm_manager import llm_manager

logger = logging.getLogger(__name__)

def generate_tree_structure(doc_name: str, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Uses LLM reasoning (via PageIndex structure principles) to create an organized hierarchical tree.
    
    PageIndex builds tree nodes using structured document summaries rather than chunk embeddings.
    """
    summary_prompt = (
        f"Generate a hierarchical index/outline for document '{doc_name}'.\n"
        f"The document has {len(pages)} pages.\n"
        "Return a simple JSON structure with main sections, brief summaries, and page ranges.\n"
        "Example format:\n"
        "{\n"
        '  "doc_id": "pi-abc123def456",\n'
        '  "status": "completed",\n'
        '  "retrieval_ready": true,\n'
        '  "result": [\n'
        "    {\n"
        '      "title": "Financial Stability",\n'
        '      "node_id": "0006",\n'
        '      "page_index": 21,\n'
        '      "prefix_summary": "The Federal Reserve maintains financial stability through comprehensive monitoring...",\n'
        '      "nodes": [\n'
        "        {\n"
        '          "title": "Monitoring Financial Vulnerabilities",\n'
        '          "node_id": "0007",\n'
        '          "page_index": 22,\n'
        '          "summary": "The Federal Reserve\'s monitoring focuses on identifying and assessing potential risks..."\n'
        "        },\n"
        "        {\n"
        '          "title": "Domestic and International Cooperation and Coordination",\n'
        '          "node_id": "0008",\n'
        '          "page_index": 28,\n'
        '          "summary": "In 2023, the Federal Reserve collaborated internationally with central banks..."\n'
        "        }\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}"
    )

#     import textwrap

# summary_prompt = textwrap.dedent(f"""\
# Generate a hierarchical index/outline for document '{doc_name}'.
# The document has {len(pages)} pages.
# Return a simple JSON structure with main sections, brief summaries, and page ranges.
# Example format:
# {{
#   "doc_id": "pi-abc123def456",
#   "status": "completed",
#   "retrieval_ready": true,
#   "result": [
#     {{
#       "title": "Financial Stability",
#       "node_id": "0006",
#       "page_index": 21,
#       "prefix_summary": "The Federal Reserve maintains financial stability through comprehensive monitoring...",
#       "nodes": [
#         {{
#           "title": "Monitoring Financial Vulnerabilities",
#           "node_id": "0007",
#           "page_index": 22,
#           "summary": "The Federal Reserve's monitoring focuses on identifying and assessing potential risks..."
#         }},
#         {{
#           "title": "Domestic and International Cooperation and Coordination",
#           "node_id": "0008",
#           "page_index": 28,
#           "summary": "In 2023, the Federal Reserve collaborated internationally with central banks..."
#         }}
#       ]
#     }}
#   ]
# }}
# """)



    # summary_prompt = (
    #     f"Generate a hierarchical index/outline for document '{doc_name}'.\n"
    #     f"The document has {len(pages)} pages.\n"
    #     "Return a simple JSON structure with main sections, brief summaries, and page ranges.\n"
    #     "Example format:\n"
    #     "{\n"
    #     '  "title": "Document Title",\n'
    #     '  "sections": [\n'
    #     '    {"title": "Introduction", "pages": [1, 2], "summary": "Overview of..."}\n'
    #     "  ]\n"
    #     "}"
    # )
    
    llm_response = llm_manager.ask(summary_prompt)
    
    # Simple fallback structure if JSON generation needs basic wrapper
    return {
        "doc_name": doc_name,
        "total_pages": len(pages),
        "llm_tree_raw": llm_response,
        "pages": pages
    }

# def index_document(pdf_path: Path) -> Path:
#     """Index a single PDF file locally and save the tree structure as JSON."""
#     logger.info(f"Processing PDF: {pdf_path.name}")
    
#     # 1. Extract text and pages
#     pages = extract_pdf_pages(pdf_path)
    
#     # 2. Build local PageIndex reasoning tree structure
#     pi = PageIndex()
#     tree_data = generate_tree_structure(pdf_path.name, pages)
    
#     # 3. Save index to disk
#     output_filename = Config.INDEXES_DIR / f"{pdf_path.stem}_index.json"
#     with open(output_filename, "w", encoding="utf-8") as f:
#         json.dump(tree_data, f, indent=2)
        
#     logger.info(f"Successfully saved PageIndex structure to: {output_filename}")
#     return output_filename

def index_document(pdf_path: Path) -> Path:
    """Index a single PDF file locally and save the tree structure as JSON."""
    logger.info(f"Processing PDF: {pdf_path.name}")
    
    # 1. Extract text and pages
    pages = extract_pdf_pages(pdf_path)
    
    # 2. Build local tree structure using LLM reasoning
    tree_data = generate_tree_structure(pdf_path.name, pages)
    
    # 3. Save index to disk
    output_filename = Config.INDEXES_DIR / f"{pdf_path.stem}_index.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, indent=2)
        
    logger.info(f"Successfully saved PageIndex structure to: {output_filename}")
    return output_filename

def index_all_documents() -> List[Path]:
    """Find and index all PDFs inside data/documents/."""
    pdf_files = list(Config.DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {Config.DOCUMENTS_DIR}")
        return []

    saved_indexes = []
    for pdf_path in pdf_files:
        index_file = index_document(pdf_path)
        saved_indexes.append(index_file)
        
    return saved_indexes