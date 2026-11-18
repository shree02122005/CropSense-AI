import React from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Sparkles, TrendingUp } from 'lucide-react';
import { useI18n } from '../i18n/LanguageContext';

const fu = (d = 0) => ({initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { delay: d, duration: 0.55, ease: [0.22, 1, 0.36, 1] }});

function ConfidenceBar({ value }) {
  const width = `${Math.round(value * 100)}%`;
  return (
    <div style={{background:'rgba(255,255,255,0.08)',borderRadius:999,height:10,overflow:'hidden',marginTop:6}}>
      <motion.div initial={{width:0}} animate={{width}} transition={{duration:0.8,ease:'easeOut'}}
        style={{height:'100%',background:'linear-gradient(90deg,#4ade80,#16a34a)',borderRadius:999}}
      />
    </div>
  );
}

function ComparisonCard({ crop, rank, isBest }) {
  const i18n       = useI18n();
  const { t }      = i18n;
  const conf       = Math.round(crop.confidence * 100);
  const matchLabel = t(`match.${crop.confidence_level || (conf >= 50 ? 'strong' : conf >= 20 ? 'moderate' : 'low')}`);
  const matchColor = conf >= 50 ? '#4ade80' : conf >= 20 ? '#fbbf24' : '#fb923c';

  return (
    <motion.div {...fu(rank * 0.05)} whileHover={{y:-6,boxShadow:'0 18px 40px rgba(0,255,100,0.12)'}}
      style={{
        background:'rgba(255,255,255,0.04)',
        border:isBest ? '1px solid rgba(74,222,128,0.75)' : '1px solid rgba(255,255,255,0.08)',
        boxShadow:isBest ? '0 0 0 2px rgba(74,222,128,0.14)' : '0 0 0 0 transparent',
        borderRadius:20,
        padding:24,
        position:'relative',
        overflow:'hidden'
      }}
    >
      {isBest && (
        <div style={{position:'absolute',top:16,right:16,background:'rgba(34,197,94,0.13)',color:'#ecfccb',padding:'6px 10px',borderRadius:999,fontSize:10,fontWeight:700,letterSpacing:'0.04em',textTransform:'uppercase'}}>{t('compare.bestMatch')}</div>
      )}
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:18}}>
        <div>
          <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:8}}>
            <span style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.12em'}}>{t('compare.rank', { n: rank })}</span>
            <span style={{fontSize:10,fontWeight:700,color:matchColor}}>• {matchLabel}</span>
          </div>
          <h3 style={{fontFamily:'var(--font-h)',fontSize:'1.45rem',fontWeight:800,color:'#f0fdf4',margin:0}}>{i18n.crop(crop.name)}</h3>
        </div>
        <div style={{textAlign:'right'}}>
          <div style={{fontSize:'1.7rem',fontWeight:800,color:matchColor}}>{conf}%</div>
          <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.08em'}}>{t('common.confidenceCap')}</div>
          <div style={{fontSize:11,fontWeight:700,color:matchColor,marginTop:2}}>{matchLabel}</div>
        </div>
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:22}}>
        {[
          [t('compare.profit'), i18n.level(crop.profit)],
          [t('result.yield'), crop.yield],
          [t('result.market'), crop.price],
          [t('result.water'), i18n.level(crop.water_need)],
          [t('result.season'), i18n.season(crop.season)]
        ].map(([label, value]) => (
          <div key={label} style={{background:'rgba(255,255,255,0.03)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:14,padding:14}}>
            <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:6}}>{label}</div>
            <div style={{fontSize:'0.95rem',color:'#f0fdf4',fontWeight:700}}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{display:'flex',alignItems:'center',gap:8,color:'#a7f3d0',fontSize:'0.82rem',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.08em'}}>
        <TrendingUp size={14}/> {t('compare.profitOutlook', { level: i18n.level(crop.profit) })}
      </div>
    </motion.div>
  );
}

function ComparisonRow({ label, values }) {
  return (
    <div style={{display:'grid',gridTemplateColumns:'1.5fr repeat(3,1fr)',gap:12,alignItems:'center',padding:'14px 0',borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
      <div style={{color:'#9ca3af',fontSize:'0.8rem',textTransform:'uppercase',letterSpacing:'0.08em'}}>{label}</div>
      {values.map((value, index)=>(
        <div key={index} style={{color:'#f0fdf4',fontWeight:600,textAlign:'center'}}>{value}</div>
      ))}
    </div>
  );
}

export default function CropComparisonDashboard({ result, onBack }) {
  const i18n = useI18n();
  const { t } = i18n;
  if (!result || !Array.isArray(result.crops)) return null;

  const crops = [...result.crops].sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  const bestCrop = crops[0];

  return (
    <div style={{minHeight:'100vh',background:'radial-gradient(ellipse 65% 45% at 50% 0%,#052e16,#050a05)',padding:'36px 18px'}}>
      <div style={{maxWidth:1180,margin:'0 auto'}}>
        <motion.div {...fu(0)} style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:16,marginBottom:34}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:10}}>
              <div style={{width:10,height:10,borderRadius:'50%',background:'#4ade80'}} />
              <span style={{color:'#4ade80',fontSize:'0.8rem',fontWeight:700,letterSpacing:'0.12em',textTransform:'uppercase'}}>{t('compare.title')}</span>
            </div>
            <h1 style={{fontFamily:'var(--font-h)',fontSize:'clamp(2rem,3vw,3rem)',fontWeight:800,color:'#f8fafc',margin:0,lineHeight:1.05}}>{t('compare.title')}</h1>
            <p style={{marginTop:12,color:'#cbd5e1',maxWidth:640,fontSize:'0.98rem',lineHeight:1.75}}>{t('compare.sub')}</p>
          </div>
          <motion.button whileHover={{scale:1.03}} whileTap={{scale:0.97}} onClick={onBack}
            style={{display:'flex',alignItems:'center',gap:8,background:'rgba(15,23,42,0.9)',border:'1px solid rgba(74,222,128,0.18)',borderRadius:12,padding:'12px 18px',color:'#f8fafc',fontSize:'0.9rem',fontWeight:700,cursor:'pointer'}}
          >
            <ChevronLeft size={16}/> {t('compare.backToResults')}
          </motion.button>
        </motion.div>

        <motion.div {...fu(0.08)} style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:18,marginBottom:32}}>
          {crops.map((crop,index) => (
            <ComparisonCard key={crop.name} crop={crop} rank={index+1} isBest={index===0} />
          ))}
        </motion.div>

        <motion.div {...fu(0.16)} style={{display:'grid',gridTemplateColumns:'1.2fr 0.8fr',gap:18,marginBottom:32}}>
          <div style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:20,padding:24}}>
            <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:18}}>
              <div style={{width:12,height:12,borderRadius:'50%',background:'#4ade80'}} />
              <span style={{fontSize:'0.85rem',fontWeight:700,color:'#f8fafc',letterSpacing:'0.08em',textTransform:'uppercase'}}>{t('compare.params')}</span>
            </div>
            <div style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.06)',borderRadius:20,overflow:'hidden'}}>
              <div style={{display:'grid',gridTemplateColumns:'1.5fr repeat(3,1fr)',gap:12,padding:'14px 18px',borderBottom:'1px solid rgba(255,255,255,0.08)',fontSize:'0.72rem',textTransform:'uppercase',letterSpacing:'0.12em',color:'#9ca3af'}}>
                <div>{t('compare.parameter')}</div>
                {crops.map(c => <div key={c.name} style={{textAlign:'center'}}>{i18n.crop(c.name)}</div>)}
              </div>
              <ComparisonRow label={t('compare.confScore')} values={crops.map(c => `${Math.round(c.confidence*100)}%`)} />
              <div style={{padding:'0 18px 14px'}}>
                <div style={{color:'#9ca3af',fontSize:'0.75rem',marginBottom:10}}>{t('compare.confProgress')}</div>
                <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:12}}>
                  {crops.map(c => <div key={c.name}>
                    <div style={{color:'#f0fdf4',fontSize:'0.78rem',marginBottom:8,textAlign:'center'}}>{Math.round(c.confidence*100)}%</div>
                    <ConfidenceBar value={c.confidence} />
                  </div>)}
                </div>
              </div>
              <ComparisonRow label={t('result.yield')} values={crops.map(c => c.yield)} />
              <ComparisonRow label={t('compare.marketPrice')} values={crops.map(c => c.price)} />
              <ComparisonRow label={t('compare.waterReq')} values={crops.map(c => i18n.level(c.water_need))} />
              <ComparisonRow label={t('compare.profitLevel')} values={crops.map(c => i18n.level(c.profit))} />
            </div>
          </div>

          <div style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:20,padding:24,display:'flex',flexDirection:'column',gap:18}}>
            <div style={{display:'flex',alignItems:'center',gap:10}}>
              <div style={{width:12,height:12,borderRadius:'50%',background:'#4ade80'}} />
              <span style={{fontSize:'0.85rem',fontWeight:700,color:'#f8fafc',letterSpacing:'0.08em',textTransform:'uppercase'}}>{t('compare.overall')}</span>
            </div>
            <div style={{display:'grid',gap:12}}>
              {crops.map((crop,index) => (
                <div key={crop.name} style={{background:'rgba(255,255,255,0.03)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:16,padding:14,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                  <div>
                    <div style={{fontSize:'0.9rem',fontWeight:700,color:'#f0fdf4'}}>{index===0?'🥇':index===1?'🥈':'🥉'} {t('compare.rank', { n: index+1 })}</div>
                    <div style={{color:'#9ca3af',fontSize:'0.78rem'}}>{i18n.crop(crop.name)}</div>
                  </div>
                  <div style={{fontSize:'0.85rem',fontWeight:700,color:'#4ade80'}}>{Math.round(crop.confidence*100)}%</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div {...fu(0.2)} style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:20,padding:24}}>
          <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:16}}>
            <Sparkles size={18} color='#4ade80' />
            <span style={{fontSize:'0.85rem',fontWeight:700,color:'#f8fafc',letterSpacing:'0.08em',textTransform:'uppercase'}}>{t('compare.final')}</span>
          </div>
          <h2 style={{fontFamily:'var(--font-h)',fontSize:'1.65rem',fontWeight:800,color:'#f0fdf4',margin:'0 0 10px'}}>{t('compare.recommendedCrop', { name: i18n.crop(bestCrop.name) })}</h2>
          <p style={{color:'#cbd5e1',lineHeight:1.75,marginBottom:20}}>{t('compare.finalText')}</p>
          <ul style={{display:'grid',gap:10,paddingLeft:20,color:'#f8fafc'}}>
            <li style={{position:'relative',marginBottom:4}}>{t('compare.b1')}</li>
            <li style={{position:'relative',marginBottom:4}}>{t('compare.b2')}</li>
            <li style={{position:'relative',marginBottom:4}}>{t('compare.b3')}</li>
            <li style={{position:'relative',marginBottom:4}}>{t('compare.b4')}</li>
          </ul>
        </motion.div>
      </div>
    </div>
  );
}
