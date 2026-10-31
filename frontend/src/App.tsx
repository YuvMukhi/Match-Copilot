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
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5">
        {/* Error Notification */}
        {matchError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center justify-between">
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
          {/* Left Panel: Match State & Team */}
          <div className="space-y-4">
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
          <div className="sticky top-16">
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
      <footer className="mt-auto border-t border-slate-200/60 bg-white py-2 px-4 text-center text-[11px] text-slate-400">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span>Match Copilot &bull; Explainable Fantasy Cricket AI</span>
          <span>Sample data. Not official Dream11 scoring.</span>
        </div>
      </footer>
    </div>
  );
}
