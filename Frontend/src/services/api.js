// services/api.js


// const API_BASE_URL = process.env.VITE_APP_API_BASE_URL || 'http://localhost:8000';
// const NEW_BACKEND_URL = process.env.VITE_APP_NEW_BACKEND_URL || 'http://localhost:5000/chat'; // Adjust port/path as per your new server setup
// services/api.js

const OLD_BACKEND_URL = 'http://localhost:5000';
const NEW_BACKEND_URL = 'http://localhost:8000';

export const api = {
  /**
   * Health check endpoint targeting the primary (5000) backend, falling back to 8000.
   */
  async checkHealth() {
    try {
      const response = await fetch(`${NEW_BACKEND_URL}/health`);
      console.log(response);
      console.log(response.ok);
      
      
      if (response.ok) {
        return await response.json();
      }
      throw new Error(`Port 5000 failed with status ${response.status}`);
    } catch (newError) {
      console.warn('Port 5000 offline, checking Port 8000...', newError);
      try {
        const oldResponse = await fetch(`${OLD_BACKEND_URL}/health`);
        if (oldResponse.ok) {
          return await oldResponse.json();
        }
      } catch (oldError) {
        return { status: 'offline', error: oldError.message };
      }
    }
  },

  // async checkHealth() {
  //   // Immediately return the matching schema expected by your React app
  //   return Promise.resolve({
  //     status: "ok"
  //   });
  // },

  /**
   * Hybrid Chat Request Implementation:
   * First attempts POST to New Backend on port 5000 (/ask).
   * If it fails, falls back to POST on port 8000 (/chat).
   */
  async sendChatMessage(query, conversationId = null, selectedDocIds = []) {
    // --- 1. TRY NEW PAGEINDEX BACKEND (Port 5000) ---
    try {
      console.log('Attempting request to Vectorless RAG (Port 5000)...');
      const newBackendResponse = await fetch(`${NEW_BACKEND_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: query,
        }),
      });

      if (!newBackendResponse.ok) {
        throw new Error(
          `New backend returned error status: ${newBackendResponse.status}`
        );
      }

      const data = await newBackendResponse.json();

      // Standardize output payload for React UI components
      return {
        answer: data.answer || '',
        sources: data.sources || [],
        conversation_id: conversationId,
        context: data.context || [],
      };
    } catch (newBackendError) {
      console.warn(
        'New backend failed or returned an error. Falling back to Old Backend...',
        newBackendError
      );

      // --- 2. FALLBACK TO OLD BACKEND (Port 8000) ---
      try {
        const oldBackendResponse = await fetch(`${OLD_BACKEND_URL}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: query,
            conversation_id: conversationId,
            document_ids: selectedDocIds,
          }),
        });

        if (!oldBackendResponse.ok) {
          throw new Error(
            `Old backend failed with status: ${oldBackendResponse.status}`
          );
        }

        return await oldBackendResponse.json();
      } catch (oldBackendError) {
        console.error('Both New and Old backends failed to process request.');
        throw new Error(
          `Primary and fallback services failed: ${oldBackendError.message}`
        );
      }
    }
  },

  /**
   * Document Management APIs
   * Tries new backend (5000) first, falls back to old backend (8000).
   */
  async listDocuments() {
    try {
      const response = await fetch(`${NEW_BACKEND_URL}/documents`);
      if (response.ok) return await response.json();
      throw new Error('New backend /documents failed');
    } catch {
      const response = await fetch(`${OLD_BACKEND_URL}/documents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }
      return await response.json();
    }
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${NEW_BACKEND_URL}/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      if (response.ok) return await response.json();
      throw new Error('New backend upload failed');
    } catch {
      const response = await fetch(`${OLD_BACKEND_URL}/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Failed to upload document: ${response.statusText}`);
      }
      return await response.json();
    }
  },

  async deleteDocument(documentId) {
    try {
      const response = await fetch(`${NEW_BACKEND_URL}/documents/${documentId}`, {
        method: 'DELETE',
      });
      if (response.ok) return await response.json();
      throw new Error('New backend delete failed');
    } catch {
      const response = await fetch(`${OLD_BACKEND_URL}/documents/${documentId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`Failed to delete document: ${response.statusText}`);
      }
      return await response.json();
    }
  },

  /**
   * Trigger indexing on demand for the PageIndex pipeline.
   */
  async triggerIndexing() {
    const response = await fetch(`${NEW_BACKEND_URL}/vector_store`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Indexing failed: ${response.statusText}`);
    }
    return await response.json();
  },
};