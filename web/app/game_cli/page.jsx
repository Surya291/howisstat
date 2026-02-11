'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

const BANNER = `
   ██╗  ██╗ ██████╗ ██╗    ██╗   ██╗███████╗   ███████╗████████╗ █████╗ ████████╗
   ██║  ██║██╔═══██╗██║    ██║   ██║██╔════╝   ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝
███████║██║   ██║██║ █╗ ██║   ██║███████╗   ███████╗   ██║   ███████║   ██║
██╔══██║██║   ██║██║███╗██║   ██║╚════██║   ╚════██║   ██║   ██╔══██║   ██║
██║  ██║╚██████╔╝╚███╔███╔╝██╗██║███████║██╗███████║   ██║   ██║  ██║   ██║
╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚═╝╚═╝╚══════╝╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝`;

export default function GameTerminal() {
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [showGuide, setShowGuide] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const lastSpokenCommentRef = useRef(null);
  const audioRef = useRef(null);

  // Detect mobile for suggestion hint (Tab vs zz)
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 640px)');
    setIsMobile(mq.matches);
    const h = () => setIsMobile(mq.matches);
    mq.addEventListener('change', h);
    return () => mq.removeEventListener('change', h);
  }, []);

  // Show guide on first visit
  useEffect(() => {
    try {
      if (!localStorage.getItem('howisstat_guide_seen')) {
        setShowGuide(true);
      }
    } catch {}
  }, []);

  const closeGuide = () => {
    setShowGuide(false);
    try {
      localStorage.setItem('howisstat_guide_seen', 'true');
    } catch {}
  };

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  const playCommentary = useCallback(async (comment) => {
    if (!comment) return;
    try {
      setIsSpeaking(true);

      // Stop any existing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const res = await fetch(`${API_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: comment }),
      });

      if (!res.ok) {
        // TTS is optional; on failure we just log and continue silently
        // eslint-disable-next-line no-console
        console.warn('TTS request failed', res.status);
        return;
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.play().catch(() => {
        // Playback can fail if user hasn't interacted yet; ignore
      });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn('TTS playback error', err);
    } finally {
      setIsSpeaking(false);
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  // When a new result with judge comment arrives, trigger TTS once
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    const lastResult = [...messages].reverse().find(
      (m) => m.type === 'result' && m.data && m.data.comment
    );
    if (!lastResult) return;

    const comment = lastResult.data.comment;
    if (!comment || comment === lastSpokenCommentRef.current) return;

    lastSpokenCommentRef.current = comment;
    playCommentary(comment);
  }, [messages, playCommentary]);

  // Auto-focus input
  useEffect(() => {
    if (!loading && prompt && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading, prompt]);

  // Initialize game on mount (guard against StrictMode double-invoke)
  const initRef = useRef(false);
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;
    sendAction(null, null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendAction = async (sid, userInput) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, input: userInput }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Server error (${res.status})`);
      }

      const data = await res.json();

      if (data.session_id) setSessionId(data.session_id);
      if (data.game_state) setGameState(data.game_state);

      // Echo user input
      if (userInput !== null && userInput !== undefined) {
        setMessages(prev => [...prev, { type: 'user_input', content: userInput }]);
      }

      // Append server messages
      if (data.messages && data.messages.length > 0) {
        setMessages(prev => [...prev, ...data.messages]);
      }

      setPrompt(data.prompt);
    } catch (e) {
      const isNetworkError = e.message === 'Failed to fetch' || e.name === 'TypeError';
      const hint = isNetworkError
        ? `Cannot reach ${API_URL}. Start the backend: python api_server.py (see README).`
        : e.message;
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Connection error: ${hint}. Make sure api_server.py is running.`
      }]);
      setPrompt({ type: 'retry', label: 'Retry', placeholder: 'Click Retry after starting the API' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (loading || !prompt) return;

    const value = input.trim();

    // Continue prompts allow empty input
    if (prompt.type !== 'continue' && !value) return;

    setInput('');
    sendAction(sessionId, value || '');
  };

  const handleNewGame = () => {
    setMessages([]);
    setSessionId(null);
    setGameState(null);
    setPrompt(null);
    sendAction(null, null);
  };

  // ═══════════════════════════════════════════════════════
  // Renderers
  // ═══════════════════════════════════════════════════════

  const renderCard = (card, key) => {
    const styles = [];
    if (card.batting_style) styles.push(card.batting_style);
    if (card.bowling_style) styles.push(card.bowling_style);

    return (
      <div key={key} className="card-row">
        <span className="card-idx">#{card.index}</span>
        <span className="card-name">{card.name}</span>
        {card.flag && <span className="card-flag">{card.flag}</span>}
        <span className="card-sep">•</span>
        <span className="card-role">{card.role}</span>
        {styles.length > 0 && (
          <>
            <span className="card-sep">•</span>
            <span className="card-styles">[{styles.join(' <> ')}]</span>
          </>
        )}
      </div>
    );
  };

  const renderMessage = (msg, idx) => {
    const k = `msg-${idx}`;

    switch (msg.type) {

      case 'banner':
        return (
          <div key={k} className="msg-enter">
            <pre className="msg-banner">{BANNER}</pre>
          </div>
        );

      case 'heading':
        return <div key={k} className="msg-heading msg-enter">{msg.content}</div>;

      case 'round_header':
        return <div key={k} className="msg-round-header msg-enter">ROUND {msg.round}</div>;

      case 'text':
        const textClass = msg.style === 'gold' ? 'msg-text msg-banner-subtitle gold msg-enter' : `msg-text ${msg.style || ''} msg-enter`;
        return <div key={k} className={textClass}>{msg.content}</div>;

      case 'error':
        return <div key={k} className="msg-error msg-enter">{msg.content}</div>;

      case 'separator':
        return <hr key={k} className={`msg-separator ${msg.style || ''} msg-enter`} />;

      case 'user_input':
        return (
          <div key={k} className="msg-user-input msg-enter">
            <span className="echo-prompt">❯</span>
            <span className="echo-text">{msg.content}</span>
          </div>
        );

      case 'franchise_list':
        return (
          <div key={k} className="franchise-list msg-enter">
            {msg.franchises.map(f => (
              <span key={f} className="franchise-item">{f}</span>
            ))}
          </div>
        );

      case 'difficulty_options':
        return (
          <div key={k} className="difficulty-options msg-enter">
            <div className="diff-opt">
              <span className="diff-key gully">G</span>
              <span className="diff-name">Gully</span>
              <span className="diff-desc">— Beginner: Simple stats, 50-50 chance</span>
            </div>
            <div className="diff-opt">
              <span className="diff-key domestic">D</span>
              <span className="diff-name">Domestic</span>
              <span className="diff-desc">— Intermediate: Broad stats, balanced</span>
            </div>
            <div className="diff-opt">
              <span className="diff-key sachin">S</span>
              <span className="diff-name">Sachin Mode</span>
              <span className="diff-desc">— Expert: Deep stats, maximum difficulty</span>
            </div>
          </div>
        );

      case 'setup_summary':
        return (
          <div key={k} className="setup-summary msg-enter">
            {Object.entries({
              'Your team': msg.data.self_franchise,
              'Opponent': msg.data.opponent_franchise,
              'Year(s)': msg.data.years,
              'Difficulty': msg.data.difficulty,
              'Cards each': msg.data.cards_each,
            }).map(([label, value]) => (
              <div key={label} className="setup-row">
                <span className="setup-label">{label}</span>
                <span className="setup-value">{value}</span>
              </div>
            ))}
          </div>
        );

      case 'cards':
        return (
          <div key={k} className="cards-box msg-enter">
            <div className="cards-title">{msg.title}</div>
            {msg.cards.map((c, i) => renderCard(c, `${k}-card-${i}`))}
          </div>
        );

      case 'visibility':
        return renderVisibility(msg, k);

      case 'dialogue':
        return (
          <div key={k} className={`dlg-box ${msg.style || ''} msg-enter`}>
            <div className="dlg-title">{msg.title}</div>
            <div className="dlg-msg">{msg.message}</div>
            {msg.reasoning && <div className="dlg-reason">{msg.reasoning}</div>}
          </div>
        );

      case 'result':
        return renderResult(msg.data, k);

      case 'game_over':
        return renderGameOver(msg, k);

      default:
        return null;
    }
  };

  const renderVisibility = (msg, k) => {
    const isChallenger = msg.role === 'challenger';
    return (
      <div key={k} className="vis-panel msg-enter">
        <div className="vis-header">
          <span className="vis-role">
            YOUR ROLE: {isChallenger ? 'Challenger' : 'Defender'}
          </span>
          <span className="vis-deck">
            You: <span className="cnt">{msg.deck_sizes.user}</span>
            {' | '}
            AI: <span className="cnt">{msg.deck_sizes.ai}</span>
          </span>
        </div>
        <div className="vis-body">
          {isChallenger ? (
            <>
              <div className="vis-label">YOUR CARD (FORCED)</div>
              {msg.top_card && renderCard(msg.top_card, `${k}-top`)}
            </>
          ) : (
            <>
              <div className="vis-label">YOUR CARDS — CHOOSE A DEFENDER</div>
              {msg.cards && msg.cards.map((c, i) => renderCard(c, `${k}-card-${i}`))}
            </>
          )}
        </div>
      </div>
    );
  };

  const renderResult = (data, k) => (
    <div key={k} className="res-box msg-enter">
      <div className="res-header">ROUND REVEAL</div>

      {/* Battle */}
      <div className="res-section">
        <div className="res-section-title">BATTLE</div>
        <div className="res-line">
          <span className="res-label">Challenger</span>
          <span>{data.challenger.name} {data.challenger.flag} [{data.challenger.role}]</span>
        </div>
        <div className="res-line">
          <span className="res-label">Defender</span>
          <span>{data.defender.name} {data.defender.flag} [{data.defender.role}]</span>
        </div>
        <div className="res-line">
          <span className="res-label">Stat</span>
          <span className="res-stat">&ldquo;{data.stat}&rdquo;</span>
        </div>
      </div>

      {/* Stat Values */}
      {data.stat_values && (
        <div className="res-section">
          <div className="res-section-title">STAT VALUES</div>
          {Object.entries(data.stat_values).map(([key, val]) => (
            <div key={key} className="res-val-row">
              <span className="res-val-key">{key}</span>
              <span className="res-val-val">{String(val)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Winner */}
      <div className="res-section">
        <div className={`res-winner ${data.winner_side === 'user' ? 'you' : 'ai'}`}>
          WINNER: {data.winner?.toUpperCase()} ({data.winner_side === 'user' ? 'YOU' : 'AI'})
        </div>
      </div>

      {/* Judge Comment */}
      {data.comment && (
        <div className="res-section">
          <div className="res-section-title">COMMENTARY</div>
          <div className="res-comment-row">
            <div className="res-comment">{data.comment}</div>
            <button
              type="button"
              className="res-comment-replay-btn"
              onClick={() => playCommentary(data.comment)}
              disabled={isSpeaking}
              aria-label="Replay commentary"
              title="Replay commentary"
            >
              🎙
            </button>
          </div>
        </div>
      )}

      {/* Role Switch */}
      {data.roles_switched && (
        <div className="res-section">
          <div className="res-switch">Roles have switched!</div>
        </div>
      )}
    </div>
  );

  const renderGameOver = (msg, k) => {
    const win = msg.winner === 'user';
    return (
      <div key={k} className="gameover-box msg-enter">
        <div className="gameover-header">GAME OVER</div>
        <div className={`gameover-body ${win ? 'win' : 'lose'}`}>
          <div className="gameover-big">{win ? 'CONGRATULATIONS! YOU WIN!' : 'DEFEAT! AI WINS!'}</div>
          <div className="gameover-score">
            Final score: You={msg.user_cards} | AI={msg.ai_cards}
          </div>
        </div>
      </div>
    );
  };

  // ═══════════════════════════════════════════════════════
  // Layout
  // ═══════════════════════════════════════════════════════

  return (
    <div className="terminal">
      {/* Status Bar */}
      <div className="status-bar">
        <span className="status-title">HOW.IS.STAT</span>
        {gameState && (
          <div className="status-stats">
            <span className="stat-item">
              Round <span className="stat-value">{gameState.round}</span>
            </span>
            <span className="stat-item">
              You <span className="stat-value">{gameState.user_cards}</span>
            </span>
            <span className="stat-item">
              AI <span className="stat-value">{gameState.ai_cards}</span>
            </span>
            <span className="stat-item">
              <span className="stat-value" style={{ textTransform: 'capitalize' }}>
                {gameState.role}
              </span>
            </span>
          </div>
        )}
        <button
          className="guide-btn"
          onClick={() => setShowGuide(true)}
          aria-label="Game Guide"
          title="Game Guide"
        >
          ?
        </button>
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.map((msg, idx) => renderMessage(msg, idx))}

        {loading && (
          <div className="msg-text ai_thinking msg-enter">
            <span className="loading-dots">
              <span></span><span></span><span></span>
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        {prompt && prompt.type === 'retry' ? (
          <div style={{ textAlign: 'center', padding: '6px 0' }}>
            <div className="input-label">{prompt.label}</div>
            <button
              type="button"
              onClick={() => sendAction(null, null)}
              disabled={loading}
              className="new-game-btn"
            >
              {loading ? 'Connecting…' : 'Retry'}
            </button>
          </div>
        ) : prompt ? (
          <>
            <div className="input-label">
              {prompt.label}
              {prompt.suggestion && (
                <span className="input-label-hint">
                  {' — '}
                  {isMobile ? 'Type zz to fill suggested stat' : 'Press Tab to fill suggested stat'}
                </span>
              )}
            </div>
            <form onSubmit={handleSubmit} className="input-wrapper">
              <span className="input-prompt">❯</span>
              <input
                ref={inputRef}
                type="text"
                className="input-field"
                value={input}
                onChange={(e) => {
                  const v = e.target.value;
                  if (isMobile && v === 'zz' && prompt?.suggestion) {
                    setInput(prompt.suggestion);
                    return;
                  }
                  setInput(v);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Tab' && prompt.suggestion) {
                    e.preventDefault();
                    setInput(prompt.suggestion);
                  }
                }}
                placeholder={
                  prompt.type === 'continue'
                    ? 'Press Enter to continue...'
                    : (prompt.placeholder || '')
                }
                disabled={loading}
                autoComplete="off"
                spellCheck={false}
              />
            </form>
          </>
        ) : loading ? (
          <div className="input-label" style={{ textAlign: 'center' }}>
            Loading...
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '6px 0' }}>
            <button onClick={handleNewGame} className="new-game-btn">
              NEW GAME
            </button>
          </div>
        )}
      </div>

      {/* Game Guide Modal */}
      {showGuide && (
        <div className="guide-overlay" onClick={closeGuide}>
          <div className="guide-modal" onClick={(e) => e.stopPropagation()}>
            <div className="guide-header">
              <span className="guide-title">Game Guide</span>
              <button className="guide-close" onClick={closeGuide} aria-label="Close guide">&times;</button>
            </div>
            <div className="guide-body">
              <div className="guide-section">
                <h3 className="guide-section-title">Roles</h3>
                <p><strong>Challenger</strong> — plays their top card (forced) and declares a stat.</p>
                <p><strong>Defender</strong> — picks the best card from their hand to compete.</p>
                <p>You start as Challenger, AI starts as Defender.</p>
              </div>
              <div className="guide-section">
                <h3 className="guide-section-title">Each Round</h3>
                <p><strong>As Challenger:</strong> See your top card, declare a stat (e.g. &ldquo;Most runs in IPL&rdquo;), then AI picks their defender.</p>
                <p><strong>As Defender:</strong> AI declares a stat, then you pick which card to defend with.</p>
              </div>
              <div className="guide-section">
                <h3 className="guide-section-title">Winning Rounds</h3>
                <p>Challenger wins &rarr; keeps both cards, stays challenger.</p>
                <p>Defender wins (or tie) &rarr; gets both cards, becomes the new challenger.</p>
              </div>
              <div className="guide-section">
                <h3 className="guide-section-title">Win Condition</h3>
                <p>Game ends when one side has <strong>0 cards</strong>. The other side wins.</p>
              </div>
              <div className="guide-section">
                <h3 className="guide-section-title">Example Stats</h3>
                <ul>
                  <li>&ldquo;Most runs in IPL&rdquo;</li>
                  <li>&ldquo;Best bowling average in Tests&rdquo;</li>
                  <li>&ldquo;Most sixes in T20Is&rdquo;</li>
                  <li>&ldquo;Best economy in death overs&rdquo;</li>
                </ul>
              </div>
              <div className="guide-section">
                <h3 className="guide-section-title">Tips</h3>
                <ul>
                  <li>Think about your card&apos;s strengths when declaring stats.</li>
                  <li>As defender, pick the card most likely to beat the stat.</li>
                  <li>Bluffing matters — the AI doesn&apos;t see your card when you&apos;re challenger.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
