import React, { useState } from 'react';
import type { MatchState, TeamDetail } from '../types';
import { ChevronRight } from 'lucide-react';

interface TeamTableProps {
  teamDetail: TeamDetail | null;
  matchState: MatchState | null;
  loading: boolean;
}

export const TeamTable: React.FC<TeamTableProps> = ({ teamDetail, matchState, loading }) => {
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);

  if (loading && !teamDetail) {
    return (
      <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs animate-pulse space-y-2">
        <div className="h-4 bg-slate-200 rounded w-1/4 mb-2"></div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-7 bg-slate-100 rounded"></div>
        ))}
      </div>
    );
  }

  if (!teamDetail) return null;

  const breakdownMap = new Map(
    matchState?.team_breakdown?.map((item) => [item.player_id, item]) || []
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Squad Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between text-xs">
        <span className="font-bold text-slate-800">
          Squad ({teamDetail.players.length} Players)
        </span>
        <span className="text-slate-400">Click player to view events</span>
      </div>

      {/* Players List */}
      <div className="divide-y divide-slate-100 text-xs">
        {teamDetail.players.map((p) => {
          const breakdown = breakdownMap.get(p.id);
          const pts = breakdown?.total_points ?? p.current_points ?? 0;
          const isSelected = selectedPlayerId === p.id;

          return (
            <div key={p.id}>
              <div
                onClick={() => setSelectedPlayerId(isSelected ? null : p.id)}
                className={`px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors ${
                  isSelected ? 'bg-emerald-50/50' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <ChevronRight
                    className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
                      isSelected ? 'rotate-90 text-emerald-600' : ''
                    }`}
                  />
                  <span className="font-medium text-slate-900">{p.name}</span>
                  <span className="text-[10px] text-slate-500 font-semibold bg-slate-100 px-1.5 py-0.2 rounded">
                    {p.role}
                  </span>
                  {p.is_captain && (
                    <span className="text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 px-1.5 py-0.2 rounded">
                      C (2x)
                    </span>
                  )}
                  {p.is_vice_captain && (
                    <span className="text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300 px-1.5 py-0.2 rounded">
                      VC (1.5x)
                    </span>
                  )}
                </div>

                <div className="font-mono font-bold text-slate-800">
                  {pts.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">pts</span>
                </div>
              </div>

              {/* Expanded Breakdown */}
              {isSelected && (
                <div className="bg-slate-50/80 px-8 py-2 border-t border-b border-slate-100 text-[11px] text-slate-600">
                  {breakdown && breakdown.events && breakdown.events.length > 0 ? (
                    <ul className="list-disc list-inside space-y-0.5 font-mono text-[10px] text-slate-600">
                      {breakdown.events.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-slate-400 italic">Starting XI bonus points (4.0 pts)</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
