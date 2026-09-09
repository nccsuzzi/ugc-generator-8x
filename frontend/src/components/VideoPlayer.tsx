'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Download, Sparkles, RefreshCw } from 'lucide-react';
import { getVideoFileUrl, getVideoDownloadUrl } from '../lib/api';
import { VideoMetadata } from '../types/chat';
import IPhoneFrame from './IPhoneFrame';

interface VideoPlayerProps {
  metadata: VideoMetadata;
}

export default function VideoPlayer({ metadata }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState('0:00');

  const fileUrl = getVideoFileUrl(metadata.id);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (video.readyState >= 2) {
      setIsLoaded(true);
    }

    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise
        .then(() => setIsPlaying(true))
        .catch((err) => {
          if (err.name !== 'AbortError') {
            setIsPlaying(false);
          }
        });
    }
  }, [fileUrl]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (!video.paused) {
      video.pause();
      setIsPlaying(false);
    } else {
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => setIsPlaying(true))
          .catch((err) => {
            if (err.name !== 'AbortError') {
              console.warn('Playback error:', err);
            }
          });
      }
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    const dur = videoRef.current.duration || 7;
    setProgress((curr / dur) * 100);
    const secs = Math.floor(curr % 60);
    setCurrentTime(`0:0${secs}`);
  };

  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      const downloadEndpoint = getVideoDownloadUrl(metadata.id);
      const response = await fetch(downloadEndpoint);
      if (!response.ok) {
        if (response.status === 410) {
          alert('This video download link has expired (24h retention window).');
          return;
        }
        throw new Error(`Download failed with status ${response.status}`);
      }

      // Try to read safe filename from Content-Disposition header
      let filename = '';
      const disposition = response.headers.get('content-disposition');
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      if (!filename) {
        const cleanConcept = (metadata.concept || 'ugc-video')
          .toLowerCase()
          .replace(/^(pov|hook)\s*:\s*/i, '')
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-+|-+$/g, '')
          .slice(0, 40);
        const dateStr = new Date().toISOString().split('T')[0];
        filename = `${cleanConcept || 'ugc-video'}_${dateStr}.mp4`;
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
      }, 500);
    } catch (err) {
      console.error('Download error, falling back to direct link:', err);
      const fallbackUrl = getVideoDownloadUrl(metadata.id);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = fallbackUrl;
      a.download = `ugc-video-${metadata.id.slice(0, 8)}.mp4`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
      }, 500);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <IPhoneFrame
      concept={metadata.concept}
      textOverlay={metadata.text_overlay}
      className="animate-entrance"
    >
      <div className="w-full h-full relative bg-[#0e121b] group overflow-hidden">
        <video
          ref={videoRef}
          src={fileUrl}
          autoPlay
          playsInline
          loop
          preload="auto"
          muted={isMuted}
          onLoadedMetadata={() => setIsLoaded(true)}
          onLoadedData={() => setIsLoaded(true)}
          onCanPlay={() => setIsLoaded(true)}
          onPlaying={() => setIsLoaded(true)}
          onTimeUpdate={handleTimeUpdate}
          onEnded={() => setIsPlaying(false)}
          className={`w-full h-full object-cover cursor-pointer transition-opacity duration-300 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onClick={togglePlay}
        />

        {/* Shimmer Skeleton Placeholder while video is buffering / decoding */}
        {!isLoaded && (
          <div className="absolute inset-0 z-10 flex flex-col justify-between px-3.5 pt-[44px] pb-5 bg-[#fafaf8] pointer-events-none">
            <div
              className="absolute -inset-[100%] bg-gradient-to-r from-transparent via-white/80 to-transparent animate-shimmer-light"
              style={{ transform: 'skewX(-20deg)' }}
            />
            {/* Top Badges during video loading (Cleanly 16px below notch) */}
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/95 backdrop-blur-md border border-[#e1e4ea] text-[10.5px] font-semibold text-[#0021cc] shadow-sm">
                <RefreshCw className="w-3 h-3 animate-spin text-[#0021cc]" />
                <span>Buffering Video</span>
              </div>
              <div className="px-2.5 py-1 rounded-full bg-white/95 backdrop-blur-md border border-[#e1e4ea] text-[10.5px] font-mono font-semibold text-[#525866] shadow-sm">
                9:16
              </div>
            </div>
            <div className="relative z-10 flex flex-col items-center justify-center my-auto">
              <div className="w-10 h-10 rounded-full bg-[#0021cc]/10 text-[#0021cc] border border-[#0021cc]/20 flex items-center justify-center animate-pulse mb-2.5 shadow-sm">
                <RefreshCw className="w-4.5 h-4.5 animate-spin" />
              </div>
              <div className="text-xs font-medium text-[#525866]">Buffering stream...</div>
            </div>
            <div className="relative z-10 w-full h-1.5 bg-[#e1e4ea] rounded-full overflow-hidden mb-1">
              <div className="h-full w-2/3 bg-[#0021cc] animate-pulse" />
            </div>
          </div>
        )}

        {/* Top Badges: Positioned at safe-area top inset top-[44px] cleanly below Dynamic Island */}
        {isLoaded && (
          <div className="absolute top-[44px] left-3.5 right-3.5 flex items-center justify-between pointer-events-none z-20">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-[10.5px] font-semibold text-white shadow-sm">
              <Sparkles className="w-3 h-3 text-[#0021cc]" />
              <span>9:16 UGC</span>
            </div>
            <div className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-[10.5px] font-mono font-medium text-white shadow-sm">
              {currentTime} / 0:0{metadata.duration || 7}
            </div>
          </div>
        )}

        {/* Center Play Button Overlay when paused */}
        {isLoaded && !isPlaying && (
          <div
            onClick={togglePlay}
            className="absolute inset-0 z-20 flex items-center justify-center bg-black/30 backdrop-blur-[1.5px] cursor-pointer"
          >
            <div className="w-13 h-13 rounded-full bg-[#0021cc] text-white flex items-center justify-center shadow-2xl shadow-[#0021cc]/50 transform transition hover:scale-105 active:scale-95">
              <Play className="w-5 h-5 ml-1 fill-white" />
            </div>
          </div>
        )}

        {/* Bottom Control Bar */}
        {isLoaded && (
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/95 via-black/50 to-transparent p-3 pb-5 pt-8 flex flex-col gap-2 transition-opacity z-20">
            {/* Progress bar */}
            <div className="w-full h-1 bg-white/25 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#0021cc] to-blue-400 transition-all duration-100"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between text-white text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={togglePlay}
                  className="p-1.5 rounded-full hover:bg-white/20 transition text-white"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
                </button>

                <button
                  onClick={toggleMute}
                  className="p-1.5 rounded-full hover:bg-white/20 transition text-white"
                  title={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
                </button>
              </div>

              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0021cc] hover:bg-[#001baa] disabled:opacity-75 text-white shadow-md transition text-[11px] font-semibold active:scale-95 cursor-pointer"
                title="Download video ad to device"
              >
                {isDownloading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </IPhoneFrame>
  );
}
