import React from 'react';
import { motion } from 'framer-motion';
import { Thermometer, Droplets, CloudRain, MapPin, Leaf, RefreshCw, FlaskConical, Sprout, TrendingUp, Printer, Download } from 'lucide-react';
import { printReport, downloadPDF } from '../reportUtils';
import { useI18n } from '../i18n/LanguageContext';

const fu = (d=0) => ({initial:{opacity:0,y:20},animate:{opacity:1,y:0},transition:{delay:d,duration:0.55,ease:[0.22,1,0.36,1]}});
const pc = p => p==='Very High'?'#4ade80':p==='High'?'#a3e635':p==='Medium'?'#fbbf24':'#9ca3af';

const SOIL_TYPE_MAP = { loamy: 2, red: 3, black: 0, clay: 1, sandy: 4 };

function Chip({ label, color }) {
  return <span style={{fontSize:10,fontWeight:700,letterSpacing:'0.07em',textTransform:'uppercase',color,background:`${color}18`,border:`1px solid ${color}40`,borderRadius:999,padding:'3px 10px'}}>{label}</span>;
}

function WeatherCard({ icon, label, value, unit, color, delay }) {
  return (
    <motion.div {...fu(delay)} style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:14,padding:'18px 20px'}}>
      <div style={{display:'flex',alignItems:'center',gap:6,color,fontSize:'0.7rem',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.08em',marginBottom:10}}>{icon} {label}</div>
      <div style={{fontFamily:'var(--font-h)',fontSize:'1.7rem',fontWeight:800,color:'#f0fdf4',lineHeight:1}}>
        {value}<span style={{fontSize:'0.85rem',color:'#6b7280',marginLeft:3,fontFamily:'var(--font-b)',fontWeight:400}}>{unit}</span>
      </div>
    </motion.div>
  );
}

