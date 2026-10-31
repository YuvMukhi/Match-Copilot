import React, { useEffect, useState } from 'react';
import { Play, Pause, RotateCcw, FastForward, Clock } from 'lucide-react';

interface ReplaySliderProps {
  currentOver: number;
  totalOvers: number;
  onOverChange: (over: number) => void;
}

export const ReplaySlider: React.FC<ReplaySliderProps> = ({
  currentOver,
  totalOvers,
  onOverChange,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Auto-step forward when Play is active
  useEffect(() => {
    let interval: number | undefined;
    if (isPlaying) {
      interval = window.setInterval(() => {
        onOverChange(currentOver >= totalOvers ? 0 : currentOver + 1);
      }, 1800);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, currentOver, totalOvers, onOverChange]);

  const presets = [
    { label: 'Start (0)', over: 0 },
    { label: 'Wicket (3)', over: 3 },
    { label: 'Powerplay (6)', over: 6 },
    { label: 'Duck Penalty (11)', over: 11 },
    { label: 'Rain Break (15)', over: 15 },
    { label: 'Finish (20)', over: 20 },
  ];

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-xs">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Match Moment Replay Scrub
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
          <span>Moment: Over {currentOver} of {totalOvers}</span>
        </div>
      </div>

      {/* Scrub Range Slider */}
      <div className="py-2">
        <label htmlFor="replay-range" className="sr-only">
          Scrub match over
        </label>
        <input
          id="replay-range"
          type="range"
          min="0"
          max={totalOvers}
          step="1"
          value={currentOver}
          onChange={(e) => {
            setIsPlaying(false);
            onOverChange(Number(e.target.value));
          }}
          className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <div className="flex justify-between text-[11px] text-slate-400 font-mono mt-1">
          <span>Over 0 (Start)</span>
          <span>Over 5</span>
          <span>Over 10</span>
          <span>Over 15</span>
          <span>Over 20 (End)</span>
        </div>
      </div>

      {/* Control Buttons & Key Presets */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
        {/* Playback Controls */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setIsPlaying(!isPlaying)}
            aria-label={isPlaying ? 'Pause replay' : 'Play replay'}
            className="flex items-center gap-1 text-xs font-medium px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-colors"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Auto Play</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setIsPlaying(false);
              onOverChange(0);
            }}
            title="Reset to Over 0"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={() => {
              setIsPlaying(false);
              onOverChange(Math.min(totalOvers, currentOver + 1));
            }}
            title="Next Over (+1)"
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
          >
            <FastForward className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Narrative Match Moment Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto py-1">
          {presets.map((preset) => (
            <button
              key={preset.over}
              type="button"
              onClick={() => {
                setIsPlaying(false);
                onOverChange(preset.over);
              }}
              className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all ${
                currentOver === preset.over
                  ? 'bg-emerald-100 text-emerald-900 font-semibold border border-emerald-300'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-transparent'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
