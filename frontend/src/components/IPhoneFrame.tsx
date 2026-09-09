'use client';

import React from 'react';

interface IPhoneFrameProps {
  children: React.ReactNode;
  concept?: string;
  textOverlay?: string;
  className?: string;
}

export default function IPhoneFrame({
  children,
  concept,
  textOverlay,
  className = '',
}: IPhoneFrameProps) {
  return (
    <div className={`relative mx-auto w-full max-w-[316px] select-none ${className}`}>
      {/* Hardware Buttons (Ultra-thin, subtle precision details) */}
      {/* Left: Action Button */}
      <div className="absolute -left-[1.5px] top-[76px] w-[1.5px] h-[18px] bg-[#2a2d34] rounded-l-[1px] shadow-sm z-10" />
      {/* Left: Volume Up */}
      <div className="absolute -left-[1.5px] top-[108px] w-[1.5px] h-[32px] bg-[#2a2d34] rounded-l-[1px] shadow-sm z-10" />
      {/* Left: Volume Down */}
      <div className="absolute -left-[1.5px] top-[150px] w-[1.5px] h-[32px] bg-[#2a2d34] rounded-l-[1px] shadow-sm z-10" />
      {/* Right: Power / Side Button */}
      <div className="absolute -right-[1.5px] top-[116px] w-[1.5px] h-[46px] bg-[#2a2d34] rounded-r-[1px] shadow-sm z-10" />

      {/* Main Outer Titanium Chassis (iPhone 15/16 Pro silhouette) */}
      <div className="relative rounded-[48px] p-[9px] bg-gradient-to-b from-[#2a2d33] via-[#18191c] to-[#0e0f12] shadow-[0_25px_60px_-15px_rgba(0,0,0,0.35),0_0_0_1px_rgba(255,255,255,0.1)_inset,0_0_20px_rgba(0,0,0,0.2)] ring-1 ring-black/40">
        {/* Subtle Top Speaker Ear Slit */}
        <div className="absolute top-[4.5px] left-1/2 -translate-x-1/2 w-10 h-[2.5px] bg-[#0c0d10] rounded-full z-30" />

        {/* Inner Glass Display Screen Container */}
        <div className="relative aspect-[9/16] w-full rounded-[40px] overflow-hidden bg-black ring-1 ring-black shadow-inner">
          {/* Dynamic Island Notch Cutout (Apple 4.2:1 proportion, centered at top) */}
          <div className="absolute top-[11px] left-1/2 -translate-x-1/2 z-40 w-[72px] h-[17px] bg-black rounded-full flex items-center justify-end pr-[9px] shadow-[0_1px_3px_rgba(0,0,0,0.9)] ring-1 ring-white/10 pointer-events-none">
            {/* Sensor / Face ID dot */}
            <div className="w-[5px] h-[5px] rounded-full bg-[#0a0a0a] mr-[6px]" />
            {/* Front Camera Lens */}
            <div className="w-[7.5px] h-[7.5px] rounded-full bg-[#0d131f] ring-1 ring-white/10 flex items-center justify-center">
              <div className="w-[3px] h-[3px] rounded-full bg-[#1b2a40]/70" />
            </div>
          </div>

          {/* Screen Content (Video Player or Loading Skeleton) */}
          <div className="w-full h-full relative">
            {children}
          </div>

          {/* iOS Home Indicator Bar */}
          <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 z-30 w-28 h-1 bg-white/40 rounded-full pointer-events-none backdrop-blur-sm" />
        </div>
      </div>

      {/* Hook Concept Callout Card below Frame */}
      {(concept || textOverlay) && (
        <div className="mt-3 p-3.5 rounded-2xl bg-[#fafaf8] border border-[#e1e4ea] shadow-sm text-xs">
          <div className="text-[10px] uppercase font-bold tracking-wider text-[#525866] mb-1">
            Hook Concept
          </div>
          <div className="text-sm font-semibold text-[#0e121b] leading-snug">
            &ldquo;{textOverlay || concept}&rdquo;
          </div>
        </div>
      )}
    </div>
  );
}
