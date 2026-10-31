import React, { useState } from 'react';
import type { MatchState, TeamDetail } from '../types';
import { Users, Info, ChevronRight, Award } from 'lucide-react';

interface TeamTableProps {
  teamDetail: TeamDetail | null;
  matchState: MatchState | null;
  loading: boolean;
}

export const TeamTable: React.FC<TeamTableProps> = ({ teamDetail, matchState, loading }) => {
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);

  if (loading && !teamDetail) {
    return (
      <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/4 mb-3"></div>
        <div className="space-y-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-8 bg-slate-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!teamDetail) {
    return (
      <div className="bg-white rounded-xl p-6 border border-slate-200 text-center text-slate-500 text-sm">
        No team data available.
      </div>
    );
  }

  // Create lookup for detailed events from matchState breakdown if present
  const breakdownMap = new Map(
    matchState?.team_breakdown?.map((item) => [item.player_id, item]) || []
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-emerald-600" />
          <h2 className="text-sm font-bold text-slate-800">
            {teamDetail.name} <span className="text-xs font-normal text-slate-500">({teamDetail.user_name})</span>
          </h2>
        </div>
        <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
          Total: {teamDetail.total_points.toFixed(1)} pts
        </div>
      </div>

      {/* Players List Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
            <tr>
              <th className="py-2.5 px-3">Player</th>
              <th className="py-2.5 px-2">Role</th>
              <th className="py-2.5 px-2">Team</th>
              <th className="py-2.5 px-2 text-right">Cr</th>
              <th className="py-2.5 px-3 text-right">Points</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {teamDetail.players.map((p) => {
              const breakdown = breakdownMap.get(p.id);
              const pts = breakdown?.total_points ?? p.current_points ?? 0;
              const isSelected = selectedPlayerId === p.id;

              return (
                <React.Fragment key={p.id}>
                  <tr
                    onClick={() => setSelectedPlayerId(isSelected ? null : p.id)}
                    className={`hover:bg-slate-50/80 cursor-pointer transition-colors ${
                      isSelected ? 'bg-emerald-50/40' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 font-medium text-slate-900 flex items-center gap-1.5">
                      <ChevronRight
                        className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
                          isSelected ? 'rotate-90 text-emerald-600' : ''
                        }`}
                      />
                      <span>{p.name}</span>
                      {p.is_captain && (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          <Award className="w-2.5 h-2.5" />
                          2x C
                        </span>
                      )}
                      {p.is_vice_captain && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-300">
                          1.5x VC
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600">
                        {p.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-slate-500 font-medium truncate max-w-[80px]">
                      {p.team === 'Mumbai Titans' ? 'MT' : 'CS'}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono text-slate-500">
                      {p.credits.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900 font-mono">
                      {pts.toFixed(1)}
                    </td>
                  </tr>

                  {/* Expandable Traceable Event Breakdown */}
                  {isSelected && (
                    <tr className="bg-slate-50/70">
                      <td colSpan={5} className="py-2 px-4 border-t border-b border-slate-100">
                        <div className="text-[11px] text-slate-600 space-y-1">
                          <div className="font-semibold text-slate-800 flex items-center gap-1">
                            <Info className="w-3 h-3 text-emerald-600" />
                            <span>Scoring Breakdown for {p.name}:</span>
                          </div>
                          {breakdown && breakdown.events && breakdown.events.length > 0 ? (
                            <ul className="list-disc list-inside space-y-0.5 text-slate-600 pl-1 font-mono text-[10px]">
                              {breakdown.events.map((ev, i) => (
                                <li key={i}>{ev}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-slate-400 italic">Starting XI points allocated (4.0 pts).</p>
                          )}
                          <div className="pt-1 text-[10px] text-slate-400">
                            Multiplier applied: {p.is_captain ? '2.0x (Captain)' : p.is_vice_captain ? '1.5x (VC)' : '1.0x (Standard)'}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
