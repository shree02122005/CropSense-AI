import React, { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bot, BookOpen, ChevronDown, ChevronUp, Loader, LocateFixed, MapPin, Mic, MicOff,
  RefreshCw, Search, Send, Sprout, Square, Trash2, Volume2, VolumeX, X,
} from 'lucide-react';
import { useI18n } from '../i18n/LanguageContext';

const API = process.env.REACT_APP_API_URL?.replace(/\/+$/, '') || '';
const CHAT_URL = `${API}/chat`;
const LOCATION_URL = `${API}/chat/location`;
const RESET_URL = `${API}/chat/reset`;
const TTS_URL = `${API}/chat/tts`;

// Speech-recognition locale per app language (Chrome / Edge Web Speech API).
const STT_LOCALE = {
  en: 'en-IN', hi: 'hi-IN', kn: 'kn-IN', te: 'te-IN', ta: 'ta-IN', ml: 'ml-IN',
  mr: 'mr-IN', bn: 'bn-IN', gu: 'gu-IN', pa: 'pa-Guru-IN', or: 'or-IN',
};
// Languages the backend can speak (gTTS). Others fall back to a browser voice if one exists.
const SERVER_TTS = new Set(['en', 'hi', 'kn', 'te', 'ta', 'ml', 'mr', 'bn', 'gu', 'pa']);
const AUTO_SPEAK_KEY = 'cropsense.chat.autoSpeak';
const SESSION_KEY = 'cropsense.chat.session';

const SpeechRecognitionImpl = typeof window !== 'undefined'
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

const newId = () => (window.crypto?.randomUUID?.() || `s-${Date.now()}-${Math.random().toString(36).slice(2)}`);
const getSessionId = () => {
  try {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) { id = newId(); sessionStorage.setItem(SESSION_KEY, id); }
    return id;
  } catch { return newId(); }
};

/** Fields of the latest analysis the assistant may use (coordinates are sent separately, as location). */
const summarizeResult = r => r ? ({
  location: r.location, soil_type: r.soil_type, soil_confidence: r.soil_confidence,
  N: r.N, P: r.P, K: r.K, npk_district: r.npk_district,
  npk_out_of_training_range: r.npk_out_of_training_range, npk_ood_features: r.npk_ood_features,
  ph: r.ph, organic_carbon: r.organic_carbon,
  temperature: r.temperature, humidity: r.humidity, rainfall: r.rainfall,
  crops: (r.crops || []).slice(0, 3).map(c => ({
    name: c.name, confidence: c.confidence, season: c.season, water_need: c.water_need, profit: c.profit,
  })),
}) : null;

const fmt = (v, nd = 1) => (v === null || v === undefined ? '–' : Number(v).toFixed(nd));
const SUIT_COLOR = { good: '#4ade80', possible: '#fbbf24', not_recommended: '#f87171' };

