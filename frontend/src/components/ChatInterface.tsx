import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessageItem, Language } from '../types';
import { EvidencePanel } from './EvidencePanel';
import { Send, Bot, User, Trash2, TrendingUp, Award, CloudRain } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessageItem[];
  loading: boolean;
  error: string | null;
  language: Language;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  currentOver: number;
}

// Clean text formatting for friend-like conversation
function renderFormattedContent(text: string): React.ReactNode {
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5">
      {lines.map((line, lineIdx) => {
        if (!line.trim()) return <div key={lineIdx} className="h-1" />;

        const isBullet = line.trim().startsWith('-');
        const contentLine = isBullet ? line.trim().substring(1).trim() : line;

        const parts = contentLine.split(/(\*\*.*?\*\*)/g);
        const formattedParts = parts.map((part, partIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={partIdx} className="font-extrabold text-slate-900">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        });

        if (isBullet) {
          return (
            <div key={lineIdx} className="flex items-start gap-2 pl-1 text-slate-800">
              <span className="text-emerald-600 font-black leading-none mt-1">&bull;</span>
              <span>{formattedParts}</span>
            </div>
          );
        }

        return <p key={lineIdx} className="text-slate-800 leading-relaxed">{formattedParts}</p>;
      })}
    </div>
  );
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  loading,
  error,
  language,
  onSendMessage,
  onClearChat,
  currentOver,
}) => {
  const [inputText, setInputText] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText);
    setInputText('');
  };

  // The 3 Core Quick-Action Chips
  const quickActionChips = [
    {
      en: 'Why did my points change?',
      hi: 'Mere points kyun badle?',
      query: language === 'hinglish' ? 'Mere points kyun change hue?' : 'Why did my points change?',
      icon: TrendingUp,
    },
    {
      en: 'Fix my captain',
      hi: 'Captain change karein?',
      query: language === 'hinglish' ? 'Fix my captain' : 'Fix my captain',
      icon: Award,
    },
    {
      en: 'What if rain cuts it to 15 overs?',
      hi: 'Baarish se 15 overs ho gaye toh?',
      query: language === 'hinglish' ? 'Agar baarish se 15 overs ho gaye toh?' : 'What if rain cuts it to 15 overs?',
      icon: CloudRain,
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm flex flex-col h-[670px] sm:h-[720px] overflow-hidden transition-all">
      {/* Calm Chat Top Bar */}
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-600 text-white flex items-center justify-center shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm sm:text-base font-extrabold text-slate-900">Match Copilot</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/70">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Over {currentOver}
              </span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClearChat}
          title="Clear chat"
          className="text-xs font-semibold text-slate-500 hover:text-slate-800 bg-white hover:bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/80 transition-colors flex items-center gap-1.5 shadow-2xs"
        >
          <Trash2 className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset</span>
        </button>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-[94%] sm:max-w-[88%] ${
                isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                  isUser ? 'bg-slate-900 text-white' : 'bg-gradient-to-tr from-emerald-600 to-teal-600 text-white'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="space-y-1">
                <div
                  className={`p-3.5 sm:p-4 rounded-2xl text-sm sm:text-[15px] leading-relaxed shadow-2xs ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs'
                      : 'bg-white text-slate-900 border border-slate-200/90 rounded-tl-xs'
                  }`}
                >
                  <div className="font-sans">
                    {isUser ? msg.content : renderFormattedContent(msg.content)}
                  </div>

                  {/* Evidence Table (Collapsed by default) */}
                  {!isUser && msg.evidence && (
                    <EvidencePanel evidence={msg.evidence} />
                  )}
                </div>

                <div
                  className={`text-xs text-slate-400 px-1 font-medium ${
                    isUser ? 'text-right' : 'text-left'
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex gap-3 max-w-[88%] mr-auto items-center">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-600 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-xs text-sm text-slate-600 flex items-center gap-2 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]"></span>
              <span className="text-xs sm:text-sm text-slate-600 font-semibold">Analyzing match numbers...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs sm:text-sm text-red-700 font-medium">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3 Quick Action Chips */}
      <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50/70">
        <div className="flex flex-wrap gap-2">
          {quickActionChips.map((chip, idx) => {
            const Icon = chip.icon;
            return (
              <button
                key={idx}
                type="button"
                disabled={loading}
                onClick={() => onSendMessage(chip.query)}
                className="text-xs sm:text-sm font-bold bg-white hover:bg-emerald-50 hover:text-emerald-900 hover:border-emerald-300 text-slate-800 px-3.5 py-1.5 sm:py-2 rounded-xl border border-slate-200/90 shadow-2xs transition-all active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
              >
                <Icon className="w-3.5 h-3.5 text-emerald-600" />
                <span>{language === 'hinglish' ? chip.hi : chip.en}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Message Input Form */}
      <form onSubmit={handleSubmit} className="p-3 sm:p-3.5 bg-white border-t border-slate-200/90 flex items-center gap-2.5">
        <input
          id="chat-input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            language === 'hinglish'
              ? 'Poochhein kuch bhi (jaise: Bumrah ke points, captain change)...'
              : 'Ask anything about your team, players, or match moment...'
          }
          disabled={loading}
          className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 sm:py-3 text-sm sm:text-base text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 focus:bg-white transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          aria-label="Send message"
          className="px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm sm:text-base flex items-center gap-1.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-xs shrink-0 active:scale-95"
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
