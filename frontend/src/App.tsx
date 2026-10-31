import React from 'react';

export default function App(): React.JSX.Element {
  return (
    <main className="min-h-screen bg-slate-50 p-6">
      <header className="max-w-7xl mx-auto flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Match Copilot</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
              Live AI
            </span>
          </h1>
          <p className="text-sm text-slate-500">
            Explainable fantasy cricket companion &bull; Sample data. Not official Dream11 scoring.
          </p>
        </div>
      </header>
    </main>
  );
}
