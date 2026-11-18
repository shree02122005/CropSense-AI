import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import './HistoryPage.css'; // We'll create this CSS file
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../i18n/LanguageContext';

const HistoryPage = ({ onBack }) => {
  const i18n = useI18n();
  const { t } = i18n;
  const [history, setHistory] = useState([]);
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [soilTypeFilter, setSoilTypeFilter] = useState('');
  const [soilTypes, setSoilTypes] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchHistory();
    fetchSoilTypes();
    fetchStats();
  }, []);

  useEffect(() => {
    filterHistory();
  }, [history, searchTerm, soilTypeFilter]);

  const fetchHistory = async () => {
    try {
      setError(null);
      const response = await axios.get('http://localhost:8000/history');
      setHistory(response.data.history);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load prediction history:', err);
      let errorMessage = 'history.loadFailed';
      
      if (err.code === 'NETWORK_ERROR' || err.message.includes('Network Error')) {
        errorMessage = 'history.noConnect';
      } else if (err.response) {
        if (err.response.status === 404) {
          errorMessage = 'history.notAvailable';
        } else if (err.response.status >= 500) {
          errorMessage = 'history.serverError';
        }
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  const fetchSoilTypes = async () => {
    try {
      const response = await axios.get('http://localhost:8000/history/soil-types');
      setSoilTypes(response.data.soil_types);
    } catch (err) {
      console.error('Failed to load soil types:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/history/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const filterHistory = () => {
    let filtered = history;

    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.location.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (soilTypeFilter) {
      filtered = filtered.filter(item =>
        item.soil_type.toLowerCase() === soilTypeFilter.toLowerCase()
      );
    }

    setFilteredHistory(filtered);
  };

  const deletePrediction = async (id) => {
    if (!window.confirm(t('history.confirmDelete'))) return;

    try {
      await axios.delete(`http://localhost:8000/history/${id}`);
      setHistory(history.filter(item => item.id !== id));
    } catch (err) {
      alert(t('history.deleteFailed'));
    }
  };

  const formatDate = (timestamp) => {
    return i18n.formatDate(timestamp);
  };

  const getCropName = (crop) => i18n.crop(crop.name || crop.crop) || t('common.unknown');
  const getRankEmoji = (index) => (index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '•');

  if (loading) {
    return (
      <div className="history-page">
        <div className="loading">{t('history.loading')}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-container">
          <div className="error">{t(error)}</div>
          <motion.button
            whileHover={{scale: 1.05}}
            whileTap={{scale: 0.95}}
            onClick={() => {
              setLoading(true);
              setError(null);
              fetchHistory();
              fetchSoilTypes();
              fetchStats();
            }}
            style={{
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '8px',
              padding: '8px 16px',
              cursor: 'pointer',
              color: '#3b82f6',
              fontSize: '0.9rem',
              marginTop: '16px'
            }}
          >
            {t('history.tryAgain')}
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="history-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="history-header">
        <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
          <motion.button
            whileHover={{scale: 1.05}}
            whileTap={{scale: 0.95}}
            onClick={onBack}
            style={{
              background: 'rgba(74, 222, 128, 0.1)',
              border: '1px solid rgba(74, 222, 128, 0.3)',
              borderRadius: '8px',
              padding: '8px 12px',
              cursor: 'pointer',
              color: '#4ade80',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.9rem'
            }}
          >
            <ArrowLeft size={16} />
            {t('common.back')}
          </motion.button>
          <h1>{t('history.title')}</h1>
        </div>
        {stats && (
          <div className="stats">
            <div className="stat-item">
              <span className="stat-label">{t('history.total')}</span>
              <span className="stat-value">{stats.total_predictions ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t('history.uniqueLoc')}</span>
              <span className="stat-value">{stats.unique_locations ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t('history.soilTypes')}</span>
              <span className="stat-value">{stats.unique_soil_types ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">{t('history.avgConf')}</span>
              <span className="stat-value">{((stats.avg_soil_confidence ?? 0) * 100).toFixed(1)}%</span>
            </div>
          </div>
        )}
      </div>

      <div className="filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder={t('history.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <select
            value={soilTypeFilter}
            onChange={(e) => setSoilTypeFilter(e.target.value)}
            className="soil-type-select"
          >
            <option value="">{t('history.allSoils')}</option>
            {soilTypes.map(type => (
              <option key={type} value={type}>{i18n.soil(type)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="history-list">
        {filteredHistory.length === 0 ? (
          <div className="no-history">
            {history.length === 0 ? t('history.none') : t('history.noMatch')}
          </div>
        ) : (
          filteredHistory.map((prediction) => (
            <motion.div
              key={prediction.id}
              className="history-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="card-header">
                <div className="location-time">
                  <h3>{prediction.location ?? t('history.unknownLocation')}</h3>
                  <span className="timestamp">{formatDate(prediction.timestamp)}</span>
                </div>
                <button
                  className="delete-btn"
                  onClick={() => deletePrediction(prediction.id)}
                  title={t('history.deleteTitle')}
                >
                  ×
                </button>
              </div>

              <div className="card-content">
                <div className="soil-info">
                  <div className="soil-type">
                    <span className="label">{t('history.soilType')}</span>
                    <span className="value">{prediction.soil_type ? i18n.soil(prediction.soil_type) : t('common.unknown')}</span>
                  </div>
                  <div className="confidence">
                    <span className="label">{t('history.confidence')}</span>
                    <span className="value">{((prediction.soil_confidence ?? 0) * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="conditions">
                  <div className="condition-item">
                    <span className="label">{t('history.temperature')}</span>
                    <span className="value">{prediction.temperature ?? t('common.na')}°C</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">{t('history.humidity')}</span>
                    <span className="value">{prediction.humidity ?? t('common.na')}%</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">{t('history.rainfall')}</span>
                    <span className="value">{prediction.rainfall ?? t('common.na')}mm</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">{t('history.ph')}</span>
                    <span className="value">{prediction.ph ?? t('common.na')}</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">{t('history.oc')}</span>
                    <span className="value">{prediction.organic_carbon ?? t('common.na')}%</span>
                  </div>
                </div>

                <div className="coordinates">
                  <span className="coord">{t('history.lat')}: {(prediction.latitude ?? 0).toFixed(4)}</span>
                  <span className="coord">{t('history.lng')}: {(prediction.longitude ?? 0).toFixed(4)}</span>
                </div>

                <div className="crops-section">
                  <h4>{t('history.recCrops')}</h4>
                  <div className="crops-list">
                    {((prediction.crops ?? []).slice().sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))).slice(0, 3).map((crop, index) => (
                      <div key={index} className="crop-item">
                        <span className="crop-name">{getRankEmoji(index)} {getCropName(crop)}</span>
                        <span className="crop-confidence">{((crop.confidence ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                    {(prediction.crops ?? []).length > 3 && (
                      <span className="more-crops">{t('history.more', { n: (prediction.crops ?? []).length - 3 })}</span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default HistoryPage;