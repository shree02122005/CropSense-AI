// test_report_fixes.js — Test script to verify report generation fixes
const { generateReportHTML } = require('./reportUtils.js');

// Test with minimal data that might have undefined fields
const testPrediction = {
  id: 'test-123',
  location: undefined,  // undefined location
  soil_type: undefined,  // undefined soil_type
  soil_confidence: undefined,  // undefined confidence
  latitude: undefined,  // undefined latitude
  longitude: undefined,  // undefined longitude
  crops: [{crop: undefined, confidence: undefined}],  // undefined crop data
  temperature: undefined,
  humidity: undefined,
  rainfall: undefined,
  ph: undefined,
  organic_carbon: undefined,
  image_name: undefined,
  timestamp: '2024-01-01T00:00:00'
};

try {
  const html = generateReportHTML(testPrediction);
  console.log('✓ Report generation successful with undefined values');
  console.log('✓ No crashes occurred');
  console.log('✓ HTML length:', html.length, 'characters');

  // Check that safe defaults were applied
  if (html.includes('Unknown') && html.includes('N/A') && html.includes('0.0')) {
    console.log('✓ Safe defaults correctly applied');
  } else {
    console.log('⚠ Safe defaults may not be applied correctly');
  }

} catch (error) {
  console.error('✗ Error occurred:', error.message);
  process.exit(1);
}