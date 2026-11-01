import React, { useState } from 'react';
import type { MatchState, TeamDetail } from '../types';
import { ChevronRight, Shield, Award } from 'lucide-react';

interface TeamTableProps {
  teamDetail: TeamDetail | null;
  matchState: MatchState | null;
  loading: boolean;
}

export const TeamTable: React.FC<TeamTableProps> = ({ teamDetail, matchState, loading }) => {
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);

  if (loading && !teamDetail) {
    return (
      <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm animate-pulse space-y-3">
        <div className="h-5 bg-slate-200 rounded w-1/4 mb-3"></div>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-10 bg-slate-100 rounded-xl"></div>
        ))}
      </div>
    );
  }

  if (!teamDetail) return null;

  const breakdownMap = new Map(
    matchState?.team_breakdown?.map((item) => [item.player_id, item]) || []
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden transition-all">
      {/* Squad Header */}
      <div className="px-5 py-3.5 border-b border-slate-100 bg-slate-50/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-600" />
          <span className="font-extrabold text-slate-900 text-sm sm:text-base">
            Playing XI ({teamDetail.players.length} Players)
          </span>
        </div>
        <span className="text-xs text-slate-500 font-medium hidden sm:inline">
          Tap player for point breakdown
        </span>
      </div>

      {/* Players List */}
      <div className="divide-y divide-slate-100">
        {teamDetail.players.map((p) => {
          const breakdown = breakdownMap.get(p.id);
          const pts = breakdown?.total_points ?? p.current_points ?? 0;
          const isSelected = selectedPlayerId === p.id;
          const isMI = p.team.toUpperCase().includes('MI') || p.team.toLowerCase().includes('mumbai');

          return (
            <div key={p.id}>
              <div
                onClick={() => setSelectedPlayerId(isSelected ? null : p.id)}
                className={`px-4 sm:px-5 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-50/80 transition-colors ${
                  isSelected ? 'bg-emerald-50/60' : ''
                }`}
              >
                <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
                  <ChevronRight
                    className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${
                      isSelected ? 'rotate-90 text-emerald-600' : ''
                    }`}
                  />

                  {/* Player Team Badge: MI or CSK */}
                  <span
                    className={`font-black text-[11px] px-2 py-0.5 rounded shadow-xs tracking-wider shrink-0 ${
                      isMI ? 'bg-blue-600 text-white' : 'bg-amber-400 text-slate-950'
                    }`}
                  >
                    {isMI ? 'MI' : 'CSK'}
                  </span>

                  {/* Player Name */}
                  <span className="font-bold text-slate-900 text-sm sm:text-base tracking-tight">
                    {p.name}
                  </span>

                  {/* Role Badge */}
                  <span className="text-xs text-slate-600 font-bold bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                    {p.role}
                  </span>

                  {/* Captain / Vice-Captain Badges */}
                  {p.is_captain && (
                    <span className="inline-flex items-center gap-1 text-xs font-black bg-gradient-to-r from-amber-500 to-amber-600 text-white px-2 py-0.5 rounded-md shadow-xs">
                      <Award className="w-3 h-3" />
                      C (2x)
                    </span>
                  )}
                  {p.is_vice_captain && (
                    <span className="inline-flex items-center gap-1 text-xs font-black bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-2 py-0.5 rounded-md shadow-xs">
                      VC (1.5x)
                    </span>
                  )}
                </div>

                {/* Fantasy Points */}
                <div className="font-mono font-black text-slate-900 text-base sm:text-lg shrink-0 pl-2">
                  {pts.toFixed(1)} <span className="text-xs font-semibold text-slate-400">pts</span>
                </div>
              </div>

              {/* Expanded Breakdown */}
              {isSelected && (
                <div className="bg-slate-50 px-6 sm:px-10 py-3 border-t border-b border-slate-100 text-xs sm:text-sm text-slate-700">
                  {breakdown && breakdown.events && breakdown.events.length > 0 ? (
                    <div>
                      <div className="font-semibold text-slate-600 mb-1.5 uppercase text-[11px] tracking-wider">
                        Scoring Ledger:
                      </div>
                      <ul className="list-disc list-inside space-y-1 font-mono text-xs sm:text-sm text-slate-700">
                        {breakdown.events.map((ev, i) => (
                          <li key={i}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div className="text-slate-500 italic">Starting XI match bonus (+4.0 pts)</div>
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
