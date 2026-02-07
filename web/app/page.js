'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="hero">
      <div className="hero-overlay" />
      <div className="hero-content">
        <div className="hero-top">
        </div>
        <div className="hero-bottom">
          <Link href="/game_cli" className="hero-play-btn">
            PLAY
          </Link>
        </div>
      </div>
    </div>
  );
}
