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
      <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-xs animate-pulse">
        <div className="h-5 bg-slate-200 rounded w-1/3 mb-4"></div>
        <div className="h-9 bg-slate-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!state) return null;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm transition-all">
      {/* Top Bar: Match Name & Freshness Badge */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          {/* Vibrant MI vs CSK Match Title */}
          <div className="flex items-center gap-1.5">
            <span className="bg-blue-600 text-white font-black text-xs sm:text-sm px-2.5 py-0.5 rounded-md shadow-xs tracking-wider">
              MI
            </span>
            <span className="text-slate-400 font-extrabold text-xs sm:text-sm tracking-widest px-0.5">
              VS
            </span>
            <span className="bg-amber-400 text-slate-950 font-black text-xs sm:text-sm px-2.5 py-0.5 rounded-md shadow-xs tracking-wider">
              CSK
            </span>
          </div>
          <span className="text-xs sm:text-sm font-semibold text-slate-500 hidden sm:inline">
            &bull; Wankhede Stadium
          </span>
        </div>

        {/* Freshness Badge */}
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200/80 shadow-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Updated after over {state.over}</span>
        </span>
      </div>

      {/* Main Score & Team Points */}
      <div className="flex items-baseline justify-between pt-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-baseline gap-2.5">
            <span className="text-4xl sm:text-5xl font-black text-slate-900 tracking-tight font-mono">
              {state.runs}/{state.wickets}
            </span>
            <span className="text-base sm:text-lg font-bold text-slate-500">
              ({state.over}.0 / {state.total_overs} ov)
            </span>
          </div>
          <div className="text-xs sm:text-sm text-slate-500 mt-1 font-medium">
            Current Run Rate: <strong className="text-slate-800 font-bold">{state.run_rate.toFixed(2)}</strong> RPO
          </div>
        </div>

        <div className="text-right">
          <div className="text-xs sm:text-sm font-semibold text-slate-500 mb-0.5">{teamName}</div>
          <div className="text-3xl sm:text-4xl font-black text-emerald-600 font-mono tracking-tight">
            {state.team_points !== undefined && state.team_points !== null
              ? state.team_points.toFixed(1)
              : '0.0'}
            <span className="text-sm font-bold text-slate-400 ml-1">pts</span>
          </div>
        </div>
      </div>

      {/* Active Batters & Recent Balls */}
      <div className="pt-3 flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="text-slate-600 flex items-center gap-1.5 font-medium">
          <span className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Batting:</span>
          <span className="font-bold text-slate-800">
            {state.current_batters.length > 0 ? state.current_batters.join(' & ') : 'Not started'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto py-1">
          {state.recent_balls.length > 0 ? (
            state.recent_balls.map((b, idx) => {
              let style = 'bg-slate-100 text-slate-700 border border-slate-200';
              if (b.is_wicket) {
                style = 'bg-red-600 text-white font-black shadow-xs border border-red-700';
              } else if (b.runs_batter === 6) {
                style = 'bg-emerald-600 text-white font-black shadow-xs border border-emerald-700';
              } else if (b.runs_batter === 4) {
                style = 'bg-emerald-100 text-emerald-900 font-black border border-emerald-300';
              } else if (b.extra_type) {
                style = 'bg-amber-100 text-amber-900 font-bold border border-amber-300';
              }

              return (
                <span
                  key={idx}
                  title={`${b.bowler_name} to ${b.batter_name}`}
                  className={`w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center rounded-full text-xs font-mono shrink-0 transition-transform hover:scale-105 ${style}`}
                >
                  {b.display_text}
                </span>
              );
            })
          ) : (
            <span className="text-slate-400 text-xs italic">No deliveries bowled yet</span>
          )}
        </div>
      </div>
    </div>
  );
};
