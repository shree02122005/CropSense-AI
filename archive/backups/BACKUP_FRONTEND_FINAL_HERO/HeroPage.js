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

export default function HeroPage({ onStart, onHistory }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const stats = [
    { value: '23', label: 'Crop Types' },
    { value: '93.04%', label: 'Accuracy' },
    { value: '93.22%', label: 'Precision' },
    { value: '93.04%', label: 'Recall' },
    { value: '93.00%', label: 'F1 Score' },
    { value: 'CNN + RF', label: 'Model Pipeline' }
  ];

  const steps = [
    {
      num: '01',
      title: 'Upload Soil Photo',
      desc: 'Upload a clear, focused photograph of your surface soil sample.',
      detail: 'Supports standard JPG/PNG images of black, clay, loamy, red, or sandy soil.',
      icon: <UploadCloud size={22} />
    },
    {
      num: '02',
      title: 'Analyze with Soil CNN',
      desc: 'The MobileNetV2 deep learning classifier detects the soil class.',
      detail: 'Evaluates color gradients and morphological soil aggregate textures.',
      icon: <Cpu size={22} />
    },
    {
      num: '03',
      title: 'Combine Telemetry',
      desc: 'Location, live weather, SoilGrids pH, and NPK profiles are unified.',
      detail: 'Haversine distance matching against published ICAR and UAS university research.',
      icon: <Layers size={22} />
    },
    {
      num: '04',
      title: 'Predict Crops',
      desc: 'The 200-tree Random Forest predicts the top-ranked suitable crops.',
      detail: 'Generates probability rankings alongside market prices, profit ratings, and water needs.',
      icon: <TrendingUp size={22} />
    }
  ];

  const features = [
    {
      title: 'Soil Intelligence',
      desc: 'Convolutional neural network trained on authentic field photography to identify 5 core agronomic soil types with non-soil rejection filters.',
      icon: <Sparkles size={24} />
    },
    {
      title: 'Location Aware',
      desc: 'GPS coordinate matching references published agricultural university soil fertility surveys across Karnataka districts for genuine nutrient profiles.',
      icon: <MapPin size={24} />
    },
    {
      title: 'Environmental Telemetry',
      desc: 'Pulls real-time temperature, atmospheric humidity, and rainfall from OpenWeather combined with surface depth pH from ISRIC SoilGrids 2.0.',
      icon: <Thermometer size={24} />
    },
    {
      title: 'Actionable Crop Insights',
      desc: 'Machine learning ensemble outputs ranked candidate crops accompanied by indicative yield ranges, seasonal planting windows, and commercial market rates.',
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
            <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="nav-link">Home</button></li>
            <li><button onClick={() => scrollToSection('how-it-works')} className="nav-link">How It Works</button></li>
            <li><button onClick={() => scrollToSection('features')} className="nav-link">Features</button></li>
            <li><button onClick={() => scrollToSection('preview')} className="nav-link">Preview</button></li>
            {onHistory && (
              <li><button onClick={onHistory} className="nav-link">History</button></li>
            )}
          </ul>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button onClick={onStart} className="navbar-cta">
              Start Analysis <ArrowRight size={15} />
            </button>
            <button 
              className="mobile-menu-toggle" 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
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
              <button onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); setMobileMenuOpen(false); }} className="nav-link" style={{ textAlign: 'left' }}>Home</button>
              <button onClick={() => scrollToSection('how-it-works')} className="nav-link" style={{ textAlign: 'left' }}>How It Works</button>
              <button onClick={() => scrollToSection('features')} className="nav-link" style={{ textAlign: 'left' }}>Features</button>
              <button onClick={() => scrollToSection('preview')} className="nav-link" style={{ textAlign: 'left' }}>Preview</button>
              {onHistory && (
                <button onClick={() => { onHistory(); setMobileMenuOpen(false); }} className="nav-link" style={{ textAlign: 'left' }}>Query History</button>
              )}
              <button onClick={() => { onStart(); setMobileMenuOpen(false); }} className="btn-primary" style={{ marginTop: 12, justifyContent: 'center' }}>
                Start Analysis <ArrowRight size={16} />
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
            <span>AI-Powered Agriculture</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="hero-title"
          >
            Smarter Crops. <br />
            <span className="hero-title-highlight">Better Decisions.</span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="hero-description"
          >
            Analyze soil and environmental conditions to discover suitable crops for your location.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="hero-button-group"
          >
            <button onClick={onStart} className="btn-primary">
              Start Analysis <ArrowRight size={17} />
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="btn-secondary">
              Explore How It Works <ArrowDown size={16} />
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
            Holdout evaluation metrics on benchmark test split. Predictions on field data reflect live soil and atmospheric conditions.
          </p>
        </div>
      </section>

      {/* ── 4. How It Works Section ─────────────────────────────────────────── */}
      <section className="content-section" id="how-it-works">
        <div className="section-header">
          <span className="section-eyebrow">Methodology</span>
          <h2 className="section-headline">HOW CROPSENSE AI WORKS</h2>
          <p className="section-subtext">
            From soil image to crop insights in a simple analysis.
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
          <span className="section-eyebrow">System Capabilities</span>
          <h2 className="section-headline">Built for Smarter Crop Analysis</h2>
          <p className="section-subtext">
            Enterprise-grade artificial intelligence engineered for practical agronomic decision support.
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
          <span className="section-eyebrow">Telemetry Preview</span>
          <h2 className="section-headline">Comprehensive Output Structure</h2>
          <p className="section-subtext">
            Illustrative sample demonstrating the multi-dimensional environmental and agricultural report generated by CropSense AI.
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
                Field Analysis Sample (Belagavi District)
              </span>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: 2 }}>
                Location: 15.8497°N, 74.4977°E • Detected Soil: Clay / Medium Black
              </div>
            </div>
            <span className="preview-tag">Illustrative Preview</span>
          </div>

          {/* Environmental factors grid */}
          <div className="preview-metrics-grid">
            <div className="preview-metric-box">
              <div className="preview-metric-label">Soil Type</div>
              <div className="preview-metric-val" style={{ color: 'var(--green-primary)' }}>Clay</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Available N</div>
              <div className="preview-metric-val">249.7 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Available P</div>
              <div className="preview-metric-val">46.8 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Available K</div>
              <div className="preview-metric-val">180.4 <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>kg/ha</span></div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Temperature</div>
              <div className="preview-metric-val">29.5°C</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Humidity</div>
              <div className="preview-metric-val">58%</div>
            </div>
            <div className="preview-metric-box">
              <div className="preview-metric-label">Soil pH</div>
              <div className="preview-metric-val">5.8</div>
            </div>
          </div>

          {/* Recommended crops sample */}
          <div style={{ marginBottom: 12, fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={16} color="var(--green-primary)" />
            <span>Top Crop Insights (Example Output)</span>
          </div>

          <div className="preview-crops-grid">
            <div className="preview-crop-card highlight">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>Grapes</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--green-primary)', fontWeight: 700 }}>Rank #1 Recommendation</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800, color: 'var(--green-primary)' }}>31%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>confidence</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>Profit: <strong>Very High</strong></span>
                <span>Water: <strong>Medium</strong></span>
              </div>
            </div>

            <div className="preview-crop-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>Maize</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Rank #2 Recommendation</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800 }}>16%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>confidence</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>Profit: <strong>Medium</strong></span>
                <span>Water: <strong>Medium</strong></span>
              </div>
            </div>

            <div className="preview-crop-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div>
                  <h4 style={{ fontFamily: 'var(--font-h)', fontSize: '1.2rem', fontWeight: 800 }}>Muskmelon</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Rank #3 Recommendation</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontFamily: 'var(--font-h)', fontSize: '1.4rem', fontWeight: 800 }}>12%</span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>confidence</div>
                </div>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                <span>Profit: <strong>High</strong></span>
                <span>Water: <strong>Medium</strong></span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── 7. Final Call to Action ─────────────────────────────────────────── */}
      <section className="content-section" style={{ paddingTop: 0 }}>
        <div className="cta-banner-wrapper">
          <h2 className="cta-banner-title">Ready to analyze your soil?</h2>
          <p className="cta-banner-text">
            Start an analysis and explore crop insights based on your soil and environmental conditions.
          </p>
          <button onClick={onStart} className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.05rem' }}>
            Start Analysis <ArrowRight size={18} />
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
                AI-assisted crop analysis using soil and environmental data.
              </p>
            </div>

            <div className="footer-links-col">
              <div>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-main)', letterSpacing: '0.08em', marginBottom: 16 }}>Navigation</h4>
                <ul className="footer-nav-list">
                  <li><button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="footer-nav-link">Home</button></li>
                  <li><button onClick={() => scrollToSection('how-it-works')} className="footer-nav-link">How It Works</button></li>
                  <li><button onClick={() => scrollToSection('features')} className="footer-nav-link">Features</button></li>
                  <li><button onClick={() => scrollToSection('preview')} className="footer-nav-link">Preview</button></li>
                  {onHistory && (
                    <li><button onClick={onHistory} className="footer-nav-link">Query History</button></li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-disclaimer-box">
            <strong>Advisory Disclaimer:</strong> AI-generated estimates are intended for decision support and should be validated with local agricultural expertise and certified soil laboratory testing.
          </div>

          <div className="footer-bottom">
            <span>© 2026 CropSense AI — College Major Project. All rights reserved.</span>
            <span>Machine Learning & Computer Vision Decision Support System</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
