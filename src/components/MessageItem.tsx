'use client';

import React from 'react';
import { Bot } from 'lucide-react';
import { ChatMessage } from '../types/chat';
import VideoPlayer from './VideoPlayer';
import ProgressStatus from './ProgressStatus';

interface MessageItemProps {
  message: ChatMessage;
}

export default function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const meta = message.videoMetadata;

  if (isUser) {
    return (
      <div className="flex justify-end my-3 animate-entrance">
        <div className="max-w-[85%] sm:max-w-[75%] px-4 py-2.5 rounded-2xl bg-[#0021cc] text-white shadow-sm text-sm font-normal leading-relaxed break-words">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3.5 my-4 justify-start animate-entrance">
      {/* Claude-style Assistant Avatar */}
      <div className="w-7 h-7 rounded-lg bg-[#0021cc]/10 text-[#0021cc] border border-[#0021cc]/15 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Bot className="w-4 h-4" />
      </div>

      {/* Assistant Content Flow (Plain Text + Embedded Result Card) */}
      <div className="flex-1 max-w-[92%] sm:max-w-[85%] space-y-3">
        {/* Unboxed plain text response */}
        <div className="text-sm text-[#0e121b] leading-relaxed font-normal whitespace-pre-wrap break-words py-0.5">
          {message.content}
        </div>

        {/* Inline Result Card (Video Player or Progress Status) */}
        {message.videoId && meta && (
          <div className="pt-1">
            {meta.status === 'completed' ? (
              <VideoPlayer metadata={meta} />
            ) : (
              <ProgressStatus
                status={meta.status}
                currentStage={meta.current_stage}
                stageMessage={meta.stage_message}
                error={meta.error}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
