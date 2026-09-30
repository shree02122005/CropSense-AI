/**
 * reportUtils.js — Utilities for generating and exporting prediction reports
 */

/**
 * Generate HTML content for a prediction report
 */
export const generateReportHTML = (prediction) => {
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const cropsHTML = (prediction.crops ?? []).map(crop =>
    `<tr>
      <td>${crop.crop ?? 'Unknown'}</td>
      <td>${((crop.confidence ?? 0) * 100).toFixed(1)}%</td>
    </tr>`
  ).join('');

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>CropSense AI Prediction Report</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        .header {
          text-align: center;
          border-bottom: 2px solid #4ade80;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        .header h1 {
          color: #4ade80;
          margin: 0;
          font-size: 2rem;
        }
        .timestamp {
          color: #666;
          font-size: 0.9rem;
        }
        .section {
          margin-bottom: 25px;
        }
        .section h2 {
          color: #4ade80;
          border-bottom: 1px solid #ddd;
          padding-bottom: 5px;
          font-size: 1.3rem;
        }
        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
        }
        .info-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #eee;
        }
        .info-item:last-child {
          border-bottom: none;
        }
        .label {
          font-weight: bold;
          color: #555;
        }
        .value {
          color: #333;
        }
        .crops-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 15px;
        }
        .crops-table th, .crops-table td {
          border: 1px solid #ddd;
          padding: 8px 12px;
          text-align: left;
        }
        .crops-table th {
          background-color: #f8f9fa;
          font-weight: bold;
          color: #4ade80;
        }
        .coordinates {
          background-color: #f8f9fa;
          padding: 15px;
          border-radius: 5px;
          margin-top: 15px;
        }
        .footer {
          text-align: center;
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #ddd;
          color: #666;
          font-size: 0.9rem;
        }
        @media print {
          body { margin: 0; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>CropSense AI Prediction Report</h1>
        <div class="timestamp">Generated on ${formatDate(new Date())}</div>
      </div>

      <div class="section">
        <h2>Location & Soil Information</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">Location:</span>
            <span class="value">${prediction.location ?? 'Unknown'}</span>
          </div>
          <div class="info-item">
            <span class="label">Soil Type:</span>
            <span class="value">${prediction.soil_type ?? 'Unknown'}</span>
          </div>
          <div class="info-item">
            <span class="label">Confidence:</span>
            <span class="value">${((prediction.soil_confidence ?? 0) * 100).toFixed(1)}%</span>
          </div>
          <div class="info-item">
            <span class="label">Image:</span>
            <span class="value">${prediction.image_name ?? 'Unknown'}</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>Environmental Conditions</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">Temperature:</span>
            <span class="value">${prediction.temperature ?? 'N/A'}°C</span>
          </div>
          <div class="info-item">
            <span class="label">Humidity:</span>
            <span class="value">${prediction.humidity ?? 'N/A'}%</span>
          </div>
          <div class="info-item">
            <span class="label">Rainfall:</span>
            <span class="value">${prediction.rainfall ?? 'N/A'}mm</span>
          </div>
          <div class="info-item">
            <span class="label">pH Level:</span>
            <span class="value">${prediction.ph ?? 'N/A'}</span>
          </div>
          <div class="info-item">
            <span class="label">Organic Carbon:</span>
            <span class="value">${prediction.organic_carbon ?? 'N/A'}%</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>Soil Macronutrients (N, P, K)</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">Available Nitrogen (N):</span>
            <span class="value">${prediction.N ?? 'N/A'} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">Available Phosphorus (P):</span>
            <span class="value">${prediction.P ?? 'N/A'} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">Available Potassium (K):</span>
            <span class="value">${prediction.K ?? 'N/A'} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">NPK Source:</span>
            <span class="value">${prediction.npk_district ?? 'Karnataka Baseline'} (${(prediction.npk_source_type ?? 'published').replace('_', ' ')})</span>
          </div>
        </div>
        ${prediction.npk_out_of_training_range ? `
        <div style="margin-top: 10px; padding: 8px 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; font-size: 11px; color: #92400e;">
          <strong>Out-of-Distribution Notice:</strong> ${prediction.ood_warning || 'Soil nutrient inputs exceed empirical training limits; model outputs represent algorithmic extrapolation.'}
        </div>` : ''}
      </div>

      <div class="coordinates">
        <strong>GPS Coordinates:</strong><br>
        Latitude: ${(prediction.latitude ?? 0).toFixed(6)}, Longitude: ${(prediction.longitude ?? 0).toFixed(6)}
      </div>

      <div class="section">
        <h2>Recommended Crops</h2>
        <table class="crops-table">
          <thead>
            <tr>
              <th>Crop</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            ${cropsHTML}
          </tbody>
        </table>
      </div>

      <div class="footer">
        <p>This report was generated by CropSense AI - Advanced Soil Analysis & Crop Recommendation System</p>
        <p>Report ID: ${prediction.id ?? 'Unknown'}</p>
      </div>
    </body>
    </html>
  `;
};

/**
 * Print the prediction report
 */
export const printReport = (prediction) => {
  const printWindow = window.open('', '_blank');
  const htmlContent = generateReportHTML(prediction);

  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.focus();

  // Wait for content to load then print
  printWindow.onload = () => {
    printWindow.print();
    printWindow.close();
  };
};

/**
 * Download the prediction report as PDF
 * Note: This uses the browser's print-to-PDF functionality
 */
export const downloadPDF = (prediction) => {
  const printWindow = window.open('', '_blank');
  const htmlContent = generateReportHTML(prediction);

  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.focus();

  // Wait for content to load then trigger save as PDF
  printWindow.onload = () => {
    // Use browser's print dialog with save as PDF option
    printWindow.print();
  };
};

/**
 * Generate and download a summary report for multiple predictions
 */
export const generateSummaryReport = (predictions, stats) => {
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const predictionsHTML = predictions.map(pred =>
    `<tr>
      <td>${formatDate(pred.timestamp)}</td>
      <td>${pred.location ?? 'Unknown'}</td>
      <td>${pred.soil_type ?? 'Unknown'}</td>
      <td>${((pred.soil_confidence ?? 0) * 100).toFixed(1)}%</td>
      <td>${(pred.crops ?? []).length}</td>
    </tr>`
  ).join('');

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>CropSense AI Summary Report</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 1000px;
          margin: 0 auto;
          padding: 20px;
        }
        .header {
          text-align: center;
          border-bottom: 2px solid #4ade80;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        .header h1 {
          color: #4ade80;
          margin: 0;
          font-size: 2rem;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          margin-bottom: 30px;
          background-color: #f8f9fa;
          padding: 20px;
          border-radius: 5px;
        }
        .stat-item {
          text-align: center;
        }
        .stat-value {
          font-size: 1.5rem;
          font-weight: bold;
          color: #4ade80;
        }
        .stat-label {
          color: #666;
          font-size: 0.9rem;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 8px 12px;
          text-align: left;
        }
        th {
          background-color: #4ade80;
          color: white;
          font-weight: bold;
        }
        .footer {
          text-align: center;
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #ddd;
          color: #666;
          font-size: 0.9rem;
        }
        @media print {
          body { margin: 0; }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>CropSense AI Summary Report</h1>
        <div>Generated on ${formatDate(new Date())}</div>
      </div>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">${stats.total_predictions ?? 0}</div>
          <div class="stat-label">Total Predictions</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${stats.unique_locations ?? 0}</div>
          <div class="stat-label">Unique Locations</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${stats.unique_soil_types ?? 0}</div>
          <div class="stat-label">Soil Types</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${((stats.avg_soil_confidence ?? 0) * 100).toFixed(1)}%</div>
          <div class="stat-label">Avg Confidence</div>
        </div>
      </div>

      <h2>Recent Predictions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Location</th>
            <th>Soil Type</th>
            <th>Confidence</th>
            <th>Crops</th>
          </tr>
        </thead>
        <tbody>
          ${predictionsHTML}
        </tbody>
      </table>

      <div class="footer">
        <p>CropSense AI - Advanced Soil Analysis & Crop Recommendation System</p>
      </div>
    </body>
    </html>
  `;

  const printWindow = window.open('', '_blank');
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();

  printWindow.onload = () => {
    printWindow.print();
  };
};