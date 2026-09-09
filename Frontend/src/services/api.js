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

      const cleanTextContent = (str) => {
        if (!str || typeof str !== 'string') return '';
        let text = str.replace(/\/uni([0-9A-Fa-f]{4})/g, (_, hex) => {
          try {
            return String.fromCharCode(parseInt(hex, 16));
          } catch {
            return '';
          }
        });
        text = text.replace(/\/g[0-9A-Fa-f]+/g, ' ');
        text = text.replace(/\/[a-zA-Z0-9]+/g, ' ');
        text = text.replace(/[⌂\u2302\u2300-\u23ff\uf000-\uf8ff\ud800-\udfff]/g, '');

        const legacyPatterns = [
          /jftLV[^\s]*/gi, /laö/gi, /Mhö/gi, /,yö[^\s]*/gi, /vlk/gi, /Hkkx/gi, /\[k\.M/gi, /mi&\[k\.M/gi,
          /izkf[^\s]*/gi, /c`gLIifrokj/gi, /fnLEcj/gi, /vxzgk;n[^\s]*/gi, /7147 GI\/\d+/gi,
          /REGD\.\s*NO\.[^\s]*/gi, /EXTRAORDINARY/gi, /PUBLISHED BY AUTHORITY/gi,
          /PART II—Section 3—Sub-section \(ii\)/gi, /THE GAZETTE OF INDIA : EXTRAORDINARY/gi,
          /\[P ART II—S EC \. 3\(ii\)\]/gi
        ];
        for (const pat of legacyPatterns) {
          text = text.replace(pat, ' ');
        }
        text = text.replace(/(\b[^\s]+\b)(?:\s+\1){2,}/gi, '$1');
        text = text.replace(/(?:\.\s*){2,}/g, '... ');
        text = text.replace(/\s+/g, ' ').trim();
        return text;
      };

      const extractRelevantSnippet = (str, maxLen = 350) => {
        const cleaned = cleanTextContent(str);
        if (!cleaned) return '';
        const matches = cleaned.match(/(?:आई एस|IS)\s*\d+.*?(?=(?:आई एस|IS|$))/gi);
        if (matches && matches.length > 0) {
          let snippet = matches.slice(0, 4).map((m) => m.trim()).join(' | ');
          if (snippet.length > maxLen) {
            snippet = snippet.substring(0, maxLen) + '...';
          }
          return snippet;
        }
        if (cleaned.length > maxLen) {
          return cleaned.substring(0, maxLen) + '...';
        }
        return cleaned;
      };

      // Standardize sources payload for React SourceCard component
      const structuredSources = (data.context && data.context.length > 0)
        ? data.context.map((c) => ({
            document: c.doc_name || c.document || 'Document',
            page: c.page_number || c.page || 1,
            content: extractRelevantSnippet(c.content || ''),
            score: c.score !== undefined ? c.score : 0.95,
          }))
        : (data.sources || []).map((s) => {
            if (typeof s === 'object' && s !== null) {
              return {
                document: s.document || s.doc_name || 'Document',
                page: s.page || s.page_number || 1,
                content: extractRelevantSnippet(s.content || ''),
                score: s.score !== undefined ? s.score : 0.95,
              };
            }
            const strVal = String(s);
            const parts = strVal.split('\ncontent :\n');
            const header = parts[0] || '';
            const rawContent = parts[1] || strVal;
            const docMatch = header.match(/^(.*?)\s*—\s*page\s*(\d+)/i);
            return {
              document: docMatch ? (docMatch[1].strip ? docMatch[1].strip() : docMatch[1].trim()) : 'Document',
              page: docMatch ? parseInt(docMatch[2], 10) : 1,
              content: extractRelevantSnippet(rawContent),
              score: 0.95,
            };
          });

      // Standardize output payload for React UI components
      return {
        answer: data.answer || '',
        sources: structuredSources,
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