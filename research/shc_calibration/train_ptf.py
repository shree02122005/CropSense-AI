"""Step 3: train district-level pedotransfer models
    SoilGrids covariates (pH, SOC, total N, clay, sand, CEC) -> available N/P/K (kg/ha)
Requires: shc_district_with_coords.csv joined with fetch_soilgrids.py output.
Run AFTER covariates are fetched (ISRIC endpoint was down during build;
fetch_soilgrids.py is resumable and caches every response)."""
import pandas as pd, numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error

COV = ['phh2o_0-5cm','phh2o_0-30cm','soc_0-5cm','soc_0-30cm','nitrogen_0-5cm',
       'nitrogen_0-30cm','clay_0-30cm','sand_0-30cm','cec_0-30cm']
TARGETS = ['N_kg_ha','P_kg_ha','K_kg_ha']

def run():
    df = pd.read_csv('shc_with_covariates.csv')
    have_cov = [c for c in COV if c in df.columns]
    if len(have_cov) < 5:
        raise SystemExit('Covariates missing - run fetch_soilgrids.py first')
    df = df.dropna(subset=have_cov + TARGETS)
    # district-average both sides (dedup the duplicated nutrient-group rows)
    g = df.groupby(['state_name','district_name']).agg({**{c:'mean' for c in have_cov},
        **{t:'mean' for t in TARGETS}}).reset_index().dropna()
    X, groups = g[have_cov], g.district_name
    print(f'{len(g)} districts, {len(have_cov)} covariates')
    cv = GroupKFold(n_splits=5)   # spatial-ish: whole district held out together
    models = {}
    for t in TARGETS:
        rf = RandomForestRegressor(n_estimators=500, min_samples_leaf=3, random_state=42, n_jobs=-1)
        pred = cross_val_predict(rf, X, g[t], cv=cv, groups=groups)
        r2, mae = r2_score(g[t], pred), mean_absolute_error(g[t], pred)
        print(f'{t}: spatial CV R2={r2:.2f} MAE={mae:.1f} kg/ha (baseline MAE={g[t].std():.1f})')
        rf.fit(X, g[t]); models[t] = rf
    import joblib; joblib.dump({'features': have_cov, 'models': models}, 'npk_ptf.joblib')
    print('saved npk_ptf.joblib')

if __name__ == '__main__':
    run()
