import React, { useEffect, useState } from 'react';
import { Play, Pause } from 'lucide-react';

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

  const quickJump = [0, 6, 11, 15, 20];

  return (
    <div className="bg-white rounded-xl p-3.5 border border-slate-200/80 shadow-xs">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="font-semibold text-slate-700">Replay Match Moment</span>
        <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
          Over {currentOver}
        </span>
      </div>

      {/* Slider Bar */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setIsPlaying(!isPlaying)}
          title={isPlaying ? 'Pause' : 'Play timeline'}
          className="w-7 h-7 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center shrink-0 transition-colors shadow-xs"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-white ml-0.5" />}
        </button>

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
          className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600 focus:outline-none"
        />
      </div>

      {/* Quick Jump Buttons */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
        {quickJump.map((ov) => (
          <button
            key={ov}
            type="button"
            onClick={() => {
              setIsPlaying(false);
              onOverChange(ov);
            }}
            className={`font-mono transition-colors hover:text-slate-800 ${
              currentOver === ov ? 'text-emerald-700 font-bold underline' : ''
            }`}
          >
            {ov === 0 ? 'Start' : ov === 20 ? 'End' : `Over ${ov}`}
          </button>
        ))}
      </div>
    </div>
  );
};
