import React from 'react';
import { Header } from './components/Header';
import { Scoreboard } from './components/Scoreboard';
import { ReplaySlider } from './components/ReplaySlider';
import { TeamTable } from './components/TeamTable';
import { ChatInterface } from './components/ChatInterface';
import { useMatchData } from './hooks/useMatchData';
import { useChat } from './hooks/useChat';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function App(): React.JSX.Element {
  const {
    teams,
    selectedMatchId,
    selectedTeamId,
    setSelectedTeamId,
    currentOver,
    setCurrentOver,
    matchState,
    teamDetail,
    loading: matchLoading,
    error: matchError,
    refreshState,
  } = useMatchData();

  const {
    language,
    setLanguage,
    messages,
    loading: chatLoading,
    error: chatError,
    sendMessage,
    clearMessages,
  } = useChat(selectedMatchId, selectedTeamId, currentOver);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      {/* Top Navigation & App Bar */}
      <Header
        teams={teams}
        selectedTeamId={selectedTeamId}
        onSelectTeam={setSelectedTeamId}
        language={language}
        onToggleLanguage={setLanguage}
      />

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {/* Error Notification if backend is unreachable */}
        {matchError && (
          <div className="mb-4 p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{matchError}</span>
            </div>
            <button
              type="button"
              onClick={() => void refreshState()}
              className="text-xs font-semibold px-2 py-1 bg-white hover:bg-red-100 rounded border border-red-300 transition-colors flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              Retry
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Panel: Scoreboard, Replay Slider, Fantasy Team (7 cols) */}
          <div className="lg:col-span-7 space-y-5">
            {/* Live Scoreboard */}
            <Scoreboard
              state={matchState}
              loading={matchLoading}
              teamName={teamDetail?.name ?? 'My Team'}
            />

            {/* Match Moment Replay Scrub Slider */}
            <ReplaySlider
              currentOver={currentOver}
              totalOvers={matchState?.total_overs ?? 20}
              onOverChange={setCurrentOver}
            />

            {/* My Fantasy Team Squad & Points Table */}
            <TeamTable
              teamDetail={teamDetail}
              matchState={matchState}
              loading={matchLoading}
            />
          </div>

          {/* Right Panel: Chat Copilot with Evidence Tables & Chips (5 cols) */}
          <div className="lg:col-span-5 sticky top-20">
            <ChatInterface
              messages={messages}
              loading={chatLoading}
              error={chatError}
              language={language}
              onSendMessage={sendMessage}
              onClearChat={clearMessages}
              currentOver={currentOver}
            />
          </div>
        </div>
      </main>

      {/* Footer with Mandatory Disclaimer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-3 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong>Match Copilot</strong> &bull; Explainable AI for Fantasy Sports
          </div>
          <div className="text-slate-400 font-medium">
            Sample data. Not official Dream11 scoring.
          </div>
        </div>
      </footer>
    </div>
  );
}
