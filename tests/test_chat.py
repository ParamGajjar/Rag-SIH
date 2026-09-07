import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from backend.app.main import app
from backend.app.routes.chat import NO_CONTEXT_FALLBACK_ANSWER

client = TestClient(app)

def make_pdf_bytes(text_content: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, text_content)
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def test_chat_empty_message():
    """Empty question string should return 400 Bad Request"""
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "Message cannot be empty" in response.json()["detail"]


def test_chat_no_documents_fallback():
    """When vector store is empty, chat endpoint returns grounded fallback answer with sources: []"""
    response = client.post("/api/chat", json={"message": "What is IS 14489?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == NO_CONTEXT_FALLBACK_ANSWER
    assert data["sources"] == []
    assert "conversation_id" in data


def test_chat_unrelated_question_fallback():
    """When no retrieved chunks pass similarity threshold, returns fallback answer with 0 LLM calls"""
    # Upload test document
    pdf_bytes = make_pdf_bytes("Indian Standard IS 14489 covers occupational safety audit.")
    up_res = client.post("/api/documents/upload", files={"file": ("is_14489.pdf", pdf_bytes, "application/pdf")})
    doc_id = up_res.json()["document_id"]

    try:
        # Ask completely unrelated question
        response = client.post("/api/chat", json={"message": "What is the capital of Mars?"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == NO_CONTEXT_FALLBACK_ANSWER
        assert data["sources"] == []
    finally:
        client.delete(f"/api/documents/{doc_id}")


@patch("backend.app.routes.chat.groq_llm.generate_grounded_response")
def test_chat_valid_question_with_mock_llm(mock_llm):
    """Valid question with matching document context returns grounded response and authentic sources"""
    mock_llm.return_value = "Indian Standard IS 14489:2018 covers the code of practice on occupational safety and health audit."

    pdf_bytes = make_pdf_bytes("Indian Standard IS 14489:2018 covers occupational safety audit guidelines.")
    up_res = client.post("/api/documents/upload", files={"file": ("safety_code.pdf", pdf_bytes, "application/pdf")})
    doc_id = up_res.json()["document_id"]

    try:
        response = client.post(
            "/api/chat",
            json={"message": "What does Indian Standard IS 14489:2018 cover?", "conversation_id": "session_test_123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "session_test_123"
        assert "IS 14489:2018" in data["answer"]
        assert len(data["sources"]) >= 1

        first_source = data["sources"][0]
        assert first_source["document"] == "safety_code.pdf"
        assert first_source["page"] == 1
        assert "IS 14489:2018" in first_source["content"]
        assert isinstance(first_source["score"], float)

        # Verify LLM was called with retrieved context
        assert mock_llm.called
    finally:
        client.delete(f"/api/documents/{doc_id}")


@patch("backend.app.routes.chat.groq_llm.generate_grounded_response")
def test_chat_missing_api_key(mock_llm):
    """Missing GROQ_API_KEY should return 500 Internal Server Error"""
    mock_llm.side_effect = ValueError("GROQ_API_KEY environment variable is not configured.")

    pdf_bytes = make_pdf_bytes("Emergency helpline contact number is 108.")
    up_res = client.post("/api/documents/upload", files={"file": ("helpline.pdf", pdf_bytes, "application/pdf")})
    doc_id = up_res.json()["document_id"]

    try:
        response = client.post("/api/chat", json={"message": "What is the helpline number?"})
        assert response.status_code == 500
        assert "Groq API key is not configured" in response.json()["detail"]
    finally:
        client.delete(f"/api/documents/{doc_id}")


@patch("backend.app.routes.chat.groq_llm.generate_grounded_response")
def test_chat_llm_service_failure(mock_llm):
    """Groq service failure / timeout should return 502 Bad Gateway"""
    mock_llm.side_effect = RuntimeError("Groq API service encountered an error.")

    pdf_bytes = make_pdf_bytes("Emergency helpline contact number is 108.")
    up_res = client.post("/api/documents/upload", files={"file": ("helpline.pdf", pdf_bytes, "application/pdf")})
    doc_id = up_res.json()["document_id"]

    try:
        response = client.post("/api/chat", json={"message": "What is the helpline number?"})
        assert response.status_code == 502
        assert "Groq LLM service failed" in response.json()["detail"]
    finally:
        client.delete(f"/api/documents/{doc_id}")
