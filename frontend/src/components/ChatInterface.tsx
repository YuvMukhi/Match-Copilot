import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessageItem, Language } from '../types';
import { EvidencePanel } from './EvidencePanel';
import { Send, Sparkles, AlertCircle, Bot, User, Trash2 } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessageItem[];
  loading: boolean;
  error: string | null;
  language: Language;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  currentOver: number;
}

// Lightweight, safe markdown formatter for chat bubbles
function renderFormattedContent(text: string): React.ReactNode {
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5">
      {lines.map((line, lineIdx) => {
        if (!line.trim()) {
          return <div key={lineIdx} className="h-1" />;
        }

        // Bullet point
        const isBullet = line.trim().startsWith('-');
        const contentLine = isBullet ? line.trim().substring(1).trim() : line;

        // Parse **bold** parts
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
            <div key={lineIdx} className="flex items-start gap-1.5 pl-1">
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText);
    setInputText('');
  };

  const quickActionChips = [
    {
      en: 'Why did my points change?',
      hi: 'Mere points kyun change hue?',
      query: language === 'hinglish' ? 'Mere points kyun change hue?' : 'Why did my points change?',
    },
    {
      en: 'Fix my captain',
      hi: 'Mera captain change karna chahiye?',
      query: language === 'hinglish' ? 'Mera captain fix karein' : 'Fix my captain',
    },
    {
      en: 'What if rain cuts it to 15 overs?',
      hi: 'Agar baarish se 15 overs ho gaye toh?',
      query: language === 'hinglish' ? 'Agar baarish se 15 overs ho gaye toh?' : 'What if rain cuts it to 15 overs?',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-[750px] overflow-hidden">
      {/* Chat Header */}
      <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <span>Match Copilot</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800">
                Online
              </span>
            </h2>
            <p className="text-[11px] text-slate-500">
              Live at Over {currentOver} &bull; Language: {language === 'hinglish' ? 'Hinglish' : 'English'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClearChat}
          title="Reset conversation"
          className="text-xs text-slate-400 hover:text-slate-600 p-1.5 rounded-md hover:bg-slate-100 transition-colors flex items-center gap-1"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Clear</span>
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-2.5 max-w-[92%] sm:max-w-[85%] ${
                isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs shadow-xs ${
                  isUser ? 'bg-slate-800 text-white' : 'bg-emerald-600 text-white'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              {/* Message Bubble */}
              <div className="space-y-1">
                <div
                  className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs shadow-xs'
                      : 'bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs shadow-xs'
                  }`}
                >
                  <div className="font-sans">
                    {isUser ? msg.content : renderFormattedContent(msg.content)}
                  </div>

                  {/* Evidence Table Panel (Explainable AI centerpiece) */}
                  {!isUser && msg.evidence && (
                    <EvidencePanel evidence={msg.evidence} />
                  )}
                </div>

                {/* Timestamp & Over pill */}
                <div
                  className={`flex items-center gap-1.5 text-[10px] text-slate-400 px-1 ${
                    isUser ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <span>{msg.timestamp}</span>
                  <span>&bull;</span>
                  <span>Over {msg.over}</span>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-2.5 max-w-[85%] mr-auto items-center">
            <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-xs shadow-xs flex items-center gap-2 text-xs text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]"></span>
              <span className="font-medium text-slate-600">Querying deterministic engine...</span>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Chips */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/70">
        <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 mb-1.5">
          <Sparkles className="w-3 h-3 text-amber-500" />
          <span>Quick actions:</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {quickActionChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              disabled={loading}
              onClick={() => onSendMessage(chip.query)}
              className="text-[11px] font-medium bg-white hover:bg-emerald-50 hover:text-emerald-800 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition-colors disabled:opacity-50"
            >
              {language === 'hinglish' ? chip.hi : chip.en}
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Form */}
      <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <label htmlFor="chat-input" className="sr-only">
          Ask Match Copilot
        </label>
        <input
          id="chat-input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            language === 'hinglish'
              ? 'Poochhein kuch bhi apne points ya captain ke baare mein...'
              : 'Ask why your points changed, fix your captain, or what-if rain...'
          }
          disabled={loading}
          className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          aria-label="Send message"
          className="p-2 sm:px-4 sm:py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs shrink-0"
        >
          <span className="hidden sm:inline">Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
