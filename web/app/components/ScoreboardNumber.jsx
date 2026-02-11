'use client';

import { useEffect, useState } from 'react';

// 7-segment encoding: a=top, b=top-right, c=bottom-right, d=bottom, e=bottom-left, f=top-left, g=middle
const SEGMENTS = {
  0: ['a', 'b', 'c', 'd', 'e', 'f'],
  1: ['b', 'c'],
  2: ['a', 'b', 'd', 'e', 'g'],
  3: ['a', 'b', 'c', 'd', 'g'],
  4: ['b', 'c', 'f', 'g'],
  5: ['a', 'c', 'd', 'f', 'g'],
  6: ['a', 'c', 'd', 'e', 'f', 'g'],
  7: ['a', 'b', 'c'],
  8: ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
  9: ['a', 'b', 'c', 'd', 'f', 'g'],
};

function SevenSegmentDigit({ digit }) {
  const lit = SEGMENTS[digit] || [];
  return (
    <svg
      className="seg7-svg"
      viewBox="0 0 44 70"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <filter id="seg7-glow">
          <feGaussianBlur stdDeviation="0.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      {/* a - top */}
      <rect x="6" y="0" width="32" height="8" rx="2" className={lit.includes('a') ? 'seg7-on' : 'seg7-off'} />
      {/* b - top-right */}
      <rect x="34" y="6" width="8" height="26" rx="2" className={lit.includes('b') ? 'seg7-on' : 'seg7-off'} />
      {/* c - bottom-right */}
      <rect x="34" y="38" width="8" height="26" rx="2" className={lit.includes('c') ? 'seg7-on' : 'seg7-off'} />
      {/* d - bottom */}
      <rect x="6" y="62" width="32" height="8" rx="2" className={lit.includes('d') ? 'seg7-on' : 'seg7-off'} />
      {/* e - bottom-left */}
      <rect x="2" y="38" width="8" height="26" rx="2" className={lit.includes('e') ? 'seg7-on' : 'seg7-off'} />
      {/* f - top-left */}
      <rect x="2" y="6" width="8" height="26" rx="2" className={lit.includes('f') ? 'seg7-on' : 'seg7-off'} />
      {/* g - middle */}
      <rect x="6" y="34" width="32" height="8" rx="2" className={lit.includes('g') ? 'seg7-on' : 'seg7-off'} />
    </svg>
  );
}

function DigitColumn({ digit, index }) {
  return (
    <div className="scoreboard-digit-box">
      <div className="scoreboard-digit-col" style={{ animationDelay: `${index * 40}ms` }}>
        <div
          className="scoreboard-digit-strip"
          style={{ transform: `translateY(-${digit * 10}%)` }}
        >
          {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((d) => (
            <div key={d} className="scoreboard-digit-cell">
              <SevenSegmentDigit digit={d} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ScoreboardNumber({ value, pad = 3 }) {
  const [mounted, setMounted] = useState(false);

  const str = String(Math.max(0, Math.floor(value))).padStart(pad, '0');
  const digits = str.split('').map(Number);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={`scoreboard-number scoreboard-7seg ${mounted ? 'scoreboard-ready' : ''}`}>
      {digits.map((d, i) => (
        <DigitColumn key={i} digit={d} index={i} />
      ))}
    </div>
  );
}
