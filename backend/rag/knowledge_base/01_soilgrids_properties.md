---
title: Understanding SoilGrids soil properties
topic: soil analysis
basis: ISRIC SoilGrids 2.0 documentation; standard soil-science interpretation
---

# Understanding SoilGrids soil properties

## What SoilGrids is
ISRIC SoilGrids 2.0 is a global map of soil properties produced by machine learning from about 240,000 soil profiles and environmental data such as climate, terrain and satellite imagery. It gives predictions on a 250 m grid for six standard depths. Values are estimates for the area around a point, not measurements of a specific field. Each value has a 90% prediction interval (the 5% and 95% quantiles); a wide interval means the estimate is uncertain. A laboratory soil test of the actual field is always more reliable.

## Properties and units
- phh2o: soil pH measured in water. SoilGrids stores pH x 10, so 62 means pH 6.2.
- clay, sand, silt: particle-size fractions of the fine earth (particles smaller than 2 mm). Stored in g/kg; dividing by 10 gives percent. Clay, silt and sand add up to about 100%.
- soc: soil organic carbon, stored in dg/kg; dividing by 10 gives g/kg. Dividing g/kg by 10 gives organic carbon percent, the unit used on Indian Soil Health Cards.
- nitrogen: TOTAL soil nitrogen, stored in cg/kg; dividing by 100 gives g/kg. Total nitrogen is mostly bound in organic matter. It is not the same as plant-available (mineral) nitrogen used for fertiliser recommendations.
- cec: cation exchange capacity at pH 7, stored in mmol(c)/kg; dividing by 10 gives cmol(c)/kg. CEC is the soil's ability to hold nutrient cations such as calcium, magnesium and potassium.
- bdod: bulk density of the fine earth, stored in cg/cm3; dividing by 100 gives kg/dm3 (same as g/cm3).
- cfvo: volume of coarse fragments (gravel and stones larger than 2 mm), stored in cm3/dm3; dividing by 10 gives volume percent.

## What SoilGrids does NOT provide
SoilGrids does not give available phosphorus, available potassium, plant-available nitrogen (so it cannot give an NPK fertiliser status), micronutrients such as zinc, iron or boron, electrical conductivity or salinity, exchangeable sodium percentage, or real-time soil moisture. These need a soil test (for nutrients and salinity) or field sensors (for moisture). Never report values for these parameters from SoilGrids.

## Interpreting the main properties
- Organic carbon (Soil Health Card classes): below 0.5% is low, 0.5 to 0.75% is medium, above 0.75% is high. Low organic carbon usually means poor soil structure, low biological activity and lower nutrient supply.
- CEC (general guide): below about 10 cmol(c)/kg is low (sandy or highly weathered soils such as many red and laterite soils), 10 to 25 is moderate, above 25 is high (clay-rich soils such as black cotton soils). Low-CEC soils lose nutrients by leaching, so fertiliser is best applied in split doses.
- Bulk density: typical mineral topsoils are between about 1.1 and 1.6 kg/dm3. Higher values indicate compaction; roots of many crops are restricted above about 1.6 in sandy soils and at lower values in clayey soils.
- Coarse fragments: more gravel and stones means less soil volume for roots and less water stored per unit depth.
- Total nitrogen: typical agricultural topsoils contain roughly 0.5 to 3 g/kg. It indicates organic matter status but does not tell how much nitrogen fertiliser a crop needs.

## Depths
For most field crops the 0 to 30 cm layer (SoilGrids depths 0-5, 5-15 and 15-30 cm) is the main root zone. A thickness-weighted average of the three layers gives a useful single value for the root zone.
