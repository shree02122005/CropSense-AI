import React from 'react';
import { motion } from 'framer-motion';

export default function HeroPage({ onStart, onHistory }) {
  return (
    <div className="hero-wrapper" style={{position:'relative',overflow:'hidden',background:'radial-gradient(ellipse 90% 70% at 50% -10%, #052e16 0%, #050a05 65%)'}}>
      {/* Grid bg */}
      <div className="hero-grid-bg" />
      {/* Glow blobs */}
      <div className="hero-glow hero-glow-top" />
      <div className="hero-glow hero-glow-bottom" />

      <motion.div
        initial={{opacity:0,y:40}}
        animate={{opacity:1,y:0}}
        transition={{duration:0.85,ease:[0.22,1,0.36,1]}}
        className="hero-inner"
        style={{zIndex:1}}
      >
        <motion.div
          initial={{opacity:0,scale:0.85}}
          animate={{opacity:1,scale:1}}
          transition={{delay:0.2}}
          className="hero-badge"
        >
          <span className="hero-badge-dot" />
          AI-Powered Precision Agriculture
        </motion.div>

        <h1 className="hero-heading">
          Smart Crop<br />
          <span className="hero-heading-highlight">Recommendations</span>
        </h1>

        <p className="hero-copy">
          Upload a soil photo, share your location — our hybrid CNN + ML model recommends the best crops for maximum yield and profit.
        </p>

        <div className="hero-actions">
          <motion.button
            whileHover={{scale:1.05,boxShadow:'0 0 48px rgba(74,222,128,0.45)'}}
            whileTap={{scale:0.97}}
            onClick={onStart}
            className="hero-primary-button"
          >
            Start Analysis →
          </motion.button>

          {onHistory && (
            <motion.button
              initial={{opacity:0}}
              animate={{opacity:1}}
              transition={{delay:0.4}}
              whileHover={{scale:1.05}}
              whileTap={{scale:0.97}}
              onClick={onHistory}
              className="hero-secondary-button"
            >
              View History
            </motion.button>
          )}
        </div>

        <motion.div
          initial={{opacity:0,y:16}}
          animate={{opacity:1,y:0}}
          transition={{delay:0.55}}
          className="hero-stats"
        >
          {[['23','Crop Types'],['88%','Accuracy'],['92%','Precision'],['92%','Recall'],['91%','F1 Score'],['Hybrid','CNN + RF']].map(([v,l]) => (
            <div key={l} className="hero-stat-card">
              <div className="hero-stat-value">{v}</div>
              <div className="hero-stat-label">{l}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
