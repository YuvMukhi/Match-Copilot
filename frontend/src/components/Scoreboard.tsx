import React from 'react';
import type { MatchState } from '../types';
import { Activity, Trophy, CircleDot } from 'lucide-react';

interface ScoreboardProps {
  state: MatchState | null;
  loading: boolean;
  teamName: string;
}

export const Scoreboard: React.FC<ScoreboardProps> = ({ state, loading, teamName }) => {
  if (loading && !state) {
    return (
      <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs animate-pulse">
        <div className="h-4 bg-slate-200 rounded w-1/3 mb-4"></div>
        <div className="h-8 bg-slate-200 rounded w-1/2 mb-2"></div>
        <div className="h-3 bg-slate-200 rounded w-1/4"></div>
      </div>
    );
  }

  if (!state) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl p-4 sm:p-5 border border-slate-200 shadow-xs transition-all">
      {/* Top Bar: Match Title & Status */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800 text-sm">{state.match_name}</span>
          <span className="text-slate-400 text-xs">&bull; Innings 1</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
            LIVE OVER {state.over}/{state.total_overs}
          </span>
        </div>
      </div>

      {/* Main Score & Fantasy Overlay Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
        {/* Left: Cricket Match Score */}
        <div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
              {state.runs}/{state.wickets}
            </span>
            <span className="text-sm font-medium text-slate-500">
              ({state.over}.0 / {state.total_overs} ov)
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium text-slate-600 mt-1">
            <span>CRR: <strong className="text-slate-900">{state.run_rate.toFixed(2)}</strong> RPO</span>
            <span>&bull;</span>
            <span className="text-slate-500">Venue: Wankhede Stadium</span>
          </div>
        </div>

        {/* Right: Fantasy Team Points Pill */}
        <div className="sm:border-l sm:border-slate-100 sm:pl-4 flex flex-col justify-center">
          <div className="flex items-center justify-between sm:justify-start gap-2">
            <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 uppercase tracking-wider">
              <Trophy className="w-3.5 h-3.5 text-amber-500" />
              {teamName} Points
            </span>
          </div>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-600">
              {state.team_points !== undefined && state.team_points !== null ? state.team_points.toFixed(1) : '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-medium">pts (at Over {state.over})</span>
          </div>
        </div>
      </div>

      {/* Active Batters & Bowler */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs gap-3">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Batting:</span>
          {state.current_batters.length > 0 ? (
            <span className="font-semibold text-slate-800">{state.current_batters.join(' & ')}</span>
          ) : (
            <span className="text-slate-500">Match not started</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Bowler:</span>
          <span className="font-semibold text-slate-800">{state.current_bowler}</span>
        </div>
      </div>

      {/* Recent Deliveries Strip */}
      <div className="mt-3 flex items-center gap-2 pt-2 border-t border-slate-50">
        <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1 shrink-0">
          <Activity className="w-3 h-3 text-slate-400" />
          Recent:
        </span>
        <div className="flex items-center gap-1.5 overflow-x-auto py-1">
          {state.recent_balls.length > 0 ? (
            state.recent_balls.map((b, idx) => {
              let badgeColor = 'bg-slate-100 text-slate-700 border-slate-200';
              if (b.is_wicket) {
                badgeColor = 'bg-red-100 text-red-800 border-red-300 font-bold';
              } else if (b.runs_batter === 6) {
                badgeColor = 'bg-emerald-600 text-white border-emerald-700 font-bold';
              } else if (b.runs_batter === 4) {
                badgeColor = 'bg-emerald-100 text-emerald-800 border-emerald-300 font-bold';
              } else if (b.extra_type) {
                badgeColor = 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
              } else if (b.runs_batter === 0) {
                badgeColor = 'bg-slate-100 text-slate-400 border-slate-200';
              }

              return (
                <span
                  key={idx}
                  title={`${b.bowler_name} to ${b.batter_name} (Over ${b.over_number}.${b.ball_in_over})`}
                  className={`px-2 py-0.5 rounded-md text-[11px] border shrink-0 font-mono tracking-tight transition-transform hover:scale-105 cursor-default ${badgeColor}`}
                >
                  {b.display_text}
                </span>
              );
            })
          ) : (
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <CircleDot className="w-3 h-3 text-slate-300" />
              Scrub slider to see deliveries
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
