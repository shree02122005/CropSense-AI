/**
 * Supported UI languages.
 *
 * To add a language (Indian or foreign):
 *   1. Create src/i18n/translations/<code>.js exporting an object with the
 *      same keys as en.js (missing keys automatically fall back to English).
 *   2. Import it in src/i18n/translations/index.js.
 *   3. Add an entry below. Set dir: 'rtl' for right-to-left scripts
 *      (e.g. Urdu, Arabic) and `locale` for date formatting.
 */
export const LANGUAGES = [
  { code: 'en', name: 'English',   english: 'English',   locale: 'en-IN', dir: 'ltr' },
  { code: 'hi', name: 'हिन्दी',      english: 'Hindi',     locale: 'hi-IN', dir: 'ltr' },
  { code: 'kn', name: 'ಕನ್ನಡ',       english: 'Kannada',   locale: 'kn-IN', dir: 'ltr' },
  { code: 'te', name: 'తెలుగు',      english: 'Telugu',    locale: 'te-IN', dir: 'ltr' },
  { code: 'ta', name: 'தமிழ்',       english: 'Tamil',     locale: 'ta-IN', dir: 'ltr' },
  { code: 'ml', name: 'മലയാളം',     english: 'Malayalam', locale: 'ml-IN', dir: 'ltr' },
  { code: 'mr', name: 'मराठी',       english: 'Marathi',   locale: 'mr-IN', dir: 'ltr' },
  { code: 'bn', name: 'বাংলা',       english: 'Bengali',   locale: 'bn-IN', dir: 'ltr' },
  { code: 'gu', name: 'ગુજરાતી',     english: 'Gujarati',  locale: 'gu-IN', dir: 'ltr' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ',      english: 'Punjabi',   locale: 'pa-IN', dir: 'ltr' },
  { code: 'or', name: 'ଓଡ଼ିଆ',       english: 'Odia',      locale: 'or-IN', dir: 'ltr' },
];

export const DEFAULT_LANGUAGE = 'en';

export const getLanguage = code =>
  LANGUAGES.find(l => l.code === code) || LANGUAGES.find(l => l.code === DEFAULT_LANGUAGE);
