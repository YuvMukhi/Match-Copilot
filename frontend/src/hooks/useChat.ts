import { useState } from 'react';
import { api } from '../services/api';
import type { ChatMessageItem, Language } from '../types';

export function useChat(matchId: string, teamId: string, currentOver: number) {
  const [language, setLanguage] = useState<Language>('en');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const initialWelcome: ChatMessageItem = {
    id: 'welcome_1',
    role: 'assistant',
    content:
      language === 'hinglish'
        ? "Namaste! Main hoon aapka **Match Copilot** 🏏. Puchhein kuch bhi apne fantasy team ke baare mein — points kyun badle, captain switch karein ya nahi, ya rain cut ka kya asar hoga!"
        : "Welcome to **Match Copilot** 🏏. I'm your explainable live fantasy cricket AI companion. Ask me why your points moved, whether you should fix your captain, or what happens if rain reduces the match!",
    over: currentOver,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };

  const [messages, setMessages] = useState<ChatMessageItem[]>([initialWelcome]);

  const sendMessage = async (userText: string) => {
    if (!userText.trim() || loading) return;

    const userMessage: ChatMessageItem = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: userText.trim(),
      over: currentOver,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await api.sendChat({
        match_id: matchId,
        team_id: teamId,
        over: currentOver,
        message: userText.trim(),
        language: language,
      });

      const assistantMessage: ChatMessageItem = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        evidence: response.evidence,
        over: response.over,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isOutOfScope: response.is_out_of_scope,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Network error communicating with Copilot';
      setError(errorMsg);
      // Append fallback error assistant message
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Sorry, couldn't get a response: ${errorMsg}. Please try asking again.`,
          over: currentOver,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setMessages([
      {
        id: `welcome_${Date.now()}`,
        role: 'assistant',
        content:
          language === 'hinglish'
            ? "Chat clear ho gaya. Batayein ab main aapki kya madad karoon?"
            : "Chat reset. How can I help analyze your fantasy team right now?",
        over: currentOver,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return {
    language,
    setLanguage,
    messages,
    loading,
    error,
    sendMessage,
    clearMessages,
  };
}
