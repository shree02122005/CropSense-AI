import React, { useState } from 'react';
import HeroPage     from './pages/HeroPage';
import OptionPage   from './pages/OptionPage';
import AnalysisPage from './pages/AnalysisPage';
import ResultPage   from './pages/ResultPage';
import ComparisonPage from './pages/CropComparisonDashboard';
import HistoryPage  from './pages/HistoryPage';

export default function App() {
  const [page, setPage]     = useState('hero');
  const [result, setResult] = useState(null);

  const go = pg => setPage(pg);

  return (
    <>
      {page === 'hero'     && <HeroPage     onStart={() => go('option')} onHistory={() => go('history')} />}
      {page === 'option'   && <OptionPage   onSelect={() => go('analysis')} onBack={() => go('hero')} />}
      {page === 'analysis' && <AnalysisPage onResult={r => { setResult(r); go('result'); }} onBack={() => go('option')} />}
      {page === 'result'   && <ResultPage   result={result} onReset={() => { setResult(null); go('hero'); }} onCompare={() => go('compare')} />}
      {page === 'compare'  && <ComparisonPage result={result} onBack={() => go('result')} />}
      {page === 'history'  && <HistoryPage  onBack={() => go('hero')} />}
    </>
  );
}
