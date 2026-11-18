# Soil Health Card (SHC) & SoilGrids Calibration Data Audit

**Date**: October 2026  
**Auditor**: CropSense AI Research & Validation Pipeline  
**Scope**: All data, code, and reference files under `research/shc_calibration/`  

---

## 1. Executive Summary

This data audit evaluates the supplied Soil Health Card (SHC) and SoilGrids calibration files located in `research/shc_calibration/` to determine whether they can reliably produce district-level available Nitrogen ($N$), Phosphorus ($P$), and Potassium ($K$) estimates for replacing the current Karnataka/hardcoded NPK lookup in CropSense AI.

### Key Audit Findings:
1. **Supplied Files**: The directory contains 5 files: `build_dataset.py`, `fetch_soilgrids.py`, `train_ptf.py`, `district_centroids.csv`, and `shc_district_with_coords.csv`.
2. **True Observation Count**: While `shc_district_with_coords.csv` has **6,600 rows**, it contains an exact **5-fold replication** created by an unstacked groupby-join in `build_dataset.py`. The genuine number of unique district-year observations is **1,320**.
3. **Geographic Coverage**: Spans **32 States & Union Territories** across India, covering **717 unique districts**.
4. **Temporal Coverage**: Spans two agricultural reporting cycles: **2023-24** (638 unique districts) and **2024-25** (682 unique districts).
5. **Georeferencing**: 1,166 district-year observations across **635 unique districts** have geographic coordinates (`lat`, `lon`), leaving **154 district-year observations (82 districts) missing coordinates**.
6. **Karnataka Coverage**: Contains **62 district-year observations across 31 districts** (all 31 official Karnataka districts). 29 districts have pre-matched coordinates; 2 districts (`Chamarajanagar` due to spelling difference and `Vijayanagara` due to recent 2021 bifurcation) lack coordinates in the pre-joined file.
7. **Target Quality & Methodology**: The target variables ($N, P, K$) are **not laboratory-measured continuous values**. They are **weighted category midpoint estimates** calculated from aggregate sample counts in 3 coarse fertility bins (Low, Medium, High). The Nitrogen midpoint constants in the supplied script ($137.5, 210.0, 297.5\text{ kg/ha}$) artificially compress all national Nitrogen estimates into $[137.5, 296.2]\text{ kg/ha}$, well below standard ICAR medium/high thresholds ($280\text{--}560+\text{ kg/ha}$).

---

## 2. Inventory of Supplied Files

| File Name | Size (Bytes) | Type / Language | Description & Functional Role |
| :--- | :--- | :--- | :--- |
| `district_centroids.csv` | 26,403 | CSV Data | Reference coordinate table providing representative latitude and longitude centroids for 724 Indian districts across 36 states/UTs. |
| `shc_district_with_coords.csv` | 1,038,420 | CSV Data | District-level aggregated SHC targets ($N, P, K, \text{pH}, \text{OC}$) merged with district centroid coordinates. |
| `build_dataset.py` | 2,068 | Python Script | Aggregation pipeline that parses raw village-level SHC category counts (`soil-nutrient-analysis.csv`), applies fertility band midpoints, and computes weighted district averages. |
| `fetch_soilgrids.py` | 3,510 | Python Script | Covariate fetcher designed to geocode districts via OpenStreetMap Nominatim and query ISRIC SoilGrids REST API for depth-specific soil properties with local JSON caching. |
| `train_ptf.py` | 2,007 | Python Script | Baseline pedotransfer training script utilizing `RandomForestRegressor` and 5-fold `GroupKFold` grouped by district. |

---

## 3. Detailed File Audits

### 3.1 `district_centroids.csv`
- **Row count**: 724 rows (plus header).
- **Columns & Data Types**:
  - `district_name` (`object` / string): Name of the district (719 unique names).
  - `state_name` (`object` / string): Name of the State or Union Territory (36 unique states).
  - `lat` (`float64`): Centroid latitude (ranges from 8.2954 to 34.5539 °N).
  - `lon` (`float64`): Centroid longitude (ranges from 68.9685 to 96.5564 °E).
