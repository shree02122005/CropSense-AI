import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import './HistoryPage.css'; // We'll create this CSS file
import { ArrowLeft } from 'lucide-react';

const HistoryPage = ({ onBack }) => {
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
      let errorMessage = 'Failed to load prediction history';
      
      if (err.code === 'NETWORK_ERROR' || err.message.includes('Network Error')) {
        errorMessage = 'Unable to connect to server. Please check if the backend is running.';
      } else if (err.response) {
        if (err.response.status === 404) {
          errorMessage = 'History service not available. Please try again later.';
        } else if (err.response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
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
    if (!window.confirm('Are you sure you want to delete this prediction?')) return;

    try {
      await axios.delete(`http://localhost:8000/history/${id}`);
      setHistory(history.filter(item => item.id !== id));
    } catch (err) {
      alert('Failed to delete prediction');
    }
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getCropName = (crop) => crop.name || crop.crop || 'Unknown';
  const getRankEmoji = (index) => (index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '•');

  if (loading) {
    return (
      <div className="history-page">
        <div className="loading">Loading prediction history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-page">
        <div className="error-container">
          <div className="error">{error}</div>
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
            Try Again
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
            Back
          </motion.button>
          <h1>Prediction History</h1>
        </div>
        {stats && (
          <div className="stats">
            <div className="stat-item">
              <span className="stat-label">Total Predictions:</span>
              <span className="stat-value">{stats.total_predictions ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Unique Locations:</span>
              <span className="stat-value">{stats.unique_locations ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Soil Types:</span>
              <span className="stat-value">{stats.unique_soil_types ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Avg Confidence:</span>
              <span className="stat-value">{((stats.avg_soil_confidence ?? 0) * 100).toFixed(1)}%</span>
            </div>
          </div>
        )}
      </div>

      <div className="filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by location..."
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
            <option value="">All Soil Types</option>
            {soilTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="history-list">
        {filteredHistory.length === 0 ? (
          <div className="no-history">
            {history.length === 0 ? 'No prediction history available yet.' : 'No predictions match your filters'}
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
                  <h3>{prediction.location ?? 'Unknown Location'}</h3>
                  <span className="timestamp">{formatDate(prediction.timestamp)}</span>
                </div>
                <button
                  className="delete-btn"
                  onClick={() => deletePrediction(prediction.id)}
                  title="Delete prediction"
                >
                  ×
                </button>
              </div>

              <div className="card-content">
                <div className="soil-info">
                  <div className="soil-type">
                    <span className="label">Soil Type:</span>
                    <span className="value">{prediction.soil_type ?? 'Unknown'}</span>
                  </div>
                  <div className="confidence">
                    <span className="label">Confidence:</span>
                    <span className="value">{((prediction.soil_confidence ?? 0) * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="conditions">
                  <div className="condition-item">
                    <span className="label">Temperature:</span>
                    <span className="value">{prediction.temperature ?? 'N/A'}°C</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">Humidity:</span>
                    <span className="value">{prediction.humidity ?? 'N/A'}%</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">Rainfall:</span>
                    <span className="value">{prediction.rainfall ?? 'N/A'}mm</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">pH:</span>
                    <span className="value">{prediction.ph ?? 'N/A'}</span>
                  </div>
                  <div className="condition-item">
                    <span className="label">Organic Carbon:</span>
                    <span className="value">{prediction.organic_carbon ?? 'N/A'}%</span>
                  </div>
                </div>

                <div className="coordinates">
                  <span className="coord">Lat: {(prediction.latitude ?? 0).toFixed(4)}</span>
                  <span className="coord">Lng: {(prediction.longitude ?? 0).toFixed(4)}</span>
                </div>

                <div className="crops-section">
                  <h4>Recommended Crops:</h4>
                  <div className="crops-list">
                    {((prediction.crops ?? []).slice().sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))).slice(0, 3).map((crop, index) => (
                      <div key={index} className="crop-item">
                        <span className="crop-name">{getRankEmoji(index)} {getCropName(crop)}</span>
                        <span className="crop-confidence">{((crop.confidence ?? 0) * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                    {(prediction.crops ?? []).length > 3 && (
                      <span className="more-crops">+{(prediction.crops ?? []).length - 3} more</span>
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