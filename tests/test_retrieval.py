import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_store import document_registry

client = TestClient(app)

import io
from reportlab.pdfgen import canvas

# Helper function to generate a valid PDF with custom text content using reportlab
def make_pdf_bytes(text_content: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text_content)
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def setup_and_teardown_documents():
    """Setup deterministic test PDFs and clean up after test execution"""
    pdf_a_bytes = make_pdf_bytes("The emergency contact number for national safety helpline is 108.")
    pdf_b_bytes = make_pdf_bytes("Indian Standard IS 10500 specifies drinking water quality parameters.")

    res_a = client.post("/api/documents/upload", files={"file": ("safety_contact.pdf", pdf_a_bytes, "application/pdf")})
    res_b = client.post("/api/documents/upload", files={"file": ("water_standard.pdf", pdf_b_bytes, "application/pdf")})

    doc_a_id = res_a.json()["document_id"]
    doc_b_id = res_b.json()["document_id"]

    yield {"doc_a_id": doc_a_id, "doc_b_id": doc_b_id}

    # Teardown
    client.delete(f"/api/documents/{doc_a_id}")
    client.delete(f"/api/documents/{doc_b_id}")


def test_relevant_query_retrieval(setup_and_teardown_documents):
    """Relevant query must retrieve the chunk containing the answer with high confidence"""
    response = client.post(
        "/api/documents/retrieve",
        json={"query": "What is the emergency contact number?", "top_k": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    
    first_result = data["results"][0]
    assert "108" in first_result["content"]
    assert first_result["similarity_score"] >= 0.35
    assert first_result["filename"] == "safety_contact.pdf"


def test_irrelevant_query_thresholding(setup_and_teardown_documents):
    """Irrelevant question must return 0 results due to similarity threshold filtering"""
    response = client.post(
        "/api/documents/retrieve",
        json={
            "query": "What is the quantum physics calculation for hyperdrive speed on Mars?",
            "similarity_threshold": 0.50
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] == 0
    assert len(data["results"]) == 0


def test_document_id_filtering(setup_and_teardown_documents):
    """Retrieval with document_ids filter must only return chunks from specified document"""
    doc_b_id = setup_and_teardown_documents["doc_b_id"]

    response = client.post(
        "/api/documents/retrieve",
        json={
            "query": "drinking water quality parameters",
            "document_ids": [doc_b_id],
            "similarity_threshold": 0.20
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1

    for res in data["results"]:
        assert res["document_id"] == doc_b_id
        assert res["filename"] == "water_standard.pdf"


def test_top_k_parameter(setup_and_teardown_documents):
    """top_k parameter must restrict maximum returned chunk count"""
    response = client.post(
        "/api/documents/retrieve",
        json={"query": "standard safety guidelines", "top_k": 1, "similarity_threshold": 0.10}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 1


def test_metadata_preservation(setup_and_teardown_documents):
    """Retrieved chunks must preserve all required metadata fields"""
    response = client.post(
        "/api/documents/retrieve",
        json={"query": "emergency contact 108", "similarity_threshold": 0.20}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 1

    res = data["results"][0]
    assert "document_id" in res
    assert "filename" in res
    assert "page" in res
    assert "chunk_id" in res
    assert "content" in res
    assert "similarity_score" in res
    assert isinstance(res["similarity_score"], float)
