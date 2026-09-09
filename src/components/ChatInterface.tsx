'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from '../types/chat';
import { sendMessage, getVideoStatus, getConversation } from '../lib/api';
import MessageItem from './MessageItem';
import ChatInput from './ChatInput';
import { Sparkles, Plus, Loader2 } from 'lucide-react';

const STORAGE_KEY = 'ugc_generator_conversation_id';

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [isRehydrating, setIsRehydrating] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingIntervalsRef = useRef<{ [videoId: string]: NodeJS.Timeout }>({});

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  };

  useEffect(() => {
    if (!isRehydrating) {
      scrollToBottom();
    }
  }, [messages, isRehydrating]);

  // Clean up any polling timers on unmount and handle benign DOM/media AbortErrors
  useEffect(() => {
    const handleRejection = (e: PromiseRejectionEvent) => {
      if (e.reason?.name === 'AbortError' || e.reason?.message?.includes('aborted')) {
        e.preventDefault();
      }
    };
    window.addEventListener('unhandledrejection', handleRejection);
    return () => {
      Object.values(pollingIntervalsRef.current).forEach(clearInterval);
      window.removeEventListener('unhandledrejection', handleRejection);
    };
  }, []);

  const startPollingVideoStatus = (videoId: string, messageId: string) => {
    if (pollingIntervalsRef.current[videoId]) {
      clearInterval(pollingIntervalsRef.current[videoId]);
    }

    const poll = async () => {
      try {
        const metadata = await getVideoStatus(videoId);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId ? { ...msg, videoMetadata: metadata } : msg
          )
        );

        if (
          metadata.status === 'completed' ||
          metadata.status === 'failed' ||
          metadata.status === 'expired'
        ) {
          if (pollingIntervalsRef.current[videoId]) {
            clearInterval(pollingIntervalsRef.current[videoId]);
            delete pollingIntervalsRef.current[videoId];
          }
        }
      } catch (err) {
        console.error(`Failed to poll video ${videoId}:`, err);
      }
    };

    // Immediate poll followed by 1.5s interval
    poll();
    pollingIntervalsRef.current[videoId] = setInterval(poll, 1500);
  };

  // Rehydrate previous session from localStorage on page reload
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const savedConvId =
          typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
        if (!savedConvId) {
          setIsRehydrating(false);
          return;
        }

        const data = await getConversation(savedConvId);
        if (data && data.messages && data.messages.length > 0) {
          setConversationId(data.conversation_id);

          const restoredMessages: ChatMessage[] = data.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            videoId: m.video_id,
            videoMetadata: m.video_metadata,
            createdAt: new Date(m.created_at),
          }));

          setMessages(restoredMessages);

          // If there is an active/in-progress video, reconnect polling seamlessly
          const activeMsg = [...restoredMessages]
            .reverse()
            .find(
              (m) =>
                m.role === 'assistant' &&
                m.videoId &&
                m.videoMetadata &&
                ['pending', 'extracting', 'planning', 'rendering'].includes(
                  m.videoMetadata.status
                )
            );

          if (activeMsg && activeMsg.videoId) {
            startPollingVideoStatus(activeMsg.videoId, activeMsg.id);
          }
        }
      } catch (err) {
        console.warn('Could not restore previous conversation session:', err);
        if (typeof window !== 'undefined') {
          localStorage.removeItem(STORAGE_KEY);
        }
      } finally {
        setIsRehydrating(false);
      }
    };

    restoreSession();
  }, []);

  const handleSendMessage = async (text: string) => {
    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const resp = await sendMessage(text, conversationId);
      if (resp.conversation_id) {
        setConversationId(resp.conversation_id);
        if (typeof window !== 'undefined') {
          localStorage.setItem(STORAGE_KEY, resp.conversation_id);
        }
      }

      const assistantMsgId = `assistant-${Date.now()}`;
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: resp.message,
        videoId: resp.video_id,
        videoMetadata: resp.video_id ? { id: resp.video_id, status: 'pending' } : undefined,
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (resp.video_id && resp.generation_started) {
        startPollingVideoStatus(resp.video_id, assistantMsgId);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `assistant-err-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I ran into an error processing your message: ${err.message || 'Unknown error'}`,
        createdAt: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewAd = () => {
    Object.values(pollingIntervalsRef.current).forEach(clearInterval);
    pollingIntervalsRef.current = {};
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
    setConversationId(undefined);
    setMessages([]);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 max-w-3xl mx-auto px-4 sm:px-6 w-full overflow-hidden">
      {/* Scrollable Message Thread Area */}
      <div className="flex-1 min-h-0 overflow-y-auto py-4 space-y-4 pr-1">
        {isRehydrating ? (
          <div className="h-full flex flex-col items-center justify-center text-center my-auto">
            <Loader2 className="w-6 h-6 animate-spin text-[#0021cc] mb-2" />
            <div className="text-xs text-[#525866]">Restoring studio session...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 my-auto animate-entrance">
            <div className="w-12 h-12 rounded-2xl bg-[#0021cc]/10 border border-[#0021cc]/15 flex items-center justify-center text-[#0021cc] mb-6 shadow-sm">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-display font-bold text-[#0e121b] mb-3 tracking-tight">
              Turn any product into a UGC ad
            </h2>
            <p className="text-sm sm:text-base text-[#525866] max-w-md mb-8 leading-relaxed font-normal">
              Paste a website URL or describe your product. The AI organizes licensed stock footage, viral reaction GIFs, and Epidemic Sound tracks into a polished 9:16 social ad.
            </p>
          </div>
        ) : (
          <>
            {/* Top Project Session Bar with New Ad button */}
            <div className="flex items-center justify-between pb-2 border-b border-[#e1e4ea]/60">
              <div className="text-[11px] font-medium text-[#7c7c7c]">
                Project Session: <span className="font-mono text-[#0e121b]">{conversationId?.slice(0, 8)}...</span>
              </div>
              <button
                onClick={handleNewAd}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white hover:bg-[#fafaf8] border border-[#e1e4ea] text-[11px] font-semibold text-[#0021cc] shadow-xs hover:border-[#0021cc]/30 transition active:scale-95 cursor-pointer"
                title="Start a new UGC video ad project"
              >
                <Plus className="w-3 h-3" />
                <span>New Ad</span>
              </button>
            </div>

            {messages.map((msg) => (
              <MessageItem key={msg.id} message={msg} />
            ))}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Bottom Input Bar */}
      <div className="shrink-0 py-3 bg-white border-t border-[#e1e4ea]/60">
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          showSuggestions={!isRehydrating && messages.length === 0}
        />
      </div>
    </div>
  );
}
