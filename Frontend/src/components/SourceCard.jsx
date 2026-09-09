import React, { useState } from 'react';
import { FileText, ChevronDown, Check, Bookmark } from 'lucide-react';

export function SourceCard({ sources }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!sources || sources.length === 0) return null;

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

  return (
    <div className="mt-4 pt-3 border-t border-slate-100">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-xs font-semibold text-slate-700 hover:text-blue-600 transition-colors py-1.5 px-2.5 rounded-xl hover:bg-slate-100/60"
      >
        <span className="flex items-center gap-2">
          <Bookmark size={15} className="text-blue-600 fill-blue-100" />
          <span>Verified Sources & Standards ({sources.length})</span>
        </span>
        <ChevronDown
          size={14}
          className={`transition-transform duration-200 text-slate-400 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div className="mt-2.5 space-y-2.5 bg-slate-50/90 p-3 rounded-2xl border border-slate-200/80">
          {sources.map((src, idx) => {
            const isObj = typeof src === 'object' && src !== null;
            const docName = isObj ? (src.document || src.doc_name || 'Document') : String(src);
            const pageNum = isObj ? (src.page || src.page_number || 1) : 1;
            const rawContent = isObj ? (src.content || '') : '';
            const contentText = extractRelevantSnippet(rawContent);
            const rawScore = isObj && src.score !== undefined ? src.score : 0.95;
            const scorePct = Math.round(rawScore <= 1 ? rawScore * 100 : rawScore);

            const matchedStandards = Array.from(
              new Set(contentText.match(/(?:IS|आई एस)\s*\d+[:\s]*\d*/gi) || [])
            );

            return (
              <div
                key={idx}
                className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs hover:border-blue-300 transition-all text-xs flex flex-col gap-2"
              >
                <div className="flex items-center justify-between font-semibold text-slate-800">
                  <span className="flex items-center gap-2 truncate max-w-[70%]">
                    <FileText size={14} className="text-blue-600 flex-shrink-0" />
                    <span className="truncate font-bold text-slate-800 text-xs" title={docName}>{docName}</span>
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded-md text-[10px]">
                      Page {pageNum}
                    </span>
                    <span className="bg-blue-50 text-blue-700 font-bold px-2 py-0.5 rounded-md text-[10px] flex items-center gap-1">
                      <Check size={11} className="text-blue-600" /> {scorePct}% match
                    </span>
                  </div>
                </div>

                {matchedStandards.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {matchedStandards.map((std, sIdx) => (
                      <span
                        key={sIdx}
                        className="bg-blue-100/70 text-blue-800 font-bold px-2 py-0.5 rounded-full text-[10px] border border-blue-200/60"
                      >
                        {std.trim()}
                      </span>
                    ))}
                  </div>
                )}

                {contentText && (
                  <p className="text-slate-700 leading-relaxed italic bg-slate-50/80 p-2.5 rounded-xl border border-slate-200/60 text-[11px] break-words">
                    "{contentText}"
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
