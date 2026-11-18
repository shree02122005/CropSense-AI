import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { LANGUAGES, DEFAULT_LANGUAGE, getLanguage } from './languages';
import translations from './translations';

const STORAGE_KEY = 'cropsense.language';

const LanguageContext = createContext(null);

const lookup = (dict, key) =>
  key.split('.').reduce((node, part) => (node && typeof node === 'object' ? node[part] : undefined), dict);

const interpolate = (str, vars) =>
  vars ? str.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined && vars[k] !== null ? String(vars[k]) : m)) : str;

const readStoredLanguage = () => {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved && LANGUAGES.some(l => l.code === saved)) return saved;
  } catch { /* storage unavailable */ }
  // First visit: use the browser language if we support it.
  try {
    const browser = (navigator.language || '').slice(0, 2).toLowerCase();
    if (LANGUAGES.some(l => l.code === browser)) return browser;
  } catch { /* ignore */ }
  return DEFAULT_LANGUAGE;
};

/**
 * Builds a translator for a language code. Missing keys fall back to English,
 * then to `fallback` (or the key itself) so the UI never shows blanks.
 */
export const makeTranslator = code => (key, vars, fallback) => {
  let value = lookup(translations[code], key);
  if (typeof value !== 'string') value = lookup(translations[DEFAULT_LANGUAGE], key);
  if (typeof value !== 'string') value = fallback !== undefined ? fallback : key;
  return interpolate(value, vars);
};

const normKey = v => String(v ?? '').toLowerCase().replace(/[^a-z]/g, '');

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(readStoredLanguage);
  const meta = getLanguage(lang);

  const setLang = useCallback(code => {
    setLangState(code);
    try { window.localStorage.setItem(STORAGE_KEY, code); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    document.documentElement.lang = meta.code;
    document.documentElement.dir = meta.dir;
  }, [meta]);

  const value = useMemo(() => {
    const t = makeTranslator(lang);
    // Helpers for values that arrive from the backend in English.
    const tv = (group, raw) => (raw === null || raw === undefined || raw === '' ? raw : t(`${group}.${normKey(raw)}`, null, String(raw)));
    return {
      lang,
      setLang,
      meta,
      languages: LANGUAGES,
      t,
      crop: name => tv('crops', name),
      soil: name => tv('soils', name),
      level: v => tv('levels', v),
      season: v => tv('seasons', v),
      formatDate: ts => {
        try { return new Date(ts).toLocaleString(meta.locale); } catch { return new Date(ts).toLocaleString(); }
      },
    };
  }, [lang, setLang, meta]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export const useI18n = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useI18n must be used inside <LanguageProvider>');
  return ctx;
};

/**
 * Maps a known English backend error (soil image validation, etc.) to a
 * translated message. Unknown messages are returned unchanged.
 */
export const translateBackendError = (msg, t) => {
  const m = String(msg || '').toLowerCase();
  const rules = [
    ['too blurry', 'errors.blurry'],
    ['too dark', 'errors.dark'],
    ['overexposed', 'errors.overexposed'],
    ['foliage', 'errors.foliage'],
    ['sky', 'errors.sky'],
    ['metallic', 'errors.synthetic'],
    ['artificial graphic', 'errors.graphic'],
    ['uncertain', 'errors.uncertain'],
    ['valid soil image', 'errors.invalidSoil'],
    ['only jpg/png', 'errors.invalidFile'],
    ['cannot connect to backend', 'errors.backendDown'],
    ['network error', 'errors.backendDown'],
  ];
  const hit = rules.find(([needle]) => m.includes(needle));
  return hit ? t(hit[1]) : msg;
};
