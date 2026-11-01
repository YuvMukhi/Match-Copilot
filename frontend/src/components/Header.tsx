import React from 'react';
import type { Language, TeamSummary } from '../types';
import { Users, Sparkles } from 'lucide-react';

interface HeaderProps {
  teams: TeamSummary[];
  selectedTeamId: string;
  onSelectTeam: (teamId: string) => void;
  language: Language;
  onToggleLanguage: (lang: Language) => void;
}

export const Header: React.FC<HeaderProps> = ({
  teams,
  selectedTeamId,
  onSelectTeam,
  language,
  onToggleLanguage,
}) => {
  return (
    <header className="bg-white border-b border-slate-200/90 sticky top-0 z-20 px-4 sm:px-8 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Brand & Match Rivalry Pill */}
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white font-black flex items-center justify-center text-sm shadow-xs">
              MC
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-slate-900 tracking-tight text-lg">Match Copilot</span>
                <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200/80">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  Live Companion
                </span>
              </div>
            </div>
          </div>

          {/* Prominent Match Badge: MI VS CSK */}
          <div className="flex items-center gap-1.5 bg-slate-100/80 px-2.5 py-1 rounded-lg border border-slate-200/80">
            <span className="bg-blue-600 text-white font-black text-xs px-2 py-0.5 rounded shadow-xs tracking-wider">
              MI
            </span>
            <span className="text-slate-400 font-extrabold text-[11px] tracking-widest px-0.5">
              VS
            </span>
            <span className="bg-amber-400 text-slate-950 font-black text-xs px-2 py-0.5 rounded shadow-xs tracking-wider">
              CSK
            </span>
          </div>
        </div>

        {/* Controls: Team Selector + Language Switcher */}
        <div className="flex items-center gap-3">
          {/* Fantasy Team Selector */}
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-500 transition-all">
            <Users className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              id="team-select"
              value={selectedTeamId}
              onChange={(e) => onSelectTeam(e.target.value)}
              className="text-sm font-semibold bg-transparent text-slate-800 focus:outline-none cursor-pointer pr-1"
            >
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* Language Switcher */}
          <div className="inline-flex rounded-xl bg-slate-100 p-1 text-sm font-semibold border border-slate-200/60">
            <button
              type="button"
              onClick={() => onToggleLanguage('en')}
              className={`px-3 py-1 rounded-lg transition-all ${
                language === 'en'
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => onToggleLanguage('hinglish')}
              className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                language === 'hinglish'
                  ? 'bg-white text-slate-900 shadow-xs font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Sparkles className="w-3 h-3 text-amber-500" />
              <span>Hinglish</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
