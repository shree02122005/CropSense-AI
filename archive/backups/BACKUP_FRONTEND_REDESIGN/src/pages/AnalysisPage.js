import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { MapPin, Upload, Loader, CheckCircle, AlertCircle, ArrowLeft, Image as Img } from 'lucide-react';

const API = process.env.REACT_APP_API_URL?.replace(/\/+$/, '') || '';
const PREDICT_ENDPOINT = API ? `${API}/predict` : '/predict';

const STEPS = [
  { key:'gps',     label:'GPS Coordinates' },
  { key:'cnn',     label:'CNN Soil Classification' },
  { key:'weather', label:'Weather API Fetch' },
  { key:'soil',    label:'SoilGrids API Fetch' },
  { key:'ml',      label:'ML Crop Prediction' },
];

export default function AnalysisPage({ onResult, onBack }) {
  const [coords,   setCoords]   = useState(null);
  const [file,     setFile]     = useState(null);
  const [preview,  setPreview]  = useState(null);
  const [locSt,    setLocSt]    = useState('idle'); // idle|loading|done|error
  const [steps,    setSteps]    = useState({gps:'idle',cnn:'idle',weather:'idle',soil:'idle',ml:'idle'});
  const [running,  setRunning]  = useState(false);
  const [err,      setErr]      = useState('');
  const [drag,     setDrag]     = useState(false);
  const [locationName, setLocationName] = useState('');
  const [manualLocation, setManualLocation] = useState('');
  const [manualLocLoading, setManualLocLoading] = useState(false);
  const [showManual, setShowManual] = useState(false);
  const [imageErr, setImageErr] = useState('');
  const inputRef = useRef();

  const setStep = (k,v) => setSteps(s=>({...s,[k]:v}));

  // Reverse geocoding: convert lat/lon to location name
  const fetchLocationName = async (lat, lon) => {
    try {
      const response = await axios.get(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`,
        { timeout: 5000 }
      );
      const address = response.data?.address;
      if (address) {
        const parts = [
          address.village || address.suburb,
          address.city,
          address.state,
          address.country
        ].filter(Boolean);
        return parts.join(', ');
      }
      return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    } catch {
      return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    }
  };

  // Forward geocoding: convert location name to lat/lon
  const searchLocation = async (name) => {
    if (!name.trim()) {
      setImageErr('Please enter a location name');
      return;
    }
    setManualLocLoading(true);
    setImageErr('');
    try {
      const response = await axios.get(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(name)}&limit=1`,
        { timeout: 5000 }
      );
      if (!response.data || response.data.length === 0) {
        setImageErr('Location not found. Please try another name.');
        setManualLocLoading(false);
        return;
      }
      const result = response.data[0];
      const lat = parseFloat(result.lat);
      const lon = parseFloat(result.lon);
      const locName = result.display_name;
      setCoords({ lat, lon });
      setLocationName(locName);
      setLocSt('done');
      setShowManual(false);
      setManualLocation('');
    } catch (e) {
      setImageErr('Failed to search location. Please try again.');
    }
    setManualLocLoading(false);
  };

  const detectLoc = () => {
    setLocSt('loading'); setErr('');
    if (!navigator.geolocation) { setLocSt('error'); setErr('Geolocation not supported.'); return; }
    
    const timeoutId = setTimeout(() => {
      setLocSt('error'); 
      setErr('Location detection timed out. Please try manual input or check permissions.');
    }, 10000);
    
    navigator.geolocation.getCurrentPosition(
      async p => { 
        clearTimeout(timeoutId);
        const lat = p.coords.latitude;
        const lon = p.coords.longitude;
        setCoords({lat, lon});
        const locName = await fetchLocationName(lat, lon);
        setLocationName(locName);
        setLocSt('done');
        setShowManual(false);
      },
      (error) => { 
        clearTimeout(timeoutId);
        setLocSt('error'); 
        const msg = error.code === 1 ? 'Location permission denied. Please use manual input.' : 'Location detection failed. Please try manual input.';
        setErr(msg);
      }
    );
  };

  const handleFile = f => {
    if (!f) return;
    if (!['image/jpeg','image/png','image/jpg'].includes(f.type)) { setImageErr('Please upload a JPG or PNG image.'); return; }
    setFile(f); setPreview(URL.createObjectURL(f)); setImageErr('');
  };

  const runAnalysis = async () => {
    if (!coords) { setErr('Detect your location first.'); return; }
    if (!file)   { setErr('Upload a soil image first.'); return; }
    setRunning(true); setErr('');
    setSteps({gps:'idle',cnn:'idle',weather:'idle',soil:'idle',ml:'idle'});

    try {
      // Animate pipeline steps with small delays
      setStep('gps', 'done');
      setStep('cnn', 'active');
      await delay(500);
      setStep('cnn', 'done');
      setStep('weather', 'active');

      const fd = new FormData();
      fd.append('image', file);
      fd.append('latitude',  coords.lat);
      fd.append('longitude', coords.lon);

      // Fire API call — animate remaining steps while waiting
      const apiCall = axios.post(PREDICT_ENDPOINT, fd, {
        timeout:35000,
      });

      await delay(600);
      setStep('weather','done'); setStep('soil','active');
      await delay(500);
      setStep('soil','done'); setStep('ml','active');

      const res = await apiCall;
      setStep('ml','done');
      await delay(400);
      onResult(res.data);
    } catch(e) {
      const raw = e?.response?.data?.message ?? e?.response?.data?.detail ?? e?.message ?? 'Cannot connect to backend. Make sure FastAPI is running on port 8000.';
      const msg = typeof raw === 'string' ? raw : JSON.stringify(raw);
      // Check for soil image validation error safely
      const msgLower = msg.toLowerCase();
      if (msgLower.includes('soil')) {
        setImageErr(msg);
      } else {
        setErr(msg);
      }
      setSteps(s=>Object.fromEntries(Object.entries(s).map(([k,v])=>[k,v==='active'?'error':v])));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{minHeight:'100vh',background:'radial-gradient(ellipse 70% 50% at 50% 0%,#052e16,#050a05)',padding:'40px 24px',display:'flex',flexDirection:'column',alignItems:'center'}}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      <motion.button initial={{opacity:0}} animate={{opacity:1}} onClick={onBack} disabled={running}
        style={{alignSelf:'flex-start',display:'flex',alignItems:'center',gap:6,background:'rgba(255,255,255,0.05)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,padding:'7px 14px',cursor:running?'not-allowed':'pointer',color:'#86efac',fontSize:13,fontFamily:'var(--font-b)',marginBottom:36}}
      >
        <ArrowLeft size={13}/> Back
      </motion.button>

      <motion.h2 initial={{opacity:0,y:-16}} animate={{opacity:1,y:0}}
        style={{fontFamily:'var(--font-h)',fontSize:'1.9rem',fontWeight:800,letterSpacing:'-0.02em',marginBottom:6,textAlign:'center'}}
      >Prepare Your Analysis</motion.h2>
      <p style={{color:'#6b7280',marginBottom:40,textAlign:'center'}}>Detect location & upload a soil image to begin</p>

      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(290px,1fr))',gap:18,maxWidth:900,width:'100%'}}>

        {/* Location */}
        <Card delay={0.05}>
          <Row><MapPin size={18} color="#4ade80"/><SectionTitle>Live Location</SectionTitle></Row>
          {coords && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}}
              style={{background:'rgba(74,222,128,0.07)',border:'1px solid rgba(74,222,128,0.2)',borderRadius:10,padding:'10px 14px',marginBottom:14,fontSize:'0.82rem',color:'#86efac',fontFamily:'monospace',lineHeight:1.8}}
            >
              {locationName && <div style={{marginBottom:8,fontSize:'0.9rem',color:'#a3e635',fontFamily:'var(--font-b)'}}>{locationName}</div>}
              Lat: {coords.lat.toFixed(6)}<br/>Lon: {coords.lon.toFixed(6)}
            </motion.div>
          )}
          <GreenBtn onClick={detectLoc} disabled={locSt==='loading'} done={locSt==='done'} error={locSt==='error'}>
            {locSt==='loading'&&<Spin/>}{locSt==='done'&&<CheckCircle size={15}/>}{locSt==='idle'&&<MapPin size={15}/>}{locSt==='error'&&<AlertCircle size={15} color="#f87171"/>}
            {locSt==='loading'?'Detecting…':locSt==='done'?'Location Detected ✓':'Detect My Location'}
          </GreenBtn>
          <button 
            onClick={() => setShowManual(!showManual)}
            style={{width:'100%',marginTop:10,padding:'8px',borderRadius:8,border:'1px solid rgba(248,188,36,0.3)',background:'rgba(248,188,36,0.05)',color:'#fbbf24',fontSize:'0.8rem',fontWeight:600,cursor:'pointer',fontFamily:'var(--font-b)',transition:'all 0.2s'}}
          >
            {showManual ? 'Hide Search Location' : 'Search Location →'}
          </button>
          <AnimatePresence>
            {showManual && (
              <motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}} style={{marginTop:12,display:'flex',flexDirection:'column',gap:8}}>
                <input 
                  type="text" 
                  placeholder="Enter location name (e.g., Bengaluru, Delhi)" 
                  value={manualLocation} 
                  onChange={e => setManualLocation(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && searchLocation(manualLocation)}
                  style={{width:'100%',padding:'8px 12px',borderRadius:8,border:'1px solid rgba(255,255,255,0.1)',background:'rgba(255,255,255,0.03)',color:'#86efac',fontFamily:'var(--font-b)',fontSize:'0.85rem'}}
                />
                <button 
                  onClick={() => searchLocation(manualLocation)}
                  disabled={manualLocLoading}
                  style={{width:'100%',padding:'8px',borderRadius:8,border:'none',background:'linear-gradient(135deg,#4ade80,#16a34a)',color:'#050a05',fontWeight:600,cursor:manualLocLoading?'not-allowed':'pointer',fontFamily:'var(--font-b)',fontSize:'0.85rem',display:'flex',alignItems:'center',justifyContent:'center',gap:6}}
                >
                  {manualLocLoading && <Spin/>}
                  {manualLocLoading ? 'Searching…' : 'Search'}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>

        {/* Image upload */}
        <Card delay={0.1}>
          <Row><Img size={18} color="#4ade80"/><SectionTitle>Soil Image</SectionTitle></Row>
          <div
            onDrop={e=>{e.preventDefault();setDrag(false);handleFile(e.dataTransfer.files[0])}}
            onDragOver={e=>{e.preventDefault();setDrag(true)}}
            onDragLeave={()=>setDrag(false)}
            onClick={()=>inputRef.current?.click()}
            style={{border:`2px dashed ${drag?'#4ade80':'rgba(255,255,255,0.12)'}`,borderRadius:12,overflow:'hidden',minHeight:130,display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',transition:'border-color 0.2s',padding:preview?0:24,textAlign:'center'}}
          >
            {preview
              ? <img src={preview} alt="soil" style={{width:'100%',maxHeight:170,objectFit:'cover',display:'block'}}/>
              : <div><Upload size={26} color="#4ade80" style={{margin:'0 auto 10px'}}/><p style={{color:'#6b7280',fontSize:'0.82rem'}}>Drag & drop or click<br/><span style={{fontSize:'0.72rem'}}>JPG / PNG</span></p></div>
            }
          </div>
          <input ref={inputRef} type="file" accept="image/jpeg,image/png" style={{display:'none'}} onChange={e=>handleFile(e.target.files[0])}/>
          {file&&<p style={{marginTop:8,fontSize:'0.75rem',color:'#6b7280',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{file.name}</p>}
          {imageErr&&<p style={{marginTop:8,fontSize:'0.75rem',color:'#f87171'}}>{imageErr}</p>}
        </Card>

        {/* Pipeline */}
        <Card delay={0.15} style={{gridColumn:'1/-1'}}>
          <SectionTitle style={{marginBottom:16}}>AI Pipeline Status</SectionTitle>
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:'4px 24px'}}>
            {STEPS.map((s,i)=>{
              const st = steps[s.key];
              const c = st==='done'?'#4ade80':st==='active'?'#f0fdf4':st==='error'?'#f87171':'#374151';
              return (
                <div key={s.key} style={{display:'flex',alignItems:'center',gap:10,padding:'8px 0',borderBottom:'1px solid rgba(255,255,255,0.04)'}}>
                  <div style={{width:28,height:28,borderRadius:'50%',border:`2px solid ${c}`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,fontWeight:700,color:c,flexShrink:0,transition:'all 0.3s'}}>
                    {st==='done'?'✓':st==='error'?'✗':i+1}
                  </div>
                  <span style={{fontSize:'0.85rem',color:c,transition:'color 0.3s'}}>{s.label}</span>
                  {st==='active'&&<div style={{marginLeft:'auto',width:14,height:14,border:'2px solid #4ade80',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.8s linear infinite'}}/>}
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <AnimatePresence>
        {(err || imageErr) && (
          <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}
            style={{marginTop:18,maxWidth:900,width:'100%',background:'rgba(239,68,68,0.1)',border:'1px solid rgba(239,68,68,0.3)',borderRadius:12,padding:'12px 16px',color:'#fca5a5',fontSize:'0.85rem',display:'flex',gap:8,alignItems:'flex-start'}}
          >
            <AlertCircle size={15} style={{flexShrink:0,marginTop:1}}/> {err || imageErr}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{delay:0.25}}
        whileHover={!running?{scale:1.04,boxShadow:'0 0 44px rgba(74,222,128,0.38)'}:{}}
        whileTap={!running?{scale:0.97}:{}}
        onClick={runAnalysis} disabled={running}
        style={{marginTop:32,padding:'15px 56px',fontSize:'1rem',fontFamily:'var(--font-h)',fontWeight:700,letterSpacing:'0.04em',
          color: running?'#86efac':'#050a05',
          background: running?'rgba(74,222,128,0.12)':'linear-gradient(135deg,#4ade80,#16a34a)',
          border: running?'1px solid rgba(74,222,128,0.3)':'none',
          borderRadius:999, cursor: running?'not-allowed':'pointer',
          display:'flex', alignItems:'center', gap:10,
          boxShadow: running?'none':'0 4px 24px rgba(74,222,128,0.28)',
        }}
      >
        {running&&<Spin/>}
        {running ? 'Analysing your field…' : 'Run Hybrid AI Analysis →'}
      </motion.button>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const delay = ms => new Promise(r=>setTimeout(r,ms));
const Card = ({children,delay:d=0,style={}}) => (
  <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:d}}
    style={{background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:18,padding:24,...style}}
  >{children}</motion.div>
);
const Row = ({children}) => <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:16}}>{children}</div>;
const SectionTitle = ({children,style={}}) => <h3 style={{fontFamily:'var(--font-h)',fontWeight:700,fontSize:'1rem',...style}}>{children}</h3>;
const Spin = () => <div style={{width:16,height:16,border:'2px solid #4ade80',borderTopColor:'transparent',borderRadius:'50%',animation:'spin 0.8s linear infinite'}}/>;
const GreenBtn = ({children,onClick,disabled,done,error}) => (
  <button onClick={onClick} disabled={disabled}
    style={{marginTop:14,width:'100%',padding:'11px',borderRadius:10,border:'none',cursor:disabled?'not-allowed':'pointer',fontFamily:'var(--font-h)',fontWeight:600,fontSize:'0.88rem',display:'flex',alignItems:'center',justifyContent:'center',gap:8,transition:'all 0.2s',
      background: done?'rgba(74,222,128,0.13)':'linear-gradient(135deg,#4ade80,#16a34a)',
      color: done?'#4ade80':'#050a05',
    }}
  >{children}</button>
);