- **Missing Values**: 0 nulls across all columns.
- **Duplicates**: 0 exact duplicates; 0 duplicate `(district_name, state_name)` pairs.
- **Coverage**: Full national coverage across 36 States/UTs.

### 3.2 `shc_district_with_coords.csv`
- **Row count**: 6,600 rows (plus header).
- **Columns & Data Types**:
  - `state_name` (`object`): State name (32 unique).
  - `district_name` (`object`): District name (714 unique names, 717 unique state-district entities).
  - `year` (`object`): Operational cycle (`2023-24` and `2024-25`).
  - `nutrient_name` (`object`): Nutrient indicator label (`Nitrogen`, `Organic Carbon`, `Phosphorus`, `Potassium`, `Soil Ph`).
  - `N_kg_ha` (`float64`): Estimated available Nitrogen in kg/ha (0 nulls).
  - `OC_pct` (`float64`): Estimated Organic Carbon percentage (15 nulls across 3 district-years).
  - `P_kg_ha` (`float64`): Estimated available Phosphorus in kg/ha (0 nulls).
  - `K_kg_ha` (`float64`): Estimated available Potassium in kg/ha (0 nulls).
  - `pH` (`float64`): Estimated Soil pH (5 nulls across 1 district-year).
  - `n_samples` (`int64`): Sample count in SHC portal (ranges from 1 to 2,058,958).
  - `lat` (`float64`): Centroid latitude (770 nulls across 154 district-years).
  - `lon` (`float64`): Centroid longitude (770 nulls across 154 district-years).
  - `skey` (`object`): Lowercase alphanumeric state key.

---

## 4. Structural Duplication & Grouping Analysis

### The 5-Fold Duplication Explained
In `shc_district_with_coords.csv`, each unique combination of `(state_name, district_name, year)` appears **exactly 5 times** (once for each value in `nutrient_name`).
- Within each group of 5 rows, the values of `N_kg_ha`, `P_kg_ha`, `K_kg_ha`, `pH`, `OC_pct`, `lat`, and `lon` are **100% identical** (standard deviation across rows = 0.000).
- The origin of this duplication is in `build_dataset.py` line 33:
  ```python
  wide = (g.w.sum() / g.value.sum().replace(0, np.nan)).unstack('nutrient_name')
  out = wide.join(n_samp).reset_index()
  ```
  `wide` is indexed by `(state_name, district_name, year)`, whereas `n_samp` retains `nutrient_name` in its multi-index. The resulting left join broadcasted the wide nutrient estimates across each nutrient sample row.
- **True Dataset Size**:
  - Raw CSV rows: 6,600
  - Unique District-Year Observations: **1,320**
  - Unique Districts: **717**
  - Observations with valid coordinates: **1,166** (5,830 rows / 5)

---

## 5. Nutrient & Covariate Availability

| Variable | Available in Dataset? | Rows Present (Unique Obs) | Missing Count | Data Origin | Units |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Available N** | Yes | 1,320 / 1,320 (100%) | 0 | SHC fertility class midpoint weighted mean | $\text{kg/ha}$ |
| **Available P** | Yes | 1,320 / 1,320 (100%) | 0 | SHC fertility class midpoint weighted mean | $\text{kg/ha}$ |
| **Available K** | Yes | 1,320 / 1,320 (100%) | 0 | SHC fertility class midpoint weighted mean | $\text{kg/ha}$ |
| **Soil pH** | Yes | 1,319 / 1,320 (99.9%) | 1 | SHC class midpoint weighted mean | $-\log[H^+]$ (pH units) |
| **Organic Carbon (OC)** | Yes | 1,317 / 1,320 (99.8%) | 3 | SHC class midpoint weighted mean | Weight % ($g/100g$) |
| **Coordinates (Lat/Lon)** | Yes | 1,166 / 1,320 (88.3%) | 154 | Centroid match from `district_centroids.csv` | Decimal Degrees (°N, °E) |

