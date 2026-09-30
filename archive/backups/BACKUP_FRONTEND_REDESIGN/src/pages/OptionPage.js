import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Settings, ArrowLeft } from 'lucide-react';

export default function OptionPage({ onSelect, onBack }) {
  const cards = [
    { icon:<MapPin size={26}/>, title:'Auto Location', desc:'Browser GPS detects your coordinates. Real-time weather + soil data fetched automatically.', tag:'Recommended', tc:'#4ade80' },
    { icon:<Settings size={26}/>, title:'Manual Input',  desc:'Enter latitude/longitude manually. Great for controlled testing or offline areas.', tag:'Advanced',     tc:'#fbbf24' },
  ];
  return (
    <div style={{minHeight:'100vh',background:'radial-gradient(ellipse 70% 50% at 50% 0%,#052e16,#050a05)',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:'60px 24px'}}>
      <motion.button initial={{opacity:0}} animate={{opacity:1}} onClick={onBack}
        style={{position:'fixed',top:20,left:20,display:'flex',alignItems:'center',gap:6,background:'rgba(255,255,255,0.05)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,padding:'7px 14px',cursor:'pointer',color:'#86efac',fontSize:13,fontFamily:'var(--font-b)'}}
      >
        <ArrowLeft size={13}/> Back
      </motion.button>

      <motion.div initial={{opacity:0,y:-20}} animate={{opacity:1,y:0}} style={{textAlign:'center',marginBottom:52}}>
        <h2 style={{fontFamily:'var(--font-h)',fontSize:'2.2rem',fontWeight:800,letterSpacing:'-0.02em',marginBottom:10}}>Choose Input Mode</h2>
        <p style={{color:'#6b7280',fontSize:'1rem'}}>How should we get your location data?</p>
      </motion.div>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(270px,1fr))',gap:18,maxWidth:640,width:'100%'}}>
        {cards.map((c,i)=>(
          <motion.div key={i} initial={{opacity:0,y:24}} animate={{opacity:1,y:0}} transition={{delay:i*0.1}}
            whileHover={{y:-5,boxShadow:'0 12px 40px rgba(74,222,128,0.13)'}}
            onClick={onSelect}
            style={{cursor:'pointer',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:18,padding:'28px 24px',transition:'border-color 0.2s'}}
            onMouseEnter={e=>e.currentTarget.style.borderColor='rgba(74,222,128,0.4)'}
            onMouseLeave={e=>e.currentTarget.style.borderColor='rgba(255,255,255,0.08)'}
          >
            <div style={{display:'flex',justifyContent:'space-between',marginBottom:18}}>
              <div style={{width:48,height:48,borderRadius:12,background:'rgba(74,222,128,0.1)',display:'flex',alignItems:'center',justifyContent:'center',color:'#4ade80'}}>{c.icon}</div>
              <span style={{fontSize:10,fontWeight:700,letterSpacing:'0.08em',textTransform:'uppercase',color:c.tc,background:`${c.tc}18`,border:`1px solid ${c.tc}40`,borderRadius:999,padding:'3px 10px',alignSelf:'flex-start'}}>{c.tag}</span>
            </div>
            <h3 style={{fontFamily:'var(--font-h)',fontWeight:700,fontSize:'1.2rem',marginBottom:8}}>{c.title}</h3>
            <p style={{color:'#6b7280',fontSize:'0.875rem',lineHeight:1.6}}>{c.desc}</p>
            <div style={{marginTop:20,color:'#4ade80',fontSize:'0.85rem',fontWeight:600}}>Select →</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