function CropCard({ crop, rank, delay }) {
  const i18n       = useI18n();
  const { t }      = i18n;
  const conf       = Math.round(crop.confidence * 100);
  const pColor     = pc(crop.profit);
  const matchLabel = t(`match.${crop.confidence_level || (conf >= 50 ? 'strong' : conf >= 20 ? 'moderate' : 'low')}`);
  const matchColor = conf >= 50 ? '#4ade80' : conf >= 20 ? '#fbbf24' : '#fb923c';

  return (
    <motion.div {...fu(delay)} whileHover={{y:-4,boxShadow:'0 12px 40px rgba(74,222,128,0.12)'}}
      style={{background:'rgba(255,255,255,0.04)',border:`1px solid ${rank===1?'rgba(74,222,128,0.35)':'rgba(255,255,255,0.08)'}`,borderRadius:18,padding:24,position:'relative',overflow:'hidden'}}
    >
      {rank===1&&<div style={{position:'absolute',top:0,right:0,background:'linear-gradient(135deg,#4ade80,#16a34a)',color:'#050a05',fontSize:10,fontWeight:800,letterSpacing:'0.07em',padding:'4px 12px',borderBottomLeftRadius:10,textTransform:'uppercase'}}>{t('result.topPick')}</div>}

      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',marginBottom:16}}>
        <div>
          <h3 style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'1.3rem',marginBottom:6}}>{i18n.crop(crop.name)}</h3>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
            <Chip label={t('result.profitChip', { level: i18n.level(crop.profit) })} color={pColor}/>
            <Chip label={matchLabel} color={matchColor}/>
            <span style={{fontSize:11,color:'#6b7280'}}>{i18n.season(crop.season)}</span>
          </div>
        </div>
        <div style={{textAlign:'right',flexShrink:0}}>
          <div style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'1.6rem',color:matchColor}}>{conf}%</div>
          <div style={{fontSize:10,color:'#6b7280'}}>{t('common.confidence')}</div>
          <div style={{fontSize:10,fontWeight:700,color:matchColor,marginTop:2}}>{matchLabel}</div>
        </div>
      </div>

      {/* Confidence bar */}
      <div style={{height:4,background:'rgba(255,255,255,0.07)',borderRadius:4,marginBottom:18,overflow:'hidden'}}>
        <motion.div initial={{width:0}} animate={{width:`${conf}%`}} transition={{delay:delay+0.3,duration:0.85,ease:'easeOut'}}
          style={{height:'100%',background:conf>=50?'linear-gradient(90deg,#16a34a,#4ade80)':conf>=20?'linear-gradient(90deg,#d97706,#fbbf24)':'linear-gradient(90deg,#ea580c,#fb923c)',borderRadius:4}}
        />
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'10px 16px'}}>
        {[[t('result.yield'),crop.yield],[t('result.market'),crop.price],[t('result.season'),'🌱 '+i18n.season(crop.season)],[t('result.water'),i18n.level(crop.water_need)]].map(([k,v])=>(
          <div key={k}>
            <div style={{fontSize:10,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:3}}>{k}</div>
            <div style={{fontSize:'0.85rem',color:'#f0fdf4',fontWeight:500}}>{v}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export default function ResultPage({ result, onReset, onCompare }) {
  const i18n = useI18n();
  const { t, lang } = i18n;
  if (!result) return null;
  const soilName = i18n.soil(result.soil_type);
  const topConfidence = result.crops?.[0]?.confidence ?? 0;
  const isLowTopCrop  = topConfidence < 0.20 || result.is_low_confidence;

  return (
    <div style={{minHeight:'100vh',background:'radial-gradient(ellipse 60% 40% at 50% 0%,#052e16,#050a05)',padding:'40px 24px'}}>
      <div style={{maxWidth:1080,margin:'0 auto'}}>

        {/* Header */}
        <motion.div {...fu(0)} style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',flexWrap:'wrap',gap:16,marginBottom:36}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:6,color:'#4ade80',fontSize:'0.75rem',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.08em',marginBottom:8}}>
              <MapPin size={13}/> {result.location}
            </div>
            <h1 style={{fontFamily:'var(--font-h)',fontSize:'clamp(1.8rem,4vw,2.6rem)',fontWeight:800,letterSpacing:'-0.02em',lineHeight:1.1}}>
              {t('result.title')}
            </h1>
          </div>
          <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={() => printReport(result, i18n)}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(59, 130, 246, 0.1)',border:'1px solid rgba(59, 130, 246, 0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#3b82f6',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <Printer size={13}/> {t('result.print')}
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={() => downloadPDF(result, i18n)}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(139, 92, 246, 0.1)',border:'1px solid rgba(139, 92, 246, 0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#8b5cf6',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <Download size={13}/> {t('result.pdf')}
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={onCompare}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(34,197,94,0.1)',border:'1px solid rgba(34,197,94,0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#22c55e',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <TrendingUp size={13}/> {t('result.compare')}
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={onReset}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(74,222,128,0.1)',border:'1px solid rgba(74,222,128,0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#4ade80',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <RefreshCw size={13}/> {t('result.newAnalysis')}
            </motion.button>
          </div>
        </motion.div>

        {/* Soil banner */}
        <motion.div {...fu(0.08)}
          style={{background:'rgba(74,222,128,0.06)',border:'1px solid rgba(74,222,128,0.18)',borderRadius:14,padding:'14px 22px',marginBottom:20,display:'flex',alignItems:'center',gap:14,flexWrap:'wrap'}}
        >
          <Sprout size={18} color="#4ade80"/>
          <span style={{fontFamily:'var(--font-h)',fontWeight:700}}>{t('result.soilType')}: {soilName}</span>
          <span style={{fontSize:'0.82rem',color:'#6b7280'}}>{t('result.cnnConfidence')}: {Math.round(result.soil_confidence*100)}%</span>
          {result.npk_source_type && (
            <span style={{fontSize:'0.72rem',color:'#94a3b8',background:'rgba(255,255,255,0.06)',padding:'2px 8px',borderRadius:6,border:'1px solid rgba(255,255,255,0.1)'}}>
              NPK: {result.npk_district} ({result.npk_source_type.replace('_', ' ')})
            </span>
          )}
          <div style={{marginLeft:'auto',display:'flex',gap:8,flexWrap:'wrap'}}>
            {[['N',result.N,'#4ade80'],['P',result.P,'#a3e635'],['K',result.K,'#fbbf24']].map(([l,v,c])=>(
              <span key={l} style={{background:`${c}15`,border:`1px solid ${c}40`,borderRadius:8,padding:'4px 12px',fontSize:'0.78rem',color:c,fontFamily:'var(--font-h)',fontWeight:700}}>{l}: {v}</span>
            ))}
          </div>
        </motion.div>

        {/* Out-of-Distribution Warning Banner (shown above factors only when top crop >= 20%) */}
        {result.npk_out_of_training_range && !isLowTopCrop && (
          <motion.div {...fu(0.09)}
            style={{background:'rgba(245,158,11,0.07)',border:'1px solid rgba(245,158,11,0.28)',borderRadius:14,padding:'12px 18px',marginBottom:20,display:'flex',alignItems:'flex-start',gap:12}}
          >
            <div style={{background:'rgba(245,158,11,0.15)',color:'#f59e0b',borderRadius:8,padding:'4px 8px',fontSize:'0.72rem',fontWeight:800,textTransform:'uppercase',letterSpacing:'0.05em',flexShrink:0,marginTop:2}}>
              {t('result.oodNotice')}
            </div>
            <div style={{fontSize:'0.8rem',color:'#fde68a',lineHeight:1.5}}>
              <strong>{t('result.oodTitle')} ({Array.isArray(result.npk_ood_features) ? result.npk_ood_features.join(', ') : 'NPK'}):</strong> {(lang === 'en' && result.ood_warning) || t('result.oodDefault')}
            </div>
          </motion.div>
        )}

        {/* Crop suitability factor cards */}
        <motion.div {...fu(0.08)} style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.06)',borderRadius:14,padding:18,marginBottom:28}}>
          <div style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'0.95rem',color:'#f0fdf4',marginBottom:10}}>{t('result.factors')}</div>

          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:6}}>
            <WeatherCard delay={0.12} icon={<Leaf size={13}/>} label={t('result.nitrogen')} value={result.N ?? t('common.na')} unit="" color="#4ade80"/>
            <WeatherCard delay={0.14} icon={<FlaskConical size={13}/>} label={t('result.phosphorus')} value={result.P ?? t('common.na')} unit="" color="#a3e635"/>
            <WeatherCard delay={0.16} icon={<Leaf size={13}/>} label={t('result.potassium')} value={result.K ?? t('common.na')} unit="" color="#fbbf24"/>
            <WeatherCard delay={0.18} icon={<Sprout size={13}/>} label={t('result.soilType')} value={`${soilName} (${SOIL_TYPE_MAP[(result.soil_type||'').toLowerCase()] ?? '?'})`} unit="" color="#16a34a"/>

            <WeatherCard delay={0.20} icon={<Thermometer size={13}/>} label={t('result.temperature')} value={result.temperature ?? t('common.na')} unit="°C" color="#f97316"/>
            <WeatherCard delay={0.22} icon={<Droplets size={13}/>} label={t('result.humidity')} value={result.humidity ?? t('common.na')} unit="%" color="#38bdf8"/>
            <WeatherCard delay={0.24} icon={<CloudRain size={13}/>} label={t('result.rainfall')} value={result.rainfall ?? t('common.na')} unit="mm" color="#818cf8"/>
            <WeatherCard delay={0.26} icon={<FlaskConical size={13}/>} label={t('result.soilPh')} value={result.ph ?? t('common.na')} unit="" color="#fb923c"/>
          </div>
        </motion.div>

        {/* Crop cards */}
        <motion.h2 {...fu(0.32)} style={{fontFamily:'var(--font-h)',fontSize:'1.3rem',fontWeight:800,marginBottom:18,letterSpacing:'-0.01em'}}>
          <TrendingUp size={18} style={{verticalAlign:'middle',marginRight:8,color:'#4ade80'}}/>
          {t('result.recommended')}
        </motion.h2>

        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(270px,1fr))',gap:14,marginBottom:isLowTopCrop?14:36}}>
          {result.crops.map((c,i)=><CropCard key={c.name} crop={c} rank={i+1} delay={0.38+i*0.08}/>)}
        </div>

        {/* Low Confidence / OOD Notice under cards */}
        {isLowTopCrop && (
          <motion.div {...fu(0.48)}
            style={{background:'rgba(245,158,11,0.07)',border:'1px solid rgba(245,158,11,0.28)',borderRadius:12,padding:'11px 18px',marginBottom:28,display:'flex',alignItems:'center',gap:12}}
          >
            <div style={{background:'rgba(245,158,11,0.18)',color:'#f59e0b',borderRadius:6,padding:'3px 8px',fontSize:'0.72rem',fontWeight:800,textTransform:'uppercase',letterSpacing:'0.05em',flexShrink:0}}>
              {t('result.notice')}
            </div>
            <div style={{fontSize:'0.82rem',color:'#fde68a',lineHeight:1.5}}>
              {t('result.lowNotice')}
            </div>
          </motion.div>
        )}

        <motion.p {...fu(0.55)} style={{textAlign:'center',fontSize:'0.75rem',color:'#374151',lineHeight:1.6}}>
          {t('result.disclaimer')}
        </motion.p>
      </div>
    </div>
  );
}
