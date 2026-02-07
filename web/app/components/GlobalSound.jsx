'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

export default function GlobalSound() {
  const audioRef = useRef(null);
  const [muted, setMuted] = useState(false);
  const [started, setStarted] = useState(false);

  // Load mute preference from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('howisstat_muted');
      if (stored === 'true') {
        setMuted(true);
      }
      // Default: unmuted
    } catch {}
  }, []);

  // Attempt to start playback after user gesture
  const tryPlay = useCallback(() => {
    if (started) return;
    const audio = audioRef.current;
    if (!audio) return;

    audio.volume = 0.25;
    audio.play().then(() => {
      setStarted(true);
    }).catch(() => {
      // Browser blocked autoplay — will retry on next interaction
    });
  }, [started]);

  // Listen for any user interaction to start audio
  useEffect(() => {
    const handler = () => tryPlay();
    document.addEventListener('click', handler);
    document.addEventListener('keydown', handler);
    document.addEventListener('touchstart', handler);
    return () => {
      document.removeEventListener('click', handler);
      document.removeEventListener('keydown', handler);
      document.removeEventListener('touchstart', handler);
    };
  }, [tryPlay]);

  // Sync mute state to audio element and localStorage
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.muted = muted;
    }
    try {
      localStorage.setItem('howisstat_muted', String(muted));
    } catch {}
  }, [muted]);

  const toggle = () => {
    setMuted(prev => !prev);
    tryPlay(); // ensure audio is started on click
  };

  return (
    <>
      <audio ref={audioRef} src="/audio/background.mp3" loop preload="auto" />
      <button
        className="global-mute-btn"
        onClick={toggle}
        aria-label={muted ? 'Unmute' : 'Mute'}
        title={muted ? 'Unmute' : 'Mute'}
      >
        {muted ? (
          // Speaker muted icon
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <line x1="23" y1="9" x2="17" y2="15" />
            <line x1="17" y1="9" x2="23" y2="15" />
          </svg>
        ) : (
          // Speaker on icon
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          </svg>
        )}
      </button>
    </>
  );
}