export default function ChatWidget({ result, bottomOffset = 16 }) {
  const { t, lang, meta } = useI18n();
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([]);          // {role, content, lang, error?, crops?, sources?}
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState(null);
  const [notice, setNotice] = useState('');
  const [autoSpeak, setAutoSpeak] = useState(() => {
    try { return localStorage.getItem(AUTO_SPEAK_KEY) !== 'off'; } catch { return true; }
  });
  // Location + SoilGrids
  const [location, setLocation] = useState(null);        // {lat, lon, name}
  const [soil, setSoil] = useState(null);                // soil summary from backend
  const [soilLoading, setSoilLoading] = useState(false);
  const [soilOpen, setSoilOpen] = useState(false);
  const [placeQuery, setPlaceQuery] = useState('');
  const [showPlaceSearch, setShowPlaceSearch] = useState(false);
  const [locBusy, setLocBusy] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef = useRef(null);
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const usedResultRef = useRef(null);

  useEffect(() => {
    try { localStorage.setItem(AUTO_SPEAK_KEY, autoSpeak ? 'on' : 'off'); } catch { /* ignore */ }
  }, [autoSpeak]);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, loading]);

  // ── Location & soil ───────────────────────────────────────────────────────
  const applyLocation = useCallback(async (loc, refresh = false) => {
    setLocation(loc);
    setSoilLoading(true);
    setNotice('');
    try {
      const res = await axios.post(LOCATION_URL, { session_id: sessionId, location: loc, refresh }, { timeout: 120000 });
      setSoil(res.data.soil);
      setSoilOpen(true);
    } catch {
      setNotice(t('chat.soilFailed'));
    } finally {
      setSoilLoading(false);
    }
  }, [sessionId, t]);

  // Reuse the location of the latest analysis automatically.
  useEffect(() => {
    if (result?.latitude != null && result?.longitude != null && usedResultRef.current !== result) {
      usedResultRef.current = result;
      applyLocation({ lat: result.latitude, lon: result.longitude, name: result.location_name || result.location });
    }
  }, [result, applyLocation]);

  const useMyLocation = () => {
    if (!navigator.geolocation) { setNotice(t('errors.geoUnsupported')); return; }
    setLocBusy(true);
    navigator.geolocation.getCurrentPosition(
      p => { setLocBusy(false); applyLocation({ lat: p.coords.latitude, lon: p.coords.longitude, name: t('chat.myLocation') }); },
      err => { setLocBusy(false); setNotice(err.code === 1 ? t('errors.geoDenied') : t('errors.geoFailed')); },
      { timeout: 10000 },
    );
  };

  const searchPlace = async () => {
    const q = placeQuery.trim();
    if (!q) return;
    setLocBusy(true);
    try {
      const res = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=1`, { timeout: 8000 });
      const hit = res.data?.[0];
      if (!hit) { setNotice(t('errors.locationNotFound')); return; }
      setShowPlaceSearch(false);
      setPlaceQuery('');
      applyLocation({ lat: parseFloat(hit.lat), lon: parseFloat(hit.lon), name: hit.display_name.split(',').slice(0, 3).join(',') });
    } catch {
      setNotice(t('errors.searchFailed'));
    } finally {
      setLocBusy(false);
    }
  };

  // ── Voice output ──────────────────────────────────────────────────────────
  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      if (audioRef.current.src?.startsWith('blob:')) URL.revokeObjectURL(audioRef.current.src);
      audioRef.current = null;
    }
    try { window.speechSynthesis?.cancel(); } catch { /* ignore */ }
    setSpeakingIdx(null);
  }, []);

  const speak = useCallback(async (text, replyLang, idx) => {
    stopSpeaking();
    setSpeakingIdx(idx);
    try {
      if (SERVER_TTS.has(replyLang)) {
        const res = await axios.post(TTS_URL, { text, language: replyLang }, { responseType: 'blob', timeout: 30000 });
        const url = URL.createObjectURL(res.data);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => { URL.revokeObjectURL(url); if (audioRef.current === audio) { audioRef.current = null; setSpeakingIdx(null); } };
        await audio.play();
        return;
      }
      const synth = window.speechSynthesis;
      const voice = synth?.getVoices().find(v => v.lang?.toLowerCase().startsWith(replyLang));
      if (!voice) { setNotice(t('chat.voiceUnavailable')); setSpeakingIdx(null); return; }
      const u = new SpeechSynthesisUtterance(text);
      u.voice = voice; u.lang = voice.lang;
      u.onend = () => setSpeakingIdx(null);
      synth.speak(u);
    } catch {
      setNotice(t('chat.voiceFailed'));
      setSpeakingIdx(null);
    }
  }, [stopSpeaking, t]);

  // ── Sending ───────────────────────────────────────────────────────────────
  const send = useCallback(async (raw) => {
    const text = (raw ?? '').trim();
    if (!text || loading) return;
    setNotice('');
    stopSpeaking();
    setSoilOpen(false);                       // give the conversation room; the card stays one tap away
    setMessages(prev => [...prev, { role: 'user', content: text, lang }]);
    setInput('');
    setLoading(true);
    try {
      const res = await axios.post(CHAT_URL, {
        session_id: sessionId, message: text, ui_language: lang, context: summarizeResult(result),
      }, { timeout: 120000 });
      if (res.data?.soil) setSoil(res.data.soil);
      if (!res.data?.reply) {
        setMessages(prev => [...prev, { role: 'assistant', content: t('chat.refused'), lang, error: true }]);
        return;
      }
      const reply = {
        role: 'assistant', content: res.data.reply, lang: res.data.language || lang,
        crops: res.data.crops || [], sources: res.data.sources || [], offline: res.data.provider === 'offline',
      };
      const replyIdx = messagesRef.current.length;
      setMessages(prev => [...prev, reply]);
      if (autoSpeak && !reply.offline) speak(reply.content, reply.lang, replyIdx);
    } catch (e) {
      const code = e?.response?.data?.detail?.code;
      const key = code === 'not_configured' ? 'chat.notConfigured'
        : code === 'busy' ? 'chat.busy'
        : e?.response ? 'chat.failed' : 'chat.offline';
      setMessages(prev => [...prev, { role: 'assistant', content: t(key), lang, error: true }]);
    } finally {
      setLoading(false);
    }
  }, [loading, lang, result, sessionId, autoSpeak, speak, stopSpeaking, t]);

  // ── Voice input ───────────────────────────────────────────────────────────
  const stopListening = useCallback(() => {
    try { recognitionRef.current?.stop(); } catch { /* ignore */ }
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognitionImpl) { setNotice(t('chat.micUnsupported')); return; }
    stopSpeaking();
    setNotice('');
    const rec = new SpeechRecognitionImpl();
    rec.lang = STT_LOCALE[lang] || 'en-IN';
    rec.interimResults = true;
    rec.continuous = false;
    rec.maxAlternatives = 1;
    let finalText = '';
    rec.onresult = ev => {
      let interim = '';
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const r = ev.results[i];
        if (r.isFinal) finalText += r[0].transcript; else interim += r[0].transcript;
      }
      setInput((finalText + interim).trim());
    };
    rec.onerror = ev => {
      if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') setNotice(t('chat.micDenied'));
      else if (ev.error === 'no-speech') setNotice(t('chat.noSpeech'));
      else if (ev.error === 'language-not-supported') setNotice(t('chat.micLangUnsupported'));
      else if (ev.error !== 'aborted') setNotice(t('chat.micFailed'));
    };
    rec.onend = () => {
      setListening(false);
      recognitionRef.current = null;
      if (finalText.trim()) send(finalText);
    };
    recognitionRef.current = rec;
    setListening(true);
    try { rec.start(); } catch { setListening(false); }
  }, [lang, send, stopSpeaking, t]);

  useEffect(() => { if (!open) { stopListening(); stopSpeaking(); } }, [open, stopListening, stopSpeaking]);
  useEffect(() => () => { stopListening(); stopSpeaking(); }, [stopListening, stopSpeaking]);
  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 150); }, [open]);

  const clearChat = () => {
    stopSpeaking();
    axios.post(RESET_URL, { session_id: sessionId }).catch(() => {});
    const id = newId();
    try { sessionStorage.setItem(SESSION_KEY, id); } catch { /* ignore */ }
    setSessionId(id);
    setMessages([]); setNotice(''); setSoil(null);
    if (location) setTimeout(() => applyLocationRef.current?.(location), 0);   // re-attach soil to the new session
  };
  const applyLocationRef = useRef(applyLocation);
  applyLocationRef.current = applyLocation;

  const suggestions = [
    t('chat.sugCrops'), t('chat.sugExplainSoil'), t('chat.sugFertilizer'), t('chat.sugImprove'), t('chat.sugTomato'),
  ];

  return (
    <>
      {/* Launcher */}
      <AnimatePresence>
        {!open && (
          <motion.button
            key="chat-launcher"
            initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }}
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => setOpen(true)}
            aria-label={t('chat.open')} title={t('chat.open')}
            style={{
              position: 'fixed', right: 16, bottom: bottomOffset, zIndex: 1100,
              display: 'flex', alignItems: 'center', gap: 8, padding: '12px 18px',
              borderRadius: 999, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg,#4ade80,#16a34a)', color: '#04130a',
              fontWeight: 700, fontSize: 14, fontFamily: 'var(--font-h)',
              boxShadow: '0 8px 28px rgba(22,163,74,0.45)',
            }}
          >
            <Bot size={20} /> <span>{t('chat.launcher')}</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Panel */}
      <AnimatePresence>
        {open && (
          <motion.section
            key="chat-panel"
            role="dialog" aria-label={t('chat.title')}
            initial={{ opacity: 0, y: 24, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 24, scale: 0.98 }}
            transition={{ duration: 0.22 }}
            style={{
              position: 'fixed', right: 16, bottom: 16, zIndex: 1100,
              width: 'min(430px, calc(100vw - 32px))', height: 'min(680px, calc(100vh - 32px))',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              background: '#06110a', border: '1px solid rgba(74,222,128,0.28)', borderRadius: 20,
              boxShadow: '0 24px 60px rgba(0,0,0,0.6)', fontFamily: 'var(--font-b)',
            }}
          >
            {/* Header */}
            <header style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 12px 10px', borderBottom: '1px solid rgba(255,255,255,0.07)', background: 'rgba(74,222,128,0.06)' }}>
              <div style={{ width: 36, height: 36, borderRadius: 12, background: 'rgba(74,222,128,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4ade80', flexShrink: 0 }}>
                <Bot size={20} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: 'var(--font-h)', fontWeight: 800, color: '#f0fdf4', fontSize: 15 }}>{t('chat.title')}</div>
                <div style={{ fontSize: 11, color: '#86efac', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {t('chat.subtitleRag')} · {meta.name}
                </div>
              </div>
              <IconBtn onClick={() => { if (autoSpeak) stopSpeaking(); setAutoSpeak(v => !v); }} label={autoSpeak ? t('chat.voiceOn') : t('chat.voiceOff')}>
                {autoSpeak ? <Volume2 size={17} /> : <VolumeX size={17} />}
              </IconBtn>
              <IconBtn onClick={clearChat} label={t('chat.clear')} disabled={!messages.length}><Trash2 size={16} /></IconBtn>
              <IconBtn onClick={() => setOpen(false)} label={t('chat.close')}><X size={18} /></IconBtn>
            </header>

            {/* Location bar */}
            <div style={{ padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)', fontSize: 12 }}>
              {location ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MapPin size={14} color="#4ade80" style={{ flexShrink: 0 }} />
                  <span style={{ color: '#d1fae5', flex: 1, minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                    title={`${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`}>
                    {location.name || `${location.lat.toFixed(3)}, ${location.lon.toFixed(3)}`}
                  </span>
                  <SmallBtn onClick={() => applyLocation(location, true)} disabled={soilLoading} label={t('chat.refreshSoil')}><RefreshCw size={12} /></SmallBtn>
                  <SmallBtn onClick={() => setShowPlaceSearch(v => !v)} label={t('chat.changeLocation')}>{t('chat.changeLocation')}</SmallBtn>
                </div>
              ) : (
                <div>
                  <div style={{ color: '#9ca3af', marginBottom: 6 }}>{t('chat.locationPrompt')}</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <SmallBtn onClick={useMyLocation} disabled={locBusy} primary label={t('chat.useMyLocation')}>
                      {locBusy ? <Loader size={12} className="spin" /> : <LocateFixed size={12} />} {t('chat.useMyLocation')}
                    </SmallBtn>
                    <SmallBtn onClick={() => setShowPlaceSearch(v => !v)} label={t('chat.searchPlace')}><Search size={12} /> {t('chat.searchPlace')}</SmallBtn>
                  </div>
                </div>
              )}
              {showPlaceSearch && (
                <form onSubmit={e => { e.preventDefault(); searchPlace(); }} style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                  <input value={placeQuery} onChange={e => setPlaceQuery(e.target.value)} placeholder={t('analysis.searchPlaceholder')}
                    style={{ flex: 1, padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: '#f0fdf4', fontSize: 12, fontFamily: 'var(--font-b)' }} />
                  <SmallBtn type="submit" disabled={locBusy} primary label={t('analysis.search')}>{t('analysis.search')}</SmallBtn>
                  {location && <SmallBtn onClick={useMyLocation} disabled={locBusy} label={t('chat.useMyLocation')}><LocateFixed size={12} /></SmallBtn>}
                </form>
              )}
              {(soilLoading || soil) && (
                <SoilCard soil={soil} loading={soilLoading} open={soilOpen} onToggle={() => setSoilOpen(v => !v)} t={t} />
              )}
            </div>

            {/* Messages */}
            <div ref={listRef} aria-live="polite" style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {messages.length === 0 && (
                <div>
                  <Bubble role="assistant">{t('chat.greetingRag')}</Bubble>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                    {suggestions.map(s => (
                      <button key={s} onClick={() => send(s)} disabled={loading}
                        style={{ textAlign: 'left', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(74,222,128,0.25)', color: '#bbf7d0', borderRadius: 999, padding: '7px 11px', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-b)' }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m, i) => (
                <Bubble key={i} role={m.role} error={m.error} lang={m.lang}>
                  {m.content}
                  {m.crops?.length > 0 && <CropCards crops={m.crops} t={t} />}
                  {m.sources?.length > 0 && (
                    <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      <span style={{ fontSize: 10, color: '#6b7280', display: 'flex', alignItems: 'center', gap: 3 }}><BookOpen size={10} /> {t('chat.sources')}:</span>
                      {m.sources.map(s => (
                        <span key={s.id} title={`${s.title} › ${s.section}`}
                          style={{ fontSize: 10, color: '#a7f3d0', background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 6, padding: '1px 6px', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {s.section}
                        </span>
                      ))}
                    </div>
                  )}
                  {m.role === 'assistant' && !m.error && !m.offline && (
                    <div style={{ marginTop: 6, display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => (speakingIdx === i ? stopSpeaking() : speak(m.content, m.lang, i))}
                        aria-label={speakingIdx === i ? t('chat.stop') : t('chat.listen')}
                        style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'transparent', border: '1px solid rgba(74,222,128,0.3)', color: '#86efac', borderRadius: 999, padding: '3px 9px', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-b)' }}>
                        {speakingIdx === i ? <Square size={11} /> : <Volume2 size={12} />}
                        {speakingIdx === i ? t('chat.stop') : t('chat.listen')}
                      </button>
                    </div>
                  )}
                </Bubble>
              ))}

              {loading && (
                <Bubble role="assistant">
                  <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                    {[0, 1, 2].map(d => (
                      <motion.span key={d} animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: d * 0.2 }}
                        style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
                    ))}
                    <span style={{ marginLeft: 6, color: '#86efac', fontSize: 12 }}>{t('chat.thinkingRag')}</span>
                  </span>
                </Bubble>
              )}
            </div>

            {notice && (
              <div role="status" style={{ margin: '0 12px 8px', padding: '7px 10px', borderRadius: 10, background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', color: '#fde68a', fontSize: 12 }}>
                {notice}
              </div>
            )}

            {/* Input */}
            <form onSubmit={e => { e.preventDefault(); send(input); }}
              style={{ display: 'flex', alignItems: 'flex-end', gap: 8, padding: 10, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
              <button type="button" onClick={listening ? stopListening : startListening} disabled={loading}
                aria-label={listening ? t('chat.micStop') : t('chat.micStart')} title={listening ? t('chat.micStop') : t('chat.micStart')}
                style={{
                  width: 42, height: 42, flexShrink: 0, borderRadius: 12, cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: listening ? '1px solid #f87171' : '1px solid rgba(74,222,128,0.35)',
                  background: listening ? 'rgba(248,113,113,0.15)' : 'rgba(74,222,128,0.08)',
                  color: listening ? '#f87171' : '#4ade80',
                  animation: listening ? 'chatPulse 1.2s ease-in-out infinite' : 'none',
                }}>
                {listening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
              <textarea
                ref={inputRef} rows={1} value={input} maxLength={1000}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input); } }}
                placeholder={listening ? t('chat.listening') : t('chat.placeholder')}
                lang={lang}
                style={{
                  flex: 1, resize: 'none', minHeight: 42, maxHeight: 110, padding: '10px 12px', borderRadius: 12,
                  border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: '#f0fdf4',
                  fontSize: 14, fontFamily: 'var(--font-b)', outline: 'none', lineHeight: 1.4,
                }}
              />
              <button type="submit" disabled={loading || !input.trim()} aria-label={t('chat.send')} title={t('chat.send')}
                style={{
                  width: 42, height: 42, flexShrink: 0, borderRadius: 12, border: 'none',
                  cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: loading || !input.trim() ? 'rgba(74,222,128,0.2)' : 'linear-gradient(135deg,#4ade80,#16a34a)',
                  color: '#04130a',
                }}>
                <Send size={17} />
              </button>
            </form>
            <div style={{ padding: '0 12px 8px', fontSize: 10, color: '#4b5563', textAlign: 'center' }}>{t('chat.disclaimer')}</div>
            <style>{'@keyframes chatPulse{0%,100%{box-shadow:0 0 0 0 rgba(248,113,113,0.5)}50%{box-shadow:0 0 0 6px rgba(248,113,113,0)}}@keyframes spin{to{transform:rotate(360deg)}}.spin{animation:spin 0.8s linear infinite}'}</style>
          </motion.section>
        )}
      </AnimatePresence>
    </>
  );
}

// ── Soil summary card ───────────────────────────────────────────────────────
function SoilCard({ soil, loading, open, onToggle, t }) {
  if (loading) {
    return (
      <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8, color: '#86efac', fontSize: 12 }}>
        <Loader size={13} className="spin" /> {t('chat.fetchingSoil')}
      </div>
    );
  }
  if (!soil) return null;
  const ok = soil.status === 'ok' || soil.status === 'partial';
  const statusText = t(`chat.soilStatus_${soil.status}`);
  const top = r => r.depths?.['0-5cm'] || {};
  return (
    <div style={{ marginTop: 8, border: '1px solid rgba(74,222,128,0.18)', borderRadius: 12, background: 'rgba(74,222,128,0.04)' }}>
      <button onClick={onToggle} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 6, padding: '7px 10px', background: 'transparent', border: 'none', cursor: 'pointer', color: ok ? '#bbf7d0' : '#fde68a', fontSize: 12, fontFamily: 'var(--font-b)', textAlign: 'left' }}>
        <Sprout size={13} />
        <span style={{ flex: 1 }}>
          <strong>{t('chat.soilTitle')}</strong> · {ok
            ? [soil.texture_class, soil.ph_class && `pH ${soil.ph_class}`].filter(Boolean).join(' · ')
            : statusText}
        </span>
        {open ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>
      {open && (
        <div style={{ padding: '0 10px 10px', fontSize: 11, color: '#d1d5db' }}>
          {ok ? (
            <>
              {soil.nearest_cell_distance_m > 150 && (
                <div style={{ color: '#fbbf24', marginBottom: 6 }}>
                  📍 {t('chat.nearestCell', { m: Math.round(soil.nearest_cell_distance_m / 10) * 10 })}
                </div>
              )}
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 6 }}>
                <thead>
                  <tr style={{ color: '#6b7280', textAlign: 'left' }}>
                    <th style={{ fontWeight: 600, padding: '2px 0' }}>{t('chat.property')}</th>
                    <th style={{ fontWeight: 600 }}>0-5</th><th style={{ fontWeight: 600 }}>5-15</th><th style={{ fontWeight: 600 }}>15-30 cm</th>
                  </tr>
                </thead>
                <tbody>
                  {soil.rows.map(r => (
                    <tr key={r.property} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
                      title={`${t('chat.range90')}: ${fmt(top(r).q05, 2)} – ${fmt(top(r).q95, 2)} ${r.unit}`}>
                      <td style={{ padding: '3px 0', color: '#a7f3d0' }}>{t(`chat.prop_${r.property}`)} <span style={{ color: '#6b7280' }}>({r.unit})</span></td>
                      {['0-5cm', '5-15cm', '15-30cm'].map(d => (
                        <td key={d}>{fmt(r.depths?.[d]?.mean, r.unit === 'pH' || r.unit === 'kg/dm³' ? 2 : 1)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {soil.flags?.length > 0 && (
                <div style={{ marginBottom: 6 }}>
                  {soil.flags.map(f => <div key={f.flag} style={{ color: '#fde68a' }}>⚠ {f.flag} — {f.evidence}</div>)}
                </div>
              )}
              {soil.missing_properties?.length > 0 && <div style={{ color: '#fbbf24' }}>{t('chat.notRetrieved')}: {soil.missing_properties.join(', ')}</div>}
            </>
          ) : (
            <div style={{ color: '#fde68a', marginBottom: 6 }}>{statusText}</div>
          )}
          <div style={{ color: '#9ca3af', marginTop: 4 }}>{t('chat.notProvided')}</div>
          <div style={{ color: '#6b7280', marginTop: 4 }}>{t('chat.estimateNote')}</div>
        </div>
      )}
    </div>
  );
}

// ── Crop recommendation cards ───────────────────────────────────────────────
function CropCards({ crops, t }) {
  return (
    <div style={{ marginTop: 8, display: 'grid', gap: 6 }}>
      {crops.map((c, i) => {
        const color = SUIT_COLOR[c.suitability] || '#9ca3af';
        return (
          <div key={i} style={{ border: `1px solid ${color}40`, background: `${color}0f`, borderRadius: 10, padding: '7px 9px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
              <strong style={{ fontSize: 13 }}>🌱 {c.crop}</strong>
              <span style={{ fontSize: 10, fontWeight: 700, color, border: `1px solid ${color}60`, borderRadius: 999, padding: '1px 7px' }}>
                {t(`chat.suit_${c.suitability}`)}
              </span>
            </div>
            {c.reasons?.map((r, j) => <div key={j} style={{ fontSize: 12, color: '#d1fae5', marginTop: 2 }}>✓ {r}</div>)}
            {c.cautions?.map((r, j) => <div key={j} style={{ fontSize: 12, color: '#fde68a', marginTop: 2 }}>! {r}</div>)}
          </div>
        );
      })}
    </div>
  );
}

function Bubble({ role, error, lang, children }) {
  const user = role === 'user';
  return (
    <div lang={lang} style={{
      alignSelf: user ? 'flex-end' : 'flex-start', maxWidth: user ? '85%' : '94%',
      background: error ? 'rgba(239,68,68,0.1)' : user ? 'linear-gradient(135deg,#16a34a,#15803d)' : 'rgba(255,255,255,0.05)',
      border: error ? '1px solid rgba(239,68,68,0.3)' : user ? 'none' : '1px solid rgba(255,255,255,0.08)',
      color: error ? '#fca5a5' : '#f0fdf4',
      borderRadius: user ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
      padding: '10px 12px', fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
    }}>
      {children}
    </div>
  );
}

function IconBtn({ onClick, label, disabled, children }) {
  return (
    <button type="button" onClick={onClick} disabled={disabled} aria-label={label} title={label}
      style={{
        width: 32, height: 32, borderRadius: 10, border: '1px solid rgba(255,255,255,0.1)',
        background: 'transparent', color: disabled ? '#374151' : '#9ca3af', cursor: disabled ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
      {children}
    </button>
  );
}

function SmallBtn({ onClick, label, disabled, primary, type = 'button', children }) {
  return (
    <button type={type} onClick={onClick} disabled={disabled} aria-label={label} title={label}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '5px 9px', borderRadius: 8, fontSize: 11, fontWeight: 600,
        border: primary ? 'none' : '1px solid rgba(74,222,128,0.3)', cursor: disabled ? 'not-allowed' : 'pointer',
        background: primary ? 'linear-gradient(135deg,#4ade80,#16a34a)' : 'transparent',
        color: primary ? '#04130a' : '#86efac', fontFamily: 'var(--font-b)', whiteSpace: 'nowrap', opacity: disabled ? 0.6 : 1,
      }}>
      {children}
    </button>
  );
}
