# Karnataka Soil Health Card NPK dataset (Cycle 2023-24 + 2024-25)

Source: Soil Nutrient Analysis dataset published by the Ministry of Agriculture &
Farmers Welfare on the India Data Portal (CKAN), extracted from
soilhealth.dac.gov.in SHC data. Original file: soil-nutrient-analysis.csv (~1.1 GB,
all India). Filtered here to state_name == "Karnataka".

## Files
1. karnataka_shc.csv  (363,080 rows, raw Karnataka extract)
   Columns: id, year, state_name, state_code, district_name, district_code,
   block_name, block_code, village_name, village_code, nutrient_type,
   nutrient_name, nutrient_level, value
   - nutrient_name includes: Nitrogen, Phosphorus, Potassium, Organic Carbon,
     Soil Ph, Electrical Conductivity, plus micronutrients (Zn, Fe, Cu, Mn, B) and Sulphur
   - For N/P/K, nutrient_level is the category (Low/Medium/High) and `value` is the
     NUMBER OF SOIL HEALTH CARDS (samples) in that village falling in that category
   - For pH, EC: level is Acidic/Neutral/Alkaline, Saline/Non Saline
   - For OC and micronutrients: Deficient/Sufficient

2. karnataka_npk_tidy.csv (long format, N/P/K only: year, district, block, village,
   nutrient_name, nutrient_level, cards)

3. karnataka_npk_wide.csv (12,520 village-year rows)
   Columns: year, district_name, block_name, village_name,
   nitrogen_low, nitrogen_medium, nitrogen_high,
   phosphorus_low, phosphorus_medium, phosphorus_high,
   potassium_low, potassium_medium, potassium_high
   Each cell = number of SHC samples in that category.

4. karnataka_npk_district_share.csv
   Share of Low/Medium/High per nutrient per district (all years pooled).

## Important limitation (same one your report found)
This is REAL government lab-scheme data, but it is CATEGORICAL: each sample is a
Low/Medium/High class, not a continuous kg/ha measurement. Converting categories to
continuous N-P-K values requires choosing class midpoints (an assumption), so this
data is well suited for:
- classifying/simulating SHC-style inputs (what your production lookup does)
- building a classifier (predict the N/P/K class from SoilGrids covariates)
- calibrating or validating your Karnataka npk_lookup.py ranges
It is NOT directly a continuous regression ground truth, unless you accept the
midpoint assumption your report already flagged.

Coverage: 31 districts, 2 SHC cycles (2023-24, 2024-25), ~12,520 village-year rows.
Note: village_name is not globally unique; identify villages by (district, block, village) or codes in the raw file.
