// CommonJS-compatible report generator for test scripts
// Mirrors the browser `frontend/src/reportUtils.js` functionality needed by tests

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString();
}

function generateReportHTML(prediction) {
  const safe = (v, def) => (v === undefined || v === null) ? def : v;

  const crops = (prediction.crops || []).map(crop => {
    const name = safe(crop.crop, 'Unknown');
    const conf = (safe(crop.confidence, 0) * 100).toFixed(1) + '%';
    return `<tr><td>${name}</td><td>${conf}</td></tr>`;
  }).join('');

  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Report</title></head><body>` +
    `<h1>CropSense AI Prediction Report</h1>` +
    `<div>Generated on ${formatDate(new Date())}</div>` +
    `<div>Location: ${safe(prediction.location, 'Unknown')}</div>` +
    `<div>Soil Type: ${safe(prediction.soil_type, 'Unknown')}</div>` +
    `<div>Confidence: ${(safe(prediction.soil_confidence, 0) * 100).toFixed(1)}%</div>` +
    `<div>Temperature: ${safe(prediction.temperature, 'N/A')}°C</div>` +
    `<div>Humidity: ${safe(prediction.humidity, 'N/A')}%</div>` +
    `<div>Rainfall: ${safe(prediction.rainfall, 'N/A')}mm</div>` +
    `<div>pH: ${safe(prediction.ph, 'N/A')}</div>` +
    `<div>Organic Carbon: ${safe(prediction.organic_carbon, 'N/A')}</div>` +
    `<div>Latitude: ${typeof prediction.latitude === 'number' ? prediction.latitude.toFixed(6) : '0.000000'}</div>` +
    `<div>Longitude: ${typeof prediction.longitude === 'number' ? prediction.longitude.toFixed(6) : '0.000000'}</div>` +
    `<h2>Recommended Crops</h2><table><thead><tr><th>Crop</th><th>Confidence</th></tr></thead><tbody>${crops}</tbody></table>` +
    `<div>Report ID: ${safe(prediction.id, 'Unknown')}</div>` +
    `</body></html>`;

  return html;
}

module.exports = { generateReportHTML };
