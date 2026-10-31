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
    <div className="mt-2.5 rounded-lg border border-slate-200/90 bg-slate-50/70 overflow-hidden transition-all text-xs">
      {/* Prominent Expand/Collapse Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-100/70 hover:bg-slate-100 text-left transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-1.5 font-medium text-slate-700">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>{evidence.title}</span>
        </div>
        <div className="flex items-center gap-1 font-semibold text-emerald-700 text-[11px]">
          <span>{isOpen ? 'Hide the numbers' : 'Show the numbers'}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {/* Collapsed/Expanded Content */}
      {isOpen && (
        <div className="p-3 border-t border-slate-200/80 space-y-2">
          {evidence.summary && (
            <p className="text-slate-600 bg-white p-2 rounded border border-slate-200/60 leading-relaxed text-[11px]">
              {evidence.summary}
            </p>
          )}

          {evidence.table_rows && evidence.table_rows.length > 0 && (
            <div className="overflow-x-auto rounded border border-slate-200 bg-white">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 text-[10px] uppercase tracking-wider">
                  <tr>
                    {evidence.table_headers.map((h, i) => (
                      <th key={i} className="py-1.5 px-2.5 whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {evidence.table_rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50">
                      {evidence.table_headers.map((colKey, cIdx) => {
                        const val = row[colKey] ?? '-';
                        const isDelta = colKey.toLowerCase().includes('delta');
                        let textStyle = 'text-slate-700';

                        if (isDelta) {
                          const s = String(val);
                          if (s.startsWith('+')) textStyle = 'text-emerald-700 font-bold';
                          else if (s.startsWith('-')) textStyle = 'text-red-600 font-bold';
                        }

                        return (
                          <td key={cIdx} className={`py-1.5 px-2.5 whitespace-nowrap ${textStyle}`}>
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
            <div className="text-[10px] text-slate-400 italic text-right pt-0.5">
              {evidence.confidence_note}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
