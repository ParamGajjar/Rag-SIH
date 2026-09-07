import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_store import document_registry

client = TestClient(app)

# Minimal valid PDF binary
VALID_PDF_BYTES = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj
4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
5 0 obj <</Length 55>> stream
BT
/F1 12 Tf
100 700 Td
(Test Indian Standard IS 14489 Document) Tj
ET
endstream endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000216 00000 n 
0000000287 00000 n 
trailer <</Size 6 /Root 1 0 R>>
startxref
393
%%EOF"""


def test_invalid_file_extension():
    """Uploading a non-PDF file should return 400 Bad Request"""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"Hello World", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_empty_file_upload():
    """Uploading an empty file should return 400 Bad Request"""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_corrupted_pdf_upload():
    """Uploading fake non-PDF content with .pdf extension should return 400 Bad Request"""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("fake.pdf", b"Not a real PDF header", "application/pdf")}
    )
    assert response.status_code == 400
    assert "File content is not a valid PDF document" in response.json()["detail"]


def test_valid_pdf_upload_and_deduplication():
    """Test valid PDF upload, metadata creation, and duplicate upload detection"""
    # 1. Initial Upload
    response = client.post(
        "/api/documents/upload",
        files={"file": ("sample_standard.pdf", VALID_PDF_BYTES, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample_standard.pdf"
    assert data["status"] == "ready"
    assert data["is_duplicate"] is False
    document_id = data["document_id"]
    page_count = data["page_count"]
    total_chunks = data["total_chunks"]

    # 2. Duplicate Upload (Same file content)
    dup_response = client.post(
        "/api/documents/upload",
        files={"file": ("sample_standard.pdf", VALID_PDF_BYTES, "application/pdf")}
    )
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["is_duplicate"] is True
    assert dup_data["document_id"] == document_id

    # 3. List Documents
    list_response = client.get("/api/documents")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total_count"] >= 1
    doc_ids = [d["document_id"] for d in list_data["documents"]]
    assert document_id in doc_ids

    # 4. Delete Document
    del_response = client.delete(f"/api/documents/{document_id}")
    assert del_response.status_code == 200
    assert del_response.json()["document_id"] == document_id

    # 5. Verify Deletion in Document Listing
    post_del_list = client.get("/api/documents").json()
    post_doc_ids = [d["document_id"] for d in post_del_list["documents"]]
    assert document_id not in post_doc_ids


def test_delete_non_existent_document():
    """Deleting a non-existent document ID should return 404 Not Found"""
    response = client.delete("/api/documents/doc_non_existent_12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
