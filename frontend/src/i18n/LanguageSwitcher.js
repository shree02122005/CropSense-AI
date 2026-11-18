import React, { useEffect, useRef, useState } from 'react';
import { Globe, Check, ChevronDown } from 'lucide-react';
import { useI18n } from './LanguageContext';

/**
 * Language picker.
 *  - variant="inline"   : sits inside a navbar
 *  - variant="floating" : fixed to the bottom-right corner (used on inner pages)
 */
export default function LanguageSwitcher({ variant = 'inline' }) {
  const { lang, setLang, languages, meta, t } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onDoc = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = e => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDoc); document.removeEventListener('keydown', onKey); };
  }, [open]);

  const floating = variant === 'floating';

  return (
    <div
      ref={ref}
      style={floating
        ? { position: 'fixed', right: 16, bottom: 16, zIndex: 1000 }
        : { position: 'relative' }}
    >
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('common.chooseLanguage')}
        title={t('common.chooseLanguage')}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: floating ? 'rgba(5,20,10,0.92)' : 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(74,222,128,0.35)', borderRadius: 999,
          padding: '7px 12px', cursor: 'pointer', color: '#86efac',
          fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-b)',
          boxShadow: floating ? '0 6px 24px rgba(0,0,0,0.45)' : 'none',
          backdropFilter: 'blur(8px)', whiteSpace: 'nowrap',
        }}
      >
        <Globe size={15} />
        <span>{meta.name}</span>
        <ChevronDown size={13} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label={t('common.language')}
          style={{
            position: 'absolute', right: 0,
            ...(floating ? { bottom: 'calc(100% + 8px)' } : { top: 'calc(100% + 8px)' }),
            listStyle: 'none', margin: 0, padding: 6, minWidth: 210,
            maxHeight: 'min(60vh, 420px)', overflowY: 'auto',
            background: '#07150c', border: '1px solid rgba(74,222,128,0.25)',
            borderRadius: 14, boxShadow: '0 16px 40px rgba(0,0,0,0.55)', zIndex: 1001,
          }}
        >
          {languages.map(l => {
            const active = l.code === lang;
            return (
              <li key={l.code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  lang={l.code}
                  onClick={() => { setLang(l.code); setOpen(false); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
                    padding: '9px 12px', borderRadius: 10, border: 'none', cursor: 'pointer', textAlign: 'left',
                    background: active ? 'rgba(74,222,128,0.14)' : 'transparent',
                    color: active ? '#4ade80' : '#e5e7eb', fontFamily: 'var(--font-b)',
                  }}
                  onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                  onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                >
                  <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.25 }}>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{l.name}</span>
                    {l.code !== 'en' && <span style={{ fontSize: 11, color: '#6b7280' }}>{l.english}</span>}
                  </span>
                  {active && <Check size={15} />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
