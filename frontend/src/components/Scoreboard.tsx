import React from 'react';
import type { MatchState } from '../types';

interface ScoreboardProps {
  state: MatchState | null;
  loading: boolean;
  teamName: string;
}

export const Scoreboard: React.FC<ScoreboardProps> = ({ state, loading, teamName }) => {
  if (loading && !state) {
    return (
      <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/3 mb-3"></div>
        <div className="h-7 bg-slate-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!state) return null;

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs">
      {/* Top row: Match and Over */}
      <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
        <span className="font-semibold text-slate-700">{state.match_name}</span>
        <span className="font-medium bg-slate-100 px-2 py-0.5 rounded text-slate-600">
          Over {state.over} of {state.total_overs}
        </span>
      </div>

      {/* Main Stats: Cricket Score & Fantasy Team Points */}
      <div className="flex items-baseline justify-between pt-1 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {state.runs}/{state.wickets}
            </span>
            <span className="text-sm font-medium text-slate-500">
              ({state.over}.0 ov)
            </span>
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            CRR: <strong className="text-slate-800">{state.run_rate.toFixed(2)}</strong> RPO
          </div>
        </div>

        <div className="text-right">
          <div className="text-xs font-medium text-slate-500">{teamName}</div>
          <div className="text-2xl font-extrabold text-emerald-600">
            {state.team_points !== undefined && state.team_points !== null
              ? state.team_points.toFixed(1)
              : '0.0'}{' '}
            <span className="text-xs font-semibold text-slate-400">pts</span>
          </div>
        </div>
      </div>

      {/* Recent Deliveries Strip */}
      <div className="pt-2.5 flex items-center justify-between text-xs">
        <div className="text-slate-400 text-[11px] font-medium">Recent balls:</div>
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {state.recent_balls.length > 0 ? (
            state.recent_balls.map((b, idx) => {
              let style = 'bg-slate-100 text-slate-600';
              if (b.is_wicket) {
                style = 'bg-red-500 text-white font-bold';
              } else if (b.runs_batter === 6) {
                style = 'bg-emerald-600 text-white font-bold';
              } else if (b.runs_batter === 4) {
                style = 'bg-emerald-100 text-emerald-800 font-bold';
              } else if (b.extra_type) {
                style = 'bg-amber-100 text-amber-800 font-semibold';
              }

              return (
                <span
                  key={idx}
                  title={`${b.bowler_name} to ${b.batter_name}`}
                  className={`w-6 h-6 flex items-center justify-center rounded-full text-[11px] shrink-0 font-mono ${style}`}
                >
                  {b.display_text}
                </span>
              );
            })
          ) : (
            <span className="text-slate-400 text-[11px]">No balls bowled yet</span>
          )}
        </div>
      </div>
    </div>
  );
};
