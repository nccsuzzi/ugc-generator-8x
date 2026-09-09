'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  showSuggestions?: boolean;
}

const SUGGESTIONS = [
  "I'm building CalAI, a calorie-tracking app. Here's the site: calai.app",
  "What can you do?",
  "Create a UGC video for https://notion.so",
];

export default function ChatInput({
  onSendMessage,
  isLoading,
  showSuggestions = false,
}: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full">
      {/* Quick Starter Suggestions */}
      {showSuggestions && (
        <div className="mb-3 flex flex-wrap gap-2 justify-center">
          {SUGGESTIONS.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => onSendMessage(suggestion)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium bg-[#fafaf8] hover:bg-white border border-[#e1e4ea] hover:border-[#0021cc]/40 text-[#525866] hover:text-[#0e121b] transition shadow-sm"
            >
              <Sparkles className="w-3 h-3 text-[#0021cc]" />
              <span className="truncate max-w-[280px] sm:max-w-[360px]">{suggestion}</span>
            </button>
          ))}
        </div>
      )}

      {/* Pill-Shaped Input Bar */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-[#e1e4ea] shadow-[0_4px_24px_rgba(0,0,0,0.06)] ring-1 ring-black/[0.03] focus-within:border-[#0021cc] focus-within:ring-2 focus-within:ring-[#0021cc]/15 transition duration-200"
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="I'm building CalAI, a calorie-tracking app. Here's the site: calai.app"
          rows={1}
          disabled={isLoading}
          className="w-full px-1.5 py-1.5 bg-transparent resize-none text-sm text-[#0e121b] placeholder-[#7c7c7c] focus:outline-none max-h-[120px] leading-relaxed font-normal"
        />

        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className={`w-9 h-9 rounded-full shrink-0 transition-all duration-200 flex items-center justify-center ${
            text.trim() && !isLoading
              ? 'bg-[#0021cc] hover:bg-[#001baa] text-white shadow-md shadow-[#0021cc]/25 hover:scale-105 active:scale-95'
              : 'bg-[#fafaf8] text-[#525866]/40 border border-[#e1e4ea] cursor-not-allowed'
          }`}
          title="Send message"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </form>

      <div className="mt-2 text-center text-[11px] text-[#7c7c7c] font-normal">
        Licensed Pexels stock • Trending Giphy reactions • Epidemic Sound audio
      </div>
    </div>
  );
}
