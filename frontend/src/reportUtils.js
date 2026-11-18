/**
 * reportUtils.js — Utilities for generating and exporting prediction reports
 */
import { makeTranslator } from './i18n/LanguageContext';
import { getLanguage } from './i18n/languages';

// Fallback i18n helpers (English) when a report is generated without a language context.
const englishI18n = (() => {
  const t = makeTranslator('en');
  const tv = (group, raw) => (raw ? t(`${group}.${String(raw).toLowerCase().replace(/[^a-z]/g, '')}`, null, String(raw)) : raw);
  return { t, lang: 'en', meta: getLanguage('en'), crop: n => tv('crops', n), soil: n => tv('soils', n),
    formatDate: ts => new Date(ts).toLocaleString('en-IN') };
})();

const escapeHTML = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/**
 * Generate HTML content for a prediction report
 */
export const generateReportHTML = (prediction, i18n = englishI18n) => {
  const { t } = i18n;
  const formatDate = (timestamp) => i18n.formatDate(timestamp);

  const cropsHTML = (prediction.crops ?? []).map(crop => {
    const conf = ((crop.confidence ?? 0) * 100).toFixed(1);
    const match = t(`match.${crop.confidence_level || (crop.confidence >= 0.5 ? 'strong' : crop.confidence >= 0.2 ? 'moderate' : 'low')}`);
    return `<tr>
      <td>${escapeHTML(i18n.crop(crop.name ?? crop.crop) ?? t('common.unknown'))}</td>
      <td>${conf}% (${match})</td>
    </tr>`;
  }).join('');

  return `
    <!DOCTYPE html>
    <html lang="${i18n.meta.code}" dir="${i18n.meta.dir}">
    <head>
      <meta charset="UTF-8">
      <title>${t('report.title')}</title>
      <style>
        body {
          font-family: Arial, 'Nirmala UI', 'Noto Sans', 'Noto Sans Devanagari', 'Noto Sans Kannada', 'Noto Sans Telugu', 'Noto Sans Tamil', 'Noto Sans Malayalam', 'Noto Sans Bengali', 'Noto Sans Gujarati', 'Noto Sans Gurmukhi', 'Noto Sans Oriya', sans-serif;
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
        <h1>${t('report.title')}</h1>
        <div class="timestamp">${t('report.generated', { date: formatDate(new Date()) })}</div>
      </div>

      <div class="section">
        <h2>${t('report.locSoil')}</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">${t('report.location')}</span>
            <span class="value">${escapeHTML(prediction.location ?? t('common.unknown'))}</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.soilType')}</span>
            <span class="value">${escapeHTML(prediction.soil_type ? i18n.soil(prediction.soil_type) : t('common.unknown'))}</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.confidence')}</span>
            <span class="value">${((prediction.soil_confidence ?? 0) * 100).toFixed(1)}%</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.image')}</span>
            <span class="value">${escapeHTML(prediction.image_name ?? t('common.unknown'))}</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>${t('report.env')}</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">${t('report.temperature')}</span>
            <span class="value">${prediction.temperature ?? t('common.na')}°C</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.humidity')}</span>
            <span class="value">${prediction.humidity ?? t('common.na')}%</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.rainfall')}</span>
            <span class="value">${prediction.rainfall ?? t('common.na')}mm</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.ph')}</span>
            <span class="value">${prediction.ph ?? t('common.na')}</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.oc')}</span>
            <span class="value">${prediction.organic_carbon ?? t('common.na')}%</span>
          </div>
        </div>
      </div>

      <div class="section">
        <h2>${t('report.npkTitle')}</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">${t('report.availN')}</span>
            <span class="value">${prediction.N ?? t('common.na')} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.availP')}</span>
            <span class="value">${prediction.P ?? t('common.na')} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.availK')}</span>
            <span class="value">${prediction.K ?? t('common.na')} kg/ha</span>
          </div>
          <div class="info-item">
            <span class="label">${t('report.npkSource')}</span>
            <span class="value">${prediction.npk_district ?? 'Karnataka Baseline'} (${(prediction.npk_source_type ?? 'published').replace('_', ' ')})</span>
          </div>
        </div>
        ${prediction.npk_out_of_training_range ? `
        <div style="margin-top: 10px; padding: 8px 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; font-size: 11px; color: #92400e;">
          <strong>${t('report.oodLabel')}</strong> ${escapeHTML((i18n.lang === 'en' && prediction.ood_warning) || t('report.oodDefault'))}
        </div>` : ''}
      </div>

      <div class="coordinates">
        <strong>${t('report.gps')}</strong><br>
        ${t('report.latitude')}: ${(prediction.latitude ?? 0).toFixed(6)}, ${t('report.longitude')}: ${(prediction.longitude ?? 0).toFixed(6)}
      </div>

      <div class="section">
        <h2>${t('report.crops')}</h2>
        <table class="crops-table">
          <thead>
            <tr>
              <th>${t('report.crop')}</th>
              <th>${t('report.confidenceCol')}</th>
            </tr>
          </thead>
          <tbody>
            ${cropsHTML}
          </tbody>
        </table>
      </div>

      <div class="footer">
        <p>${t('report.footer')}</p>
        <p>${t('report.reportId', { id: escapeHTML(prediction.id ?? t('common.unknown')) })}</p>
      </div>
    </body>
    </html>
  `;
};

/**
 * Print the prediction report
 */
export const printReport = (prediction, i18n) => {
  const printWindow = window.open('', '_blank');
  const htmlContent = generateReportHTML(prediction, i18n);

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
export const downloadPDF = (prediction, i18n) => {
  const printWindow = window.open('', '_blank');
  const htmlContent = generateReportHTML(prediction, i18n);

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