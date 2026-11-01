import React, { useEffect, useState } from 'react';
import { Play, Pause, FastForward } from 'lucide-react';

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

  useEffect(() => {
    let interval: number | undefined;
    if (isPlaying) {
      interval = window.setInterval(() => {
        onOverChange(currentOver >= totalOvers ? 0 : currentOver + 1);
      }, 1500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, currentOver, totalOvers, onOverChange]);

  const quickJump = [
    { label: 'Start (0)', val: 0 },
    { label: 'Over 6 (PP)', val: 6 },
    { label: 'Over 11 (Duck)', val: 11 },
    { label: 'Over 15', val: 15 },
    { label: 'End (20)', val: 20 },
  ];

  return (
    <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-sm transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FastForward className="w-4 h-4 text-emerald-600" />
          <span className="font-bold text-slate-800 text-sm sm:text-base">Match Moment Replay</span>
        </div>
        <span className="font-mono font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-200/80 text-sm shadow-xs">
          Over {currentOver} of {totalOvers}
        </span>
      </div>

      {/* Slider Bar & Play/Pause */}
      <div className="flex items-center gap-3 sm:gap-4 my-2">
        <button
          type="button"
          onClick={() => setIsPlaying(!isPlaying)}
          title={isPlaying ? 'Pause replay' : 'Play timeline'}
          className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shrink-0 transition-all shadow-sm ${
            isPlaying
              ? 'bg-amber-500 hover:bg-amber-600 text-white'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white'
          }`}
        >
          {isPlaying ? (
            <Pause className="w-4 h-4 sm:w-5 sm:h-5 fill-current" />
          ) : (
            <Play className="w-4 h-4 sm:w-5 sm:h-5 fill-current ml-0.5" />
          )}
        </button>

        <div className="flex-1 flex flex-col justify-center">
          <input
            id="replay-slider"
            type="range"
            min="0"
            max={totalOvers}
            step="1"
            value={currentOver}
            onChange={(e) => {
              setIsPlaying(false);
              onOverChange(Number(e.target.value));
            }}
            className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600 focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* Quick Jump Moments */}
      <div className="flex flex-wrap items-center justify-between gap-1.5 mt-3 pt-2 border-t border-slate-100">
        {quickJump.map((item) => (
          <button
            key={item.val}
            type="button"
            onClick={() => {
              setIsPlaying(false);
              onOverChange(item.val);
            }}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg transition-all ${
              currentOver === item.val
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
