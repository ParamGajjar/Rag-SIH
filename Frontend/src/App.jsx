import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  ArrowUp,
  HelpCircle,
  User,
  Shield,
  Info,
  Menu,
  FileText,
  CheckCircle,
  FlaskConical,
  Loader2,
  AlertCircle
} from 'lucide-react';

import { api } from './services/api';
import { HealthBadge } from './components/HealthBadge';
import { SourceCard } from './components/SourceCard';
import { DocumentSidebar } from './components/DocumentSidebar';

function App() {
  const [query, setQuery] = useState('');
  const [isChatActive, setIsChatActive] = useState(false);
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);

  // Document Management State
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // System & Health State
  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [errorAlert, setErrorAlert] = useState(null);

  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  // // Initial load & health polling
  // useEffect(() => {
  //   const fetchInitialData = async () => {
  //     const health = await api.checkHealth();
  //     setIsBackendOnline(health.status === 'ok')
  //     // setIsBackendOnline(health.status === 'online');

  //     if (health.status === 'online') {
  //       try {
  //         const docData = await api.listDocuments();
  //         setDocuments(docData.documents || []);
  //         setSelectedDocIds((docData.documents || []).map((d) => d.document_id));
  //       } catch (err) {
  //         console.error('Error fetching documents:', err);
  //       }
  //     }
  //   };

  //   fetchInitialData();
  //   const interval = setInterval(async () => {
  //     const health = await api.checkHealth();
  //     setIsBackendOnline(health.status === 'ok');
  //   }, 10000);

  //   return () => clearInterval(interval);
  // }, []);

  // Document Selection Handlers
  const handleToggleSelectDoc = (id) => {
    if (selectedDocIds.includes(id)) {
      setSelectedDocIds(selectedDocIds.filter((docId) => docId !== id));
    } else {
      setSelectedDocIds([...selectedDocIds, id]);
    }
  };

  const handleSelectAllDocs = () => {
    setSelectedDocIds(documents.map((d) => d.document_id));
  };

  const handleClearDocSelection = () => {
    setSelectedDocIds([]);
  };

  // PDF Upload Handler
  const handleUploadFile = async (file) => {
    setIsUploading(true);
    setErrorAlert(null);
    try {
      const result = await api.uploadDocument(file);
      const docData = await api.listDocuments();
      setDocuments(docData.documents || []);
      
      // Auto-select newly uploaded doc
      if (!selectedDocIds.includes(result.document_id)) {
        setSelectedDocIds([...selectedDocIds, result.document_id]);
      }
    } catch (err) {
      setErrorAlert(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Document Deletion Handler
  const handleDeleteDoc = async (id) => {
    setErrorAlert(null);
    try {
      await api.deleteDocument(id);
      setDocuments(documents.filter((d) => d.document_id !== id));
      setSelectedDocIds(selectedDocIds.filter((docId) => docId !== id));
    } catch (err) {
      setErrorAlert(`Delete failed: ${err.message}`);
    }
  };

  // Chat Query Submission Handler
  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    const userQuery = query.trim();
    if (!userQuery || isThinking) return;

    if (!isBackendOnline) {
      setErrorAlert('Backend server is offline. Please check backend connection.');
      return;
    }

    setIsChatActive(true);
    setErrorAlert(null);

    // User Message
    const userMsg = { type: 'user', text: userQuery };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setIsThinking(true);

    try {
      const chatRes = await api.sendChatMessage(
        userQuery,
        conversationId,
        selectedDocIds
      );

      if (chatRes.conversation_id) {
        setConversationId(chatRes.conversation_id);
      }

      const aiMsg = {
        type: 'ai',
        text: chatRes.answer,
        sources: chatRes.sources || [],
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setErrorAlert(`Chat error: ${err.message}`);
      const errorMsg = {
        type: 'ai',
        text: `Error: ${err.message}. Please verify backend status and try again.`,
        sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleQuickAction = (text) => {
    setQuery(text);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      {/* Navbar */}
      <nav className="bg-white border-b border-slate-200 px-4 md:px-6 py-3.5 flex items-center justify-between sticky top-0 z-20 shadow-2xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
          >
            <Menu size={20} />
          </button>
          <div className="bg-blue-600 text-white p-2 rounded-xl shadow-xs">
            <Shield size={22} />
          </div>
          <span className="text-lg font-extrabold text-slate-800 tracking-tight">
            StandardAssist IN
          </span>
        </div>

        <div className="flex items-center gap-4">
          <HealthBadge isOnline={isBackendOnline} />
          <button className="text-slate-500 hover:text-slate-700 p-1">
            <HelpCircle size={20} />
          </button>
          <div className="h-8 w-8 bg-slate-200 rounded-full flex items-center justify-center text-slate-600 font-semibold text-xs">
            <User size={18} />
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <DocumentSidebar
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleSelectDoc={handleToggleSelectDoc}
          onSelectAllDocs={handleSelectAllDocs}
          onClearDocSelection={handleClearDocSelection}
          onUploadFile={handleUploadFile}
          onDeleteDoc={handleDeleteDoc}
          isUploading={isUploading}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        {/* Content Area */}
        <main className="flex-1 flex flex-col h-[calc(100vh-61px)] overflow-y-auto relative">
          {/* Error Alert Banner */}
          {errorAlert && (
            <div className="mx-4 mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center justify-between shadow-2xs animate-fade-in">
              <div className="flex items-center gap-2">
                <AlertCircle size={16} className="text-rose-500 flex-shrink-0" />
                <span>{errorAlert}</span>
              </div>
              <button
                onClick={() => setErrorAlert(null)}
                className="text-rose-400 hover:text-rose-600 text-xs font-bold"
              >
                Dismiss
              </button>
            </div>
          )}

          {!isChatActive ? (
            /* Landing View */
            <div className="flex-1 max-w-3xl mx-auto px-4 py-12 flex flex-col items-center text-center justify-center">
              <div className="bg-blue-100/70 text-blue-700 px-4 py-1.5 rounded-full text-xs font-semibold mb-6 inline-flex items-center gap-2 border border-blue-200/50">
                <Info size={15} /> AI-Powered Indian Standards & BIS Compliance Guide
              </div>
              
              <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">
                How can I assist you with Indian Standards today?
              </h2>
              
              <p className="text-sm md:text-base text-slate-600 mb-8 max-w-xl leading-relaxed">
                Upload safety codes, ISI compliance standards, or testing manuals for intelligent, grounded AI answers with verified source citations.
              </p>

              {/* Initial Query Box */}
              <form onSubmit={handleSearch} className="w-full max-w-2xl relative mb-12 shadow-md shadow-slate-200/60 rounded-2xl group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500" size={20} />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question or search Indian Standards..."
                  className="w-full pl-12 pr-16 py-4 rounded-2xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-base transition-all"
                />
                <button
                  type="submit"
                  disabled={!query.trim() || isThinking || !isBackendOnline}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-40"
                >
                  <ArrowUp size={18} />
                </button>
              </form>

              {/* Quick Action Cards */}
              <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                <button
                  onClick={() => handleQuickAction("What standard applies to occupational safety and health audit?")}
                  className="bg-white p-4 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all group text-left"
                >
                  <FileText className="text-blue-500 mb-2.5 group-hover:scale-105 transition-transform" size={22} />
                  <h3 className="font-bold text-xs text-slate-800 mb-1">Safety Audits</h3>
                  <p className="text-[11px] text-slate-500">Discover guidelines for occupational health and safety codes.</p>
                </button>

                <button
                  onClick={() => handleQuickAction("What is the certification process for ISI marking?")}
                  className="bg-white p-4 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all group text-left"
                >
                  <CheckCircle className="text-emerald-500 mb-2.5 group-hover:scale-105 transition-transform" size={22} />
                  <h3 className="font-bold text-xs text-slate-800 mb-1">ISI Certification</h3>
                  <p className="text-[11px] text-slate-500">Learn about mandatory ISI marking schemes and documentation.</p>
                </button>

                <button
                  onClick={() => handleQuickAction("Where can I test drinking water parameters?")}
                  className="bg-white p-4 rounded-2xl border border-slate-200 hover:border-blue-300 hover:shadow-sm transition-all group text-left"
                >
                  <FlaskConical className="text-purple-500 mb-2.5 group-hover:scale-105 transition-transform" size={22} />
                  <h3 className="font-bold text-xs text-slate-800 mb-1">Testing & Labs</h3>
                  <p className="text-[11px] text-slate-500">Find BIS recognized laboratory testing parameters.</p>
                </button>
              </div>
            </div>
          ) : (
            /* Active Chat View */
            <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 pt-6 pb-28">
              <div className="flex-1 overflow-y-auto space-y-6">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                  >
                    {msg.type === 'ai' && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-3 flex-shrink-0 mt-1">
                        <Shield size={16} />
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                        msg.type === 'user'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-white border border-slate-200/90 shadow-2xs text-slate-800'
                      }`}
                    >
                      <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                      {msg.type === 'ai' && <SourceCard sources={msg.sources} />}
                    </div>
                  </div>
                ))}

                {isThinking && (
                  <div className="flex items-center gap-3 text-slate-500 text-xs italic animate-fade-in">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                      <Shield size={16} />
                    </div>
                    <div className="bg-white p-3 rounded-2xl border border-slate-200 flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin text-blue-600" />
                      <span>Analyzing documents & generating response...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent pt-6 pb-5 px-4 z-10 lg:pl-80">
                <div className="max-w-2xl mx-auto">
                  <form
                    onSubmit={handleSearch}
                    className="relative shadow-lg shadow-slate-200/60 rounded-2xl bg-white border border-slate-200 group"
                  >
                    <textarea
                      rows={1}
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask another question... (Enter to send, Shift+Enter for newline)"
                      className="w-full pl-4 pr-12 py-3.5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm resize-none"
                    />
                    <button
                      type="submit"
                      disabled={!query.trim() || isThinking || !isBackendOnline}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-xs disabled:opacity-40"
                    >
                      <ArrowUp size={16} />
                    </button>
                  </form>
                  <div className="text-center mt-2 text-[11px] text-slate-400">
                    StandardAssist IN retrieves context strictly from uploaded Indian Standard PDFs.
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
