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
      {/* Top Bar: Match Name & Freshness Badge */}
      <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
        <span className="font-semibold text-slate-800">{state.match_name}</span>
        <span className="text-[11px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/70">
          Updated after over {state.over}
        </span>
      </div>

      {/* Main Score & Team Points */}
      <div className="flex items-baseline justify-between pt-1 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {state.runs}/{state.wickets}
            </span>
            <span className="text-sm font-medium text-slate-500">
              ({state.over}.0 / {state.total_overs} ov)
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

      {/* Active Batters & Recent Balls */}
      <div className="pt-2.5 flex items-center justify-between text-xs">
        <div className="text-slate-500 text-[11px]">
          <span className="text-slate-400">Batting: </span>
          <span className="font-medium text-slate-700">
            {state.current_batters.length > 0 ? state.current_batters.join(' & ') : 'Not started'}
          </span>
        </div>

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
                  className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] shrink-0 font-mono ${style}`}
                >
                  {b.display_text}
                </span>
              );
            })
          ) : (
            <span className="text-slate-400 text-[10px]">No balls bowled yet</span>
          )}
        </div>
      </div>
    </div>
  );
};
