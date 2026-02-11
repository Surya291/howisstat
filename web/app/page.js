'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import ScoreboardNumber from './components/ScoreboardNumber';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

export default function Home() {
  const [games, setGames] = useState(0);
  const [rounds, setRounds] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data) {
          setGames(data.games ?? 0);
          setRounds(data.rounds ?? 0);
        }
      })
      .catch(() => {});
  }, []);

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
          <div className="hero-stats">
            <div className="hero-stats-block">
              <span className="hero-stats-label">Games</span>
              <div className="hero-stats-scoreboard">
                <ScoreboardNumber value={games} />
              </div>
            </div>
            <span className="hero-stats-divider">||</span>
            <div className="hero-stats-block">
              <span className="hero-stats-label">Rounds</span>
              <div className="hero-stats-scoreboard">
                <ScoreboardNumber value={rounds} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