---

## 6. Target Distributions & Outlier Analysis

Distribution statistics evaluated across the 1,320 unique district-year observations:

| Parameter | Count | Mean | Std Dev | Min | 25% | Median | 75% | Max | IQR Outliers |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **N_kg_ha** | 1,320 | 163.97 | 32.78 | 137.50 | 137.91 | 149.20 | 181.17 | 296.16 | 40 high (> 246.06) |
| **P_kg_ha** | 1,320 | 24.71 | 8.67 | 7.50 | 16.94 | 23.70 | 32.48 | 40.00 | 0 |
| **K_kg_ha** | 1,320 | 222.93 | 79.79 | 72.96 | 155.12 | 205.32 | 286.33 | 400.00 | 0 |
| **pH** | 1,319 | 6.61 | 0.36 | 5.50 | 6.52 | 6.75 | 6.76 | 8.50 | 185 low (<6.16), 26 high (>7.12) |
| **OC_pct** | 1,317 | 0.51 | 0.19 | 0.25 | 0.33 | 0.49 | 0.65 | 0.90 | 0 |

### Critical Outlier & Boundary Observations:
- **Hard Clamping at Midpoints**:
  - The minimum possible $N$ is exactly $137.50\text{ kg/ha}$ (the assigned 'Low' midpoint). Exactly 156 district-years (11.8%) have $N = 137.50$, indicating 100% of tested samples in those districts fell into the 'Low' category.
  - The maximum $N$ in the dataset is $296.16\text{ kg/ha}$, just below the 'High' midpoint of $297.50\text{ kg/ha}$.
  - The minimum $P$ is $7.50\text{ kg/ha}$ (Low midpoint) and maximum is $40.00\text{ kg/ha}$ (High midpoint).
  - The minimum $K$ is $72.96\text{ kg/ha}$ and maximum is $400.00\text{ kg/ha}$.
  - The minimum $OC$ is $0.25\%$ and maximum is $0.90\%$.
- **No Pathological Values**: No negative values, infinite numbers, or corrupted text strings exist in the target columns.

---

## 7. Karnataka Geographic & Nutrient Audit

- **Total Karnataka Observations**: 62 district-years (31 in 2023-24, 31 in 2024-25).
- **Total Unique Karnataka Districts**: 31 (complete coverage of all Karnataka administrative districts).
- **Districts with Coordinates**: 29 of 31 districts (58 district-years).
- **Districts Missing Coordinates**: 2 districts:
  1. `Chamarajanagar` (spelled `Chamarajanagara` in `district_centroids.csv`).
  2. `Vijayanagara` (newly formed in 2021 from Ballari, present in SHC portal but omitted in the pre-2021 centroids table).
- **Karnataka Nutrient Summary (Mean ± Std)**:
  - $N$: $151.7 \pm 14.8\text{ kg/ha}$ (range: $137.5\text{--}201.2$)
  - $P$: $24.8 \pm 6.9\text{ kg/ha}$ (range: $11.4\text{--}39.5$)
  - $K$: $236.4 \pm 62.4\text{ kg/ha}$ (range: $122.9\text{--}359.8$)
  - $\text{pH}$: $6.69 \pm 0.29$ (range: $5.76\text{--}7.25$)
  - $\text{OC}$: $0.51 \pm 0.17\%$ (range: $0.27\text{--}0.85\%$)

---

## 8. Conclusion of Phase 1 Audit

The supplied data provides **1,166 georeferenced district-year observations across 635 districts** nationwide and **58 georeferenced observations across 29 districts in Karnataka**. The data is structurally sound once de-duplicated, but represents **discretized pseudo-continuous estimates** rather than precise physical lab measurements.
