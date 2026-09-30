import React from 'react';
import { motion } from 'framer-motion';
import { Thermometer, Droplets, CloudRain, MapPin, Leaf, RefreshCw, FlaskConical, Sprout, TrendingUp, Printer, Download } from 'lucide-react';
import { printReport, downloadPDF } from '../reportUtils';

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
  const conf    = Math.round(crop.confidence * 100);
  const pColor  = pc(crop.profit);
  return (
    <motion.div {...fu(delay)} whileHover={{y:-4,boxShadow:'0 12px 40px rgba(74,222,128,0.12)'}}
      style={{background:'rgba(255,255,255,0.04)',border:`1px solid ${rank===1?'rgba(74,222,128,0.35)':'rgba(255,255,255,0.08)'}`,borderRadius:18,padding:24,position:'relative',overflow:'hidden'}}
    >
      {rank===1&&<div style={{position:'absolute',top:0,right:0,background:'linear-gradient(135deg,#4ade80,#16a34a)',color:'#050a05',fontSize:10,fontWeight:800,letterSpacing:'0.07em',padding:'4px 12px',borderBottomLeftRadius:10,textTransform:'uppercase'}}>Top Pick</div>}

      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',marginBottom:16}}>
        <div>
          <h3 style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'1.3rem',marginBottom:6}}>{crop.name}</h3>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
            <Chip label={`${crop.profit} Profit`} color={pColor}/>
            <span style={{fontSize:11,color:'#6b7280'}}>{crop.season}</span>
          </div>
        </div>
        <div style={{textAlign:'right',flexShrink:0}}>
          <div style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'1.6rem',color:'#4ade80'}}>{conf}%</div>
          <div style={{fontSize:10,color:'#6b7280'}}>confidence</div>
        </div>
      </div>

      {/* Confidence bar */}
      <div style={{height:4,background:'rgba(255,255,255,0.07)',borderRadius:4,marginBottom:18,overflow:'hidden'}}>
        <motion.div initial={{width:0}} animate={{width:`${conf}%`}} transition={{delay:delay+0.3,duration:0.85,ease:'easeOut'}}
          style={{height:'100%',background:'linear-gradient(90deg,#16a34a,#4ade80)',borderRadius:4}}
        />
      </div>

      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'10px 16px'}}>
        {[['Yield',crop.yield],['Market',crop.price],['Season','🌱 '+crop.season],['Water',crop.water_need]].map(([k,v])=>(
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
  if (!result) return null;
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
              Analysis Complete
            </h1>
          </div>
          <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={() => printReport(result)}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(59, 130, 246, 0.1)',border:'1px solid rgba(59, 130, 246, 0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#3b82f6',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <Printer size={13}/> Print Report
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={() => downloadPDF(result)}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(139, 92, 246, 0.1)',border:'1px solid rgba(139, 92, 246, 0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#8b5cf6',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <Download size={13}/> Download PDF
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={onCompare}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(34,197,94,0.1)',border:'1px solid rgba(34,197,94,0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#22c55e',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <TrendingUp size={13}/> Compare Crops
            </motion.button>
            <motion.button whileHover={{scale:1.04}} whileTap={{scale:0.96}} onClick={onReset}
              style={{display:'flex',alignItems:'center',gap:7,background:'rgba(74,222,128,0.1)',border:'1px solid rgba(74,222,128,0.3)',borderRadius:10,padding:'9px 18px',cursor:'pointer',color:'#4ade80',fontSize:'0.85rem',fontFamily:'var(--font-h)',fontWeight:600}}
            >
              <RefreshCw size={13}/> New Analysis
            </motion.button>
          </div>
        </motion.div>

        {/* Soil banner */}
        <motion.div {...fu(0.08)}
          style={{background:'rgba(74,222,128,0.06)',border:'1px solid rgba(74,222,128,0.18)',borderRadius:14,padding:'14px 22px',marginBottom:20,display:'flex',alignItems:'center',gap:14,flexWrap:'wrap'}}
        >
          <Sprout size={18} color="#4ade80"/>
          <span style={{fontFamily:'var(--font-h)',fontWeight:700}}>Soil Type: {result.soil_type}</span>
          <span style={{fontSize:'0.82rem',color:'#6b7280'}}>CNN Confidence: {Math.round(result.soil_confidence*100)}%</span>
          <div style={{marginLeft:'auto',display:'flex',gap:8,flexWrap:'wrap'}}>
            {[['N',result.N,'#4ade80'],['P',result.P,'#a3e635'],['K',result.K,'#fbbf24']].map(([l,v,c])=>(
              <span key={l} style={{background:`${c}15`,border:`1px solid ${c}40`,borderRadius:8,padding:'4px 12px',fontSize:'0.78rem',color:c,fontFamily:'var(--font-h)',fontWeight:700}}>{l}: {v}</span>
            ))}
          </div>
        </motion.div>

        {/* Crop suitability factor cards */}
        <motion.div {...fu(0.08)} style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.06)',borderRadius:14,padding:18,marginBottom:28}}>
          <div style={{fontFamily:'var(--font-h)',fontWeight:800,fontSize:'0.95rem',color:'#f0fdf4',marginBottom:10}}>Crop Suitability Factors</div>

          <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:6}}>
            <WeatherCard delay={0.12} icon={<Leaf size={13}/>} label="Nitrogen (N)" value={result.N ?? 'N/A'} unit="" color="#4ade80"/>
            <WeatherCard delay={0.14} icon={<FlaskConical size={13}/>} label="Phosphorus (P)" value={result.P ?? 'N/A'} unit="" color="#a3e635"/>
            <WeatherCard delay={0.16} icon={<Leaf size={13}/>} label="Potassium (K)" value={result.K ?? 'N/A'} unit="" color="#fbbf24"/>
            <WeatherCard delay={0.18} icon={<Sprout size={13}/>} label="Soil Type" value={`${result.soil_type} (${SOIL_TYPE_MAP[(result.soil_type||'').toLowerCase()] ?? '?'})`} unit="" color="#16a34a"/>

            <WeatherCard delay={0.20} icon={<Thermometer size={13}/>} label="Temperature" value={result.temperature ?? 'N/A'} unit="°C" color="#f97316"/>
            <WeatherCard delay={0.22} icon={<Droplets size={13}/>} label="Humidity" value={result.humidity ?? 'N/A'} unit="%" color="#38bdf8"/>
            <WeatherCard delay={0.24} icon={<CloudRain size={13}/>} label="Rainfall" value={result.rainfall ?? 'N/A'} unit="mm" color="#818cf8"/>
            <WeatherCard delay={0.26} icon={<FlaskConical size={13}/>} label="Soil pH" value={result.ph ?? 'N/A'} unit="" color="#fb923c"/>
          </div>
        </motion.div>

        {/* Crop cards */}
        <motion.h2 {...fu(0.32)} style={{fontFamily:'var(--font-h)',fontSize:'1.3rem',fontWeight:800,marginBottom:18,letterSpacing:'-0.01em'}}>
          <TrendingUp size={18} style={{verticalAlign:'middle',marginRight:8,color:'#4ade80'}}/>
          Recommended Crops
        </motion.h2>

        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(270px,1fr))',gap:14,marginBottom:36}}>
          {result.crops.map((c,i)=><CropCard key={c.name} crop={c} rank={i+1} delay={0.38+i*0.08}/>)}
        </div>

        <motion.p {...fu(0.55)} style={{textAlign:'center',fontSize:'0.75rem',color:'#374151',lineHeight:1.6}}>
          AI-generated estimates only. Consult a local agronomist before major farming decisions.
        </motion.p>
      </div>
    </div>
  );
}
