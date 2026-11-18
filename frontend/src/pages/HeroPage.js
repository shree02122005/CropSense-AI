import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sprout, 
  ArrowRight, 
  ArrowDown, 
  UploadCloud, 
  Cpu, 
  Layers, 
  TrendingUp, 
  Menu, 
  X, 
  Activity, 
  MapPin, 
  Thermometer, 
  Droplets, 
  CheckCircle2, 
  Sparkles,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { useI18n } from '../i18n/LanguageContext';
import LanguageSwitcher from '../i18n/LanguageSwitcher';

export default function HeroPage({ onStart, onHistory }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { t, crop, level, soil } = useI18n();

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const stats = [
    { value: '23', label: t('stats.cropTypes') },
    { value: '93.04%', label: t('stats.accuracy') },
    { value: '93.22%', label: t('stats.precision') },
    { value: '93.04%', label: t('stats.recall') },
    { value: '93.00%', label: t('stats.f1') },
    { value: 'CNN + RF', label: t('stats.pipeline') }
  ];

  const steps = [
    {
      num: '01',
      title: t('how.s1Title'),
      desc: t('how.s1Desc'),
      detail: t('how.s1Detail'),
      icon: <UploadCloud size={22} />
    },
    {
      num: '02',
      title: t('how.s2Title'),
      desc: t('how.s2Desc'),
      detail: t('how.s2Detail'),
      icon: <Cpu size={22} />
    },
    {
      num: '03',
      title: t('how.s3Title'),
      desc: t('how.s3Desc'),
      detail: t('how.s3Detail'),
      icon: <Layers size={22} />
    },
    {
      num: '04',
      title: t('how.s4Title'),
      desc: t('how.s4Desc'),
      detail: t('how.s4Detail'),
      icon: <TrendingUp size={22} />
    }
  ];

  const features = [
    {
      title: t('features.f1Title'),
      desc: t('features.f1Desc'),
      icon: <Sparkles size={24} />
    },
    {
      title: t('features.f2Title'),
      desc: t('features.f2Desc'),
      icon: <MapPin size={24} />
    },
    {
      title: t('features.f3Title'),
      desc: t('features.f3Desc'),
      icon: <Thermometer size={24} />
    },
    {
      title: t('features.f4Title'),
      desc: t('features.f4Desc'),
      icon: <Activity size={24} />
    }
  ];

  return (
    <div style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      
      {/* ── 1. Sticky Navigation Bar ────────────────────────────────────────── */}
      <nav className="navbar-wrapper" aria-label="Main Navigation">
        <div className="navbar-container">
          <div className="navbar-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="brand-icon-wrapper">
              <Sprout size={20} />
            </div>
            <span>CropSense AI</span>
          </div>

          <ul className="navbar-links">
            <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="nav-link">{t('nav.home')}</button></li>
            <li><button onClick={() => scrollToSection('how-it-works')} className="nav-link">{t('nav.howItWorks')}</button></li>
            <li><button onClick={() => scrollToSection('features')} className="nav-link">{t('nav.features')}</button></li>
            <li><button onClick={() => scrollToSection('preview')} className="nav-link">{t('nav.preview')}</button></li>
            {onHistory && (
              <li><button onClick={onHistory} className="nav-link">{t('nav.history')}</button></li>
            )}
          </ul>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <LanguageSwitcher />
            <button onClick={onStart} className="navbar-cta">
              {t('nav.startAnalysis')} <ArrowRight size={15} />
            </button>
            <button 
              className="mobile-menu-toggle" 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={t('nav.toggleMenu')}
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mobile-drawer"
            >
              <button onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); setMobileMenuOpen(false); }} className="nav-link" style={{ textAlign: 'left' }}>{t('nav.home')}</button>
              <button onClick={() => scrollToSection('how-it-works')} className="nav-link" style={{ textAlign: 'left' }}>{t('nav.howItWorks')}</button>
              <button onClick={() => scrollToSection('features')} className="nav-link" style={{ textAlign: 'left' }}>{t('nav.features')}</button>
              <button onClick={() => scrollToSection('preview')} className="nav-link" style={{ textAlign: 'left' }}>{t('nav.preview')}</button>
              {onHistory && (
                <button onClick={() => { onHistory(); setMobileMenuOpen(false); }} className="nav-link" style={{ textAlign: 'left' }}>{t('nav.queryHistory')}</button>
              )}
              <button onClick={() => { onStart(); setMobileMenuOpen(false); }} className="btn-primary" style={{ marginTop: 12, justifyContent: 'center' }}>
                {t('nav.startAnalysis')} <ArrowRight size={16} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* ── 2. Hero Section ─────────────────────────────────────────────────── */}
      <section className="hero-section" id="top">
        <div className="hero-texture-overlay" />
        <div className="hero-content">
          <motion.div 
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="hero-eyebrow"
          >
            <Sprout size={13} />
            <span>{t('hero.eyebrow')}</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="hero-title"
          >
            {t('hero.title1')} <br />
            <span className="hero-title-highlight">{t('hero.title2')}</span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="hero-description"
          >
            {t('hero.desc')}
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="hero-button-group"
          >
            <button onClick={onStart} className="btn-primary">
              {t('nav.startAnalysis')} <ArrowRight size={17} />
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="btn-secondary">
              {t('hero.explore')} <ArrowDown size={16} />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ── 3. Quick Stats (Documented Holdout Evaluation Metrics) ───────────── */}
      <section className="stats-section" aria-label="Model Performance Metrics">
        <div className="stats-container">
          <div className="stats-grid">
            {stats.map((st, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.08, duration: 0.4 }}
                className="stat-item-card"
              >
                <div className="stat-numeric-value">{st.value}</div>
                <div className="stat-descriptor-label">{st.label}</div>
              </motion.div>
            ))}
          </div>
          <p className="stats-footnote">
            {t('stats.footnote')}
          </p>
        </div>
      </section>

      {/* ── 4. How It Works Section ─────────────────────────────────────────── */}
      <section className="content-section" id="how-it-works">
        <div className="section-header">
          <span className="section-eyebrow">{t('how.eyebrow')}</span>
          <h2 className="section-headline">{t('how.headline')}</h2>
          <p className="section-subtext">
            {t('how.sub')}
          </p>
        </div>

        <div className="steps-grid">
          {steps.map((st, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1, duration: 0.5 }}
              className="step-card"
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <span className="step-number-badge">{st.num}</span>
                <div className="step-icon-box">{st.icon}</div>
              </div>
              <h3 className="step-title">{st.title}</h3>
              <p className="step-description">{st.desc}</p>
              <div style={{ marginTop: 'auto', paddingTop: 16, borderTop: '1px solid var(--border-light)', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                {st.detail}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── 5. Features Section ─────────────────────────────────────────────── */}
      <section className="content-section" id="features" style={{ paddingTop: 0 }}>
        <div className="section-header">
          <span className="section-eyebrow">{t('features.eyebrow')}</span>
          <h2 className="section-headline">{t('features.headline')}</h2>
          <p className="section-subtext">
            {t('features.sub')}
          </p>
        </div>

        <div className="features-grid">
          {features.map((feat, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1, duration: 0.45 }}
              className="feature-card"
            >
              <div className="feature-icon-box">
                {feat.icon}
              </div>
              <h3 className="feature-title">{feat.title}</h3>
              <p className="feature-text">{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── 6. Interactive Analysis Preview ─────────────────────────────────── */}
      <section className="content-section" id="preview" style={{ paddingTop: 0 }}>
        <div className="section-header">
          <span className="section-eyebrow">{t('preview.eyebrow')}</span>
          <h2 className="section-headline">{t('preview.headline')}</h2>
          <p className="section-subtext">
            {t('preview.sub')}
          </p>
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="preview-container"
        >
          <div className="preview-badge-header">
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--green-primary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {t('preview.sampleTitle')}
              </span>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: 2 }}>
                {t('preview.sampleLocation', { coords: '15.8497°N, 74.4977°E' })}
              </div>
            </div>
            <span className="preview-tag">{t('preview.tag')}</span>
          </div>

          {/* Environmental factors grid */}
          <div className="preview-metrics-grid">
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('result.soilType')}</div>
              <div className="preview-metric-val" style={{ color: 'var(--green-primary)' }}>{soil('clay')}</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('preview.availN')}</div>
              <div className="preview-metric-val">249.7 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('preview.availP')}</div>
              <div className="preview-metric-val">46.8 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('preview.availK')}</div>
              <div className="preview-metric-val">180.4 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('result.temperature')}</div>
              <div className="preview-metric-val">29.5°C</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('result.humidity')}</div>
              <div className="preview-metric-val">58%</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">{t('result.soilPh')}</div>
              <div className="preview-metric-val">5.8</div>
            </div>
          </div>

          {/* Recommended crops sample */}
          <div style={{ marginBottom: 12, fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={16} color="var(--green-primary)" />
            <span>{t('preview.topInsights')}</span>
          </div>

          <div className="preview-crops-grid">
            <div className="preview-crop-card highlight">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>{crop('grapes')}</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--green-primary)', fontWeight: 700 }}>{t('preview.rank', { n: 1 })}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800, color: 'var(--green-primary)' }}>31%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{t('common.confidence')}</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>{t('preview.profit')}: <strong>{level('Very High')}</strong></span>
                <span>{t('preview.water')}: <strong>{level('Medium')}</strong></span>
              </div>
            </div>

            <div className="preview-crop-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>{crop('maize')}</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t('preview.rank', { n: 2 })}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800 }}>16%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{t('common.confidence')}</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>{t('preview.profit')}: <strong>{level('Medium')}</strong></span>
                <span>{t('preview.water')}: <strong>{level('Medium')}</strong></span>
              </div>
            </div>

            <div className="preview-crop-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>{crop('muskmelon')}</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t('preview.rank', { n: 3 })}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800 }}>12%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{t('common.confidence')}</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>{t('preview.profit')}: <strong>{level('High')}</strong></span>
                <span>{t('preview.water')}: <strong>{level('Medium')}</strong></span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── 7. Final Call to Action ─────────────────────────────────────────── */}
      <section className="content-section" style={{ paddingTop: 0 }}>
        <div className="cta-banner-wrapper">
          <h2 className="cta-banner-title">{t('cta.title')}</h2>
          <p className="cta-banner-text">
            {t('cta.text')}
          </p>
          <button onClick={onStart} className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.05rem' }}>
            {t('nav.startAnalysis')} <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ── 8. Footer ───────────────────────────────────────────────────────── */}
      <footer className="site-footer">
        <div className="footer-container">
          <div className="footer-top">
            <div className="footer-brand-col">
              <div className="navbar-brand" style={{ marginBottom: 12 }}>
                <div className="brand-icon-wrapper">
                  <Sprout size={18} />
                </div>
                <span>CropSense AI</span>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {t('footer.tagline')}
              </p>
            </div>

            <div className="footer-links-col">
              <div>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-main)', letterSpacing: '0.08em', marginBottom: 16 }}>{t('footer.navigation')}</h4>
                <ul className="footer-nav-list">
                  <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="footer-nav-link">{t('nav.home')}</button></li>
                  <li><button onClick={() => scrollToSection('how-it-works')} className="footer-nav-link">{t('nav.howItWorks')}</button></li>
                  <li><button onClick={() => scrollToSection('features')} className="footer-nav-link">{t('nav.features')}</button></li>
                  <li><button onClick={() => scrollToSection('preview')} className="footer-nav-link">{t('nav.preview')}</button></li>
                  {onHistory && (
                    <li><button onClick={onHistory} className="footer-nav-link">{t('nav.queryHistory')}</button></li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-disclaimer-box">
            <strong>{t('footer.disclaimerLabel')}</strong> {t('footer.disclaimer')}
          </div>

          <div className="footer-bottom">
            <span>{t('footer.rights')}</span>
            <span>{t('footer.system')}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
