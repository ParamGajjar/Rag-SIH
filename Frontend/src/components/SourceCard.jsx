import React, { useState } from 'react';
import { FileText, ChevronDown } from 'lucide-react';

export function SourceCard({ sources }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 pt-3 border-t border-slate-100">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-xs font-semibold text-slate-600 hover:text-blue-600 transition-colors py-1 px-2 rounded-lg hover:bg-slate-100/60"
      >
        <span className="flex items-center gap-1.5">
          <FileText size={15} className="text-blue-500" />
          <span>Sources & Citations ({sources.length})</span>
        </span>
        <ChevronDown
          size={14}
          className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="mt-2.5 space-y-2.5 bg-slate-50/80 p-3 rounded-xl border border-slate-200/80">
          {sources.map((src, idx) => {
            const scorePct = Math.round((src.score || 0) * 100);
            return (
              <div
                key={idx}
                className="bg-white p-3 rounded-lg border border-slate-200/70 shadow-2xs hover:border-blue-300 transition-all text-xs"
              >
                <div className="flex items-center justify-between font-semibold text-slate-800 mb-1.5">
                  <span className="flex items-center gap-1.5 truncate max-w-[70%]">
                    <FileText size={13} className="text-blue-500 flex-shrink-0" />
                    <span className="truncate">{src.document}</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px]">
                      Page {src.page}
                    </span>
                    <span className="bg-blue-50 text-blue-700 font-bold px-2 py-0.5 rounded text-[10px]">
                      {scorePct}% match
                    </span>
                  </div>
                </div>
                <p className="text-slate-600 leading-relaxed italic bg-slate-50/60 p-2 rounded border border-slate-100 text-[11px]">
                  "{src.content}"
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
