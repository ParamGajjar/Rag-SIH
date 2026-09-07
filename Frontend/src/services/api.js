const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorData.error || response.statusText;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  /** Check backend server health status */
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
      if (!res.ok) return { status: 'offline' };
      const data = await res.json();
      return { status: data.status === 'ok' ? 'online' : 'offline' };
    } catch {
      return { status: 'offline' };
    }
  },

  /** Upload a PDF document */
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },

  /** List all indexed documents */
  async listDocuments() {
    const response = await fetch(`${API_BASE_URL}/api/documents`, {
      method: 'GET',
    });
    return handleResponse(response);
  },

  /** Delete indexed document by ID */
  async deleteDocument(documentId) {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },

  /** Send chat question and retrieve grounded AI response */
  async sendChatMessage(message, conversationId = null, documentIds = null) {
    const bodyPayload = {
      message,
      ...(conversationId && { conversation_id: conversationId }),
      ...(documentIds && documentIds.length > 0 && { document_ids: documentIds }),
    };

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bodyPayload),
    });
    return handleResponse(response);
  },
};
