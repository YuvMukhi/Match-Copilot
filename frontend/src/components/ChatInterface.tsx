import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessageItem, Language } from '../types';
import { EvidencePanel } from './EvidencePanel';
import { Send, Bot, User, Trash2 } from 'lucide-react';

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
    <div className="space-y-1">
      {lines.map((line, lineIdx) => {
        if (!line.trim()) return <div key={lineIdx} className="h-0.5" />;

        const isBullet = line.trim().startsWith('-');
        const contentLine = isBullet ? line.trim().substring(1).trim() : line;

        const parts = contentLine.split(/(\*\*.*?\*\*)/g);
        const formattedParts = parts.map((part, partIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={partIdx} className="font-semibold text-slate-900">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        });

        if (isBullet) {
          return (
            <div key={lineIdx} className="flex items-start gap-1.5 pl-1 text-slate-700">
              <span className="text-emerald-600 font-bold leading-none mt-1">&bull;</span>
              <span>{formattedParts}</span>
            </div>
          );
        }

        return <p key={lineIdx}>{formattedParts}</p>;
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
      hi: 'Mere points kyun change hue?',
      query: language === 'hinglish' ? 'Mere points kyun change hue?' : 'Why did my points change?',
    },
    {
      en: 'Fix my captain',
      hi: 'Fix my captain',
      query: language === 'hinglish' ? 'Fix my captain' : 'Fix my captain',
    },
    {
      en: 'What if rain cuts it to 15 overs?',
      hi: 'Agar baarish se 15 overs ho gaye toh?',
      query: language === 'hinglish' ? 'Agar baarish se 15 overs ho gaye toh?' : 'What if rain cuts it to 15 overs?',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs flex flex-col h-[640px] sm:h-[680px] overflow-hidden">
      {/* Calm Chat Top Bar */}
      <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-semibold">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Match Copilot</span>
          <span className="text-[11px] text-slate-400">&bull; Live at Over {currentOver}</span>
        </div>

        <button
          type="button"
          onClick={onClearChat}
          title="Clear chat"
          className="text-[11px] text-slate-400 hover:text-slate-600 transition-colors flex items-center gap-1"
        >
          <Trash2 className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-2 max-w-[92%] sm:max-w-[85%] ${
                isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs ${
                  isUser ? 'bg-slate-800 text-white' : 'bg-emerald-600 text-white'
                }`}
              >
                {isUser ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
              </div>

              <div className="space-y-1">
                <div
                  className={`p-3 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-xs shadow-xs'
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
                  className={`text-[10px] text-slate-400 px-1 ${
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
          <div className="flex gap-2 max-w-[85%] mr-auto items-center">
            <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-3 h-3" />
            </div>
            <div className="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-xs text-xs text-slate-500 flex items-center gap-1.5 shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]"></span>
              <span className="text-[11px] text-slate-500 font-medium">Checking the numbers...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3 Quick Action Chips */}
      <div className="px-3.5 py-2 border-t border-slate-100 bg-slate-50/50">
        <div className="flex flex-wrap gap-1.5">
          {quickActionChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              disabled={loading}
              onClick={() => onSendMessage(chip.query)}
              className="text-[11px] font-medium bg-white hover:bg-emerald-50 hover:text-emerald-800 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200/80 shadow-xs transition-colors disabled:opacity-50"
            >
              {language === 'hinglish' ? chip.hi : chip.en}
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Form */}
      <form onSubmit={handleSubmit} className="p-2.5 bg-white border-t border-slate-200/80 flex items-center gap-2">
        <input
          id="chat-input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            language === 'hinglish'
              ? 'Poochhein kuch bhi (English ya Hinglish me)...'
              : 'Ask a question or tap a chip above...'
          }
          disabled={loading}
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:bg-white transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          aria-label="Send message"
          className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs sm:text-sm flex items-center gap-1 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs shrink-0"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
