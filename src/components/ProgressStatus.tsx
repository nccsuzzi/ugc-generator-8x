'use client';

import React from 'react';
import {
  Loader2,
  Globe,
  Sparkles,
  Search,
  Music2,
  Film,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { VideoGenerationStatus } from '../types/chat';
import IPhoneFrame from './IPhoneFrame';

interface ProgressStatusProps {
  status: VideoGenerationStatus;
  currentStage?: string;
  stageMessage?: string;
  error?: string;
}

const STAGES = [
  { id: 'extracting', label: 'Extracting product facts', icon: Globe },
  { id: 'analyzing', label: 'Analyzing audience angles', icon: Sparkles },
  { id: 'searching_assets', label: 'Searching licensed media', icon: Search },
  { id: 'adapting_audio', label: 'Adapting soundtrack', icon: Music2 },
  { id: 'rendering', label: 'Compositing 4-layer UGC', icon: Film },
  { id: 'validating', label: 'Validating QA & licensing', icon: ShieldCheck },
];

export default function ProgressStatus({
  status,
  currentStage,
  stageMessage,
  error,
}: ProgressStatusProps) {
  if (status === 'expired') {
    return (
      <IPhoneFrame className="animate-entrance">
        <div className="w-full h-full flex flex-col items-center justify-center px-6 pt-[44px] pb-6 text-center bg-[#fafaf8] select-none">
          <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center mb-3">
            <Clock className="w-6 h-6" />
          </div>
          <div className="text-sm font-semibold text-[#0e121b] mb-1.5 font-display">
            Video Link Expired
          </div>
          <p className="text-xs text-[#525866] leading-relaxed font-normal mb-3">
            UGC video assets are retained for 24 hours. This video is no longer available for stream or download.
          </p>
          <div className="px-3 py-1 rounded-full bg-white border border-[#e1e4ea] text-[10.5px] font-medium text-[#7c7c7c]">
            24h retention window passed
          </div>
        </div>
      </IPhoneFrame>
    );
  }

  if (status === 'failed') {
    return (
      <IPhoneFrame className="animate-entrance">
        <div className="w-full h-full flex flex-col items-center justify-center px-6 pt-[44px] pb-6 text-center bg-[#fff1f2] select-none">
          <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mb-3">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="text-sm font-semibold text-[#9f1239] mb-2 font-display">
            Generation Failed
          </div>
          <p className="text-xs text-[#be123c] leading-relaxed font-normal">
            {error || 'An unexpected error occurred during rendering.'}
          </p>
        </div>
      </IPhoneFrame>
    );
  }

  // Determine stage progress
  const stageOrder = [
    'extracting',
    'analyzing',
    'searching_assets',
    'adapting_audio',
    'rendering',
    'validating',
    'completed',
  ];

  // Map legacy status to stage if currentStage not supplied
  const effectiveStage =
    currentStage ||
    (status === 'extracting'
      ? 'extracting'
      : status === 'planning'
      ? 'analyzing'
      : status === 'rendering'
      ? 'rendering'
      : 'extracting');

  const currentIndex = stageOrder.indexOf(effectiveStage);
  const activeIndex = currentIndex >= 0 ? currentIndex : 0;
  const progressPercent = Math.min(
    100,
    Math.max(12, Math.round(((activeIndex + 1) / stageOrder.length) * 100))
  );

  return (
    <IPhoneFrame className="animate-entrance">
      {/* 
        Safe-Area Top Inset: pt-[44px] ensures all top status elements start cleanly
        16px below the Dynamic Island notch (which sits at top: 11px, height: 17px, bottom: 28px).
      */}
      <div className="w-full h-full relative bg-[#fafaf8] overflow-hidden flex flex-col justify-between px-3.5 pt-[44px] pb-5">
        {/* Soft Light Shimmer Overlay */}
        <div
          className="absolute -inset-[100%] bg-gradient-to-r from-transparent via-white/80 to-transparent animate-shimmer-light pointer-events-none"
          style={{ transform: 'skewX(-20deg)' }}
        />

        {/* Top Header Badges (Row placed cleanly below notch) */}
        <div className="relative z-10 flex items-center justify-between pointer-events-none mb-1">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/95 backdrop-blur-md border border-[#e1e4ea] shadow-sm text-[10.5px] font-semibold text-[#0021cc]">
            <Loader2 className="w-3 h-3 animate-spin text-[#0021cc]" />
            <span>Assembling UGC</span>
          </div>
          <div className="px-2.5 py-1 rounded-full bg-white/95 backdrop-blur-md border border-[#e1e4ea] text-[10.5px] font-mono font-semibold text-[#525866] shadow-sm">
            {progressPercent}%
          </div>
        </div>

        {/* Center Stage Card & Milestone Checklist */}
        <div className="relative z-10 my-auto py-1">
          {/* Active Stage Callout Card */}
          <div className="p-3 rounded-xl bg-white border border-[#e1e4ea] shadow-sm mb-3">
            <div className="text-[9.5px] uppercase font-bold tracking-wider text-[#0021cc] mb-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0021cc] animate-ping" />
              <span>Current Pipeline Stage</span>
            </div>
            <p className="text-xs font-semibold text-[#0e121b] leading-snug min-h-[30px] flex items-center">
              {stageMessage || 'Searching licensed media catalogs...'}
            </p>
          </div>

          {/* 6-Stage Milestone Tracker */}
          <div className="space-y-1.5 px-0.5">
            {STAGES.map((st, idx) => {
              const isDone = activeIndex > idx;
              const isCurrent = activeIndex === idx;
              const Icon = st.icon;

              return (
                <div key={st.id} className="flex items-center gap-2 text-xs">
                  <div
                    className={`w-4.5 h-4.5 rounded-full flex items-center justify-center shrink-0 text-[10px] transition-all duration-300 ${
                      isDone
                        ? 'bg-[#f0fdf4] text-[#15803d] border border-[#bbf7d0]'
                        : isCurrent
                        ? 'bg-[#0021cc]/10 text-[#0021cc] border border-[#0021cc]/30 shadow-sm'
                        : 'bg-white text-[#7c7c7c] border border-[#e1e4ea]'
                    }`}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-3 h-3 text-[#16a34a]" />
                    ) : isCurrent ? (
                      <Loader2 className="w-3 h-3 animate-spin text-[#0021cc]" />
                    ) : (
                      <Icon className="w-2.5 h-2.5 text-[#7c7c7c]" />
                    )}
                  </div>

                  <span
                    className={`transition-colors duration-200 text-[11px] truncate font-normal ${
                      isDone
                        ? 'text-[#7c7c7c] line-through opacity-70'
                        : isCurrent
                        ? 'text-[#0e121b] font-semibold'
                        : 'text-[#525866]'
                    }`}
                  >
                    {st.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Progress Bar */}
        <div className="relative z-10 pt-2">
          <div className="w-full h-1.5 bg-[#e1e4ea] rounded-full overflow-hidden mb-1.5">
            <div
              className="h-full bg-gradient-to-r from-[#0021cc] to-[#001baa] transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="text-[9.5px] text-center text-[#7c7c7c] tracking-wide font-normal">
            Pexels stock • Giphy reactions • Epidemic Sound
          </div>
        </div>
      </div>
    </IPhoneFrame>
  );
}
