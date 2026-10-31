import React from 'react';
import type { Language, TeamSummary } from '../types';

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
    <header className="bg-white border-b border-slate-200/80 sticky top-0 z-20 px-4 sm:px-6 py-2.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Clean Logo & Title */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
            MC
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 tracking-tight text-base">Match Copilot</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Assistant
            </span>
          </div>
        </div>

        {/* Minimal Controls: Team Selector + Language Toggle */}
        <div className="flex items-center gap-2.5">
          <select
            id="team-select"
            value={selectedTeamId}
            onChange={(e) => onSelectTeam(e.target.value)}
            className="text-xs font-medium bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
          >
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          {/* Simple Language Switcher */}
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 text-xs font-medium">
            <button
              type="button"
              onClick={() => onToggleLanguage('en')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                language === 'en'
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => onToggleLanguage('hinglish')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                language === 'hinglish'
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Hinglish
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
