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
    <div className="min-h-screen bg-slate-50/60 flex flex-col font-sans text-slate-900">
      {/* Top Navigation */}
      <Header
        teams={teams}
        selectedTeamId={selectedTeamId}
        onSelectTeam={setSelectedTeamId}
        language={language}
        onToggleLanguage={setLanguage}
      />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* Error Notification */}
        {matchError && (
          <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800 flex items-center justify-between shadow-2xs">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-5 h-5 shrink-0 text-red-600" />
              <span className="font-medium">{matchError}</span>
            </div>
            <button
              type="button"
              onClick={() => void refreshState()}
              className="text-xs sm:text-sm font-bold px-3 py-1.5 bg-white hover:bg-red-100 rounded-lg border border-red-300 transition-colors flex items-center gap-1.5 shadow-2xs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-7 items-start">
          {/* Left Panel: Match State & Team */}
          <div className="space-y-5">
            <Scoreboard
              state={matchState}
              loading={matchLoading}
              teamName={teamDetail?.name ?? 'My Team'}
            />

            <ReplaySlider
              currentOver={currentOver}
              totalOvers={matchState?.total_overs ?? 20}
              onOverChange={setCurrentOver}
            />

            <TeamTable
              teamDetail={teamDetail}
              matchState={matchState}
              loading={matchLoading}
            />
          </div>

          {/* Right Panel: Chat Copilot */}
          <div className="sticky top-20">
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

      {/* Minimal Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-3 px-6 text-xs sm:text-sm text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="font-medium">Match Copilot &bull; Second-Screen Fantasy Live Assistant</span>
          <span className="text-slate-400">Sample data. Not official Dream11 scoring.</span>
        </div>
      </footer>
    </div>
  );
}
