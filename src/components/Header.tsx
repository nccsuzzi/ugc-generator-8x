'use client';

import React from 'react';
import { Video } from 'lucide-react';

export default function Header() {
  return (
    <header className="shrink-0 z-30 w-full border-b border-[#e1e4ea] bg-white/90 backdrop-blur-md transition-colors">
      <div className="max-w-4xl mx-auto px-6 h-16 flex items-center">
        {/* Icon + Title + Subtitle only */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#0021cc] flex items-center justify-center text-white shadow-md shadow-[#0021cc]/25 shrink-0">
            <Video className="w-4.5 h-4.5" />
          </div>
          <div>
            <h1 className="text-base font-display font-bold text-[#0e121b] tracking-tight leading-tight">
              UGC Video Generator
            </h1>
            <p className="text-xs text-[#525866] font-normal leading-normal">
              Paste a product URL to assemble a vertical 9:16 video
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
