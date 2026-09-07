import React, { useRef } from 'react';
import { UploadCloud, FileText, Trash2, CheckSquare, Square, X, Loader2, Info } from 'lucide-react';

export function DocumentSidebar({
  documents,
  selectedDocIds,
  onToggleSelectDoc,
  onSelectAllDocs,
  onClearDocSelection,
  onUploadFile,
  onDeleteDoc,
  isUploading,
  isOpen,
  onClose,
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Only PDF files are allowed.');
        return;
      }
      onUploadFile(file);
      e.target.value = '';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Only PDF files are allowed.');
        return;
      }
      onUploadFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const isAllSelected =
    documents.length > 0 && selectedDocIds.length === documents.length;

  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-30 w-80 bg-white border-r border-slate-200 flex flex-col transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
        <div className="flex items-center gap-2 font-bold text-slate-800">
          <FileText size={18} className="text-blue-600" />
          <span>Document Management</span>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden text-slate-400 hover:text-slate-600 p-1"
        >
          <X size={18} />
        </button>
      </div>

      {/* Upload Dropzone */}
      <div className="p-4 border-b border-slate-200">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
            isUploading
              ? 'border-blue-300 bg-blue-50/50 pointer-events-none'
              : 'border-slate-200 hover:border-blue-400 hover:bg-slate-50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="application/pdf,.pdf"
            className="hidden"
          />

          {isUploading ? (
            <div className="flex flex-col items-center py-2 text-blue-600">
              <Loader2 size={24} className="animate-spin mb-2" />
              <span className="text-xs font-semibold">Processing PDF & Vectorizing...</span>
            </div>
          ) : (
            <div className="flex flex-col items-center text-slate-500">
              <UploadCloud size={28} className="text-blue-500 mb-1.5" />
              <span className="text-xs font-semibold text-slate-700">Upload PDF Document</span>
              <span className="text-[11px] text-slate-400 mt-0.5">Drag & drop or click to browse</span>
            </div>
          )}
        </div>
      </div>

      {/* Selection Filter Bar */}
      <div className="px-4 py-2 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between text-xs">
        <span className="text-slate-500 font-medium">
          Filter ({selectedDocIds.length}/{documents.length} selected)
        </span>
        <div className="flex items-center gap-2">
          {isAllSelected ? (
            <button
              onClick={onClearDocSelection}
              className="text-blue-600 hover:underline font-semibold"
            >
              Clear
            </button>
          ) : (
            <button
              onClick={onSelectAllDocs}
              className="text-blue-600 hover:underline font-semibold"
            >
              Select All
            </button>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        {documents.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            <Info size={24} className="mx-auto mb-2 opacity-50" />
            <span>No documents indexed yet. Upload a PDF to start.</span>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.document_id);
            const fileSizeKb = Math.round(doc.file_size / 1024);

            return (
              <div
                key={doc.document_id}
                className={`p-3 rounded-xl border transition-all flex flex-col gap-2 ${
                  isSelected
                    ? 'bg-blue-50/40 border-blue-200'
                    : 'bg-white border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div
                    onClick={() => onToggleSelectDoc(doc.document_id)}
                    className="flex items-center gap-2 cursor-pointer truncate flex-1"
                  >
                    {isSelected ? (
                      <CheckSquare size={16} className="text-blue-600 flex-shrink-0" />
                    ) : (
                      <Square size={16} className="text-slate-400 flex-shrink-0" />
                    )}
                    <span className="font-semibold text-xs text-slate-800 truncate" title={doc.filename}>
                      {doc.filename}
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      if (window.confirm(`Delete document '${doc.filename}'?`)) {
                        onDeleteDoc(doc.document_id);
                      }
                    }}
                    className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                    title="Delete document"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pl-6">
                  <span>{doc.page_count} pages • {fileSizeKb} KB</span>
                  <span className="bg-emerald-100 text-emerald-700 font-bold px-1.5 py-0.5 rounded text-[10px]">
                    Ready
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
