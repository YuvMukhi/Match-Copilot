import React, { useState } from 'react';
import type { EvidencePayload } from '../types';
import { Table, ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';

interface EvidencePanelProps {
  evidence: EvidencePayload;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidence }) => {
  const [isOpen, setIsOpen] = useState<boolean>(true); // default open or prominent toggle

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50/80 overflow-hidden shadow-xs transition-all">
      {/* Toggle Button Banner */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-100/90 hover:bg-slate-200/80 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <Table className="w-4 h-4 text-emerald-700 shrink-0" />
          <span className="text-xs font-bold text-slate-800 tracking-tight flex items-center gap-1.5">
            <span>{evidence.title}</span>
            <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
              Verified Math
            </span>
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
          <span>{isOpen ? 'Hide the numbers' : 'Show the numbers'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Table & Confidence Panel */}
      {isOpen && (
        <div className="p-3 border-t border-slate-200 space-y-2.5">
          {/* Summary Banner */}
          {evidence.summary && (
            <p className="text-xs text-slate-700 bg-white p-2.5 rounded-md border border-slate-200 font-sans leading-relaxed">
              {evidence.summary}
            </p>
          )}

          {/* Structured Evidence Table */}
          {evidence.table_rows && evidence.table_rows.length > 0 && (
            <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200 text-[11px]">
                  <tr>
                    {evidence.table_headers.map((header, idx) => (
                      <th key={idx} className="py-2 px-2.5 whitespace-nowrap">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {evidence.table_rows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-slate-50 transition-colors">
                      {evidence.table_headers.map((colKey, colIdx) => {
                        const cellVal = row[colKey] ?? '-';
                        const isDelta = colKey.toLowerCase().includes('delta');
                        let cellClass = 'text-slate-700';

                        if (isDelta) {
                          const strVal = String(cellVal);
                          if (strVal.startsWith('+')) {
                            cellClass = 'text-emerald-700 font-bold';
                          } else if (strVal.startsWith('-')) {
                            cellClass = 'text-red-600 font-bold';
                          }
                        }

                        return (
                          <td key={colIdx} className={`py-2 px-2.5 whitespace-nowrap ${cellClass}`}>
                            {String(cellVal)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Confidence & Traceability Footer */}
          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Traceable: <strong>{evidence.tool_called}</strong> engine execution</span>
            </span>
            {evidence.confidence_note && (
              <span className="text-slate-400 italic">{evidence.confidence_note}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
