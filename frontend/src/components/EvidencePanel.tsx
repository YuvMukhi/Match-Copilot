import React, { useState } from 'react';
import type { EvidencePayload } from '../types';
import { ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';

interface EvidencePanelProps {
  evidence: EvidencePayload;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence }) => {
  // Collapsed by default as per UX principles
  const [isOpen, setIsOpen] = useState<boolean>(false);

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/80 overflow-hidden transition-all text-sm">
      {/* Prominent Expand/Collapse Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-100/80 hover:bg-slate-200/70 text-left transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2 font-semibold text-slate-800 text-xs sm:text-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{evidence.title}</span>
        </div>
        <div className="flex items-center gap-1 font-bold text-emerald-700 text-xs sm:text-sm bg-white px-2 py-0.5 rounded-md border border-slate-200 shadow-2xs">
          <span>{isOpen ? 'Hide numbers' : 'Show numbers'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Collapsed/Expanded Content */}
      {isOpen && (
        <div className="p-3.5 border-t border-slate-200/90 space-y-2.5">
          {evidence.summary && (
            <p className="text-slate-700 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed text-xs sm:text-sm font-sans">
              {evidence.summary}
            </p>
          )}

          {evidence.table_rows && evidence.table_rows.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-2xs">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200 text-xs uppercase tracking-wider">
                  <tr>
                    {evidence.table_headers.map((h, i) => (
                      <th key={i} className="py-2 px-3 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-xs sm:text-sm">
                  {evidence.table_rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50 transition-colors">
                      {evidence.table_headers.map((colKey, cIdx) => {
                        const val = row[colKey] ?? '-';
                        const isDelta = colKey.toLowerCase().includes('delta');
                        let textStyle = 'text-slate-800 font-medium';

                        if (isDelta) {
                          const s = String(val);
                          if (s.startsWith('+')) textStyle = 'text-emerald-700 font-black';
                          else if (s.startsWith('-')) textStyle = 'text-red-600 font-black';
                        }

                        return (
                          <td key={cIdx} className={`py-2 px-3 whitespace-nowrap ${textStyle}`}>
                            {String(val)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Confidence Note */}
          {evidence.confidence_note && (
            <div className="text-xs text-slate-500 italic text-right pt-0.5">
              {evidence.confidence_note}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
