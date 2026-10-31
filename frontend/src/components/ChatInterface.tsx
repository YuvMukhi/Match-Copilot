import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessageItem, Language } from '../types';
import { EvidencePanel } from './EvidencePanel';
import { Send, Sparkles, Bot, User, Trash2 } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessageItem[];
  loading: boolean;
  error: string | null;
  language: Language;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  currentOver: number;
}

// Clean text and markdown rendering
function renderFormattedContent(text: string): React.ReactNode {
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5">
      {lines.map((line, lineIdx) => {
        if (!line.trim()) {
          return <div key={lineIdx} className="h-1" />;
        }

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText);
    setInputText('');
  };

  // Conversational prompt ideas that users can click OR type their own
  const samplePrompts = [
    {
      en: 'How is my team doing?',
      hi: 'Meri team kaisa kar rahi hai?',
    },
    {
      en: 'Why did my points change?',
      hi: 'Mere points kyun change hue?',
    },
    {
      en: 'Should I change my captain?',
      hi: 'Kya mujhe captain change karna chahiye?',
    },
    {
      en: 'How is Rohit Sharma performing?',
      hi: 'Rohit Sharma ke points kitne hain?',
    },
    {
      en: 'What if rain cuts it to 15 overs?',
      hi: 'Agar baarish se 15 overs ho gaye toh?',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs flex flex-col h-[650px] sm:h-[700px] overflow-hidden">
      {/* Top Bar */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-xs shadow-xs font-semibold">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-800">Match Copilot Chat</div>
            <div className="text-[11px] text-slate-400">
              Ask anything about your team &bull; Over {currentOver}
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClearChat}
          title="Clear conversation"
          className="text-xs text-slate-400 hover:text-slate-600 p-1.5 rounded-md hover:bg-slate-100 transition-colors flex items-center gap-1"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-[11px]">Clear</span>
        </button>
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-2.5 max-w-[90%] sm:max-w-[85%] ${
                isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-xs ${
                  isUser ? 'bg-slate-800 text-white' : 'bg-emerald-600 text-white'
                }`}
              >
                {isUser ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
              </div>

              {/* Message Bubble */}
              <div className="space-y-1">
                <div
                  className={`p-3 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs shadow-xs'
                      : 'bg-white text-slate-800 border border-slate-200/90 rounded-tl-xs shadow-xs'
                  }`}
                >
                  <div className="font-sans">
                    {isUser ? msg.content : renderFormattedContent(msg.content)}
                  </div>

                  {/* Expandable Evidence Table */}
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

        {/* Loading Spinner */}
        {loading && (
          <div className="flex gap-2.5 max-w-[85%] mr-auto items-center">
            <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <Bot className="w-3 h-3" />
            </div>
            <div className="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-xs shadow-xs flex items-center gap-2 text-xs text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]"></span>
              <span className="text-slate-600 text-[11px]">Thinking...</span>
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

      {/* Suggested Quick Prompt Pills */}
      <div className="px-3.5 py-2 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
          <Sparkles className="w-3 h-3 text-amber-500" />
          <span>Suggestions (or type anything below):</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {samplePrompts.map((p, idx) => {
            const queryText = language === 'hinglish' ? p.hi : p.en;
            return (
              <button
                key={idx}
                type="button"
                disabled={loading}
                onClick={() => onSendMessage(queryText)}
                className="text-[11px] font-medium bg-white hover:bg-emerald-50 hover:text-emerald-800 text-slate-600 px-2.5 py-1 rounded-full border border-slate-200 shadow-xs transition-colors disabled:opacity-50"
              >
                {queryText}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Freeform Chat Input Form */}
      <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <label htmlFor="chat-input" className="sr-only">
          Type your question
        </label>
        <input
          id="chat-input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            language === 'hinglish'
              ? 'Poochhein kuch bhi apne players, points, ya strategy ke baare mein...'
              : 'Ask anything about your team, players, captaincy, or strategy...'
          }
          disabled={loading}
          className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:bg-white transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || loading}
          aria-label="Send message"
          className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs shrink-0"
        >
          <span>Send</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
