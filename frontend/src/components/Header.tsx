import React from 'react';
import type { Language, TeamSummary } from '../types';
import { ShieldCheck, Languages, Radio } from 'lucide-react';

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
    <header className="bg-white border-b border-slate-200 sticky top-0 z-20 px-4 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Logo and Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-sm font-bold text-lg tracking-wider">
            MC
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Match Copilot</h1>
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                <Radio className="w-3 h-3 text-emerald-600 animate-pulse" />
                Live Engine
              </span>
            </div>
            <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
              <span>Explainable AI Assistant for Fantasy Cricket</span>
              <span>&bull;</span>
              <span className="text-slate-400 font-medium">Sample data. Not official Dream11 scoring.</span>
            </p>
          </div>
        </div>

        {/* Controls: Team Selector + Language Toggle */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          {/* Team Switcher */}
          <div className="flex items-center gap-2">
            <label htmlFor="team-select" className="text-xs font-medium text-slate-600 hidden md:inline">
              My Team:
            </label>
            <select
              id="team-select"
              value={selectedTeamId}
              onChange={(e) => onSelectTeam(e.target.value)}
              className="text-xs font-medium bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors"
            >
              {teams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.user_name})
                </option>
              ))}
            </select>
          </div>

          {/* Language Toggle */}
          <div className="inline-flex items-center p-0.5 rounded-lg bg-slate-100 border border-slate-200 text-xs font-medium">
            <button
              type="button"
              onClick={() => onToggleLanguage('en')}
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
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
              className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
                language === 'hinglish'
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Languages className="w-3 h-3 text-emerald-600" />
              Hinglish
            </button>
          </div>

          {/* Explainability badge */}
          <div className="hidden lg:flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50/70 border border-emerald-200/60 rounded-md px-2 py-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Deterministic Math</span>
          </div>
        </div>
      </div>
    </header>
  );
};
