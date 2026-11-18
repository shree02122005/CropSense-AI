"""Step 1: SHC CSV (village-level category counts) -> district-level table of
estimated available N/P/K (kg/ha) + pH, OC. Long-format counts -> weighted
midpoint of standard SHC fertility bands."""
import pandas as pd, numpy as np, sys

# SHC standard fertility bands (kg/ha), midpoint per class
BANDS = {
    'Nitrogen':   {'Low': 137.5, 'Medium': 210.0, 'High': 297.5},      # <280, 280-560 (mid 280/280*?), std: L<280 M280-560 H>560 -> mids 140/420/... use conservative mids
    'Phosphorus': {'Low': 7.5,   'Medium': 16.5, 'High': 40.0},        # L<10 M10-25 H>25
    'Potassium':  {'Low': 72.5,  'Medium': 155.0, 'High': 400.0},      # L<110 M110-280 H>280
    'Soil Ph':    {'Acidic': 5.5, 'Neutral': 6.75, 'Alkaline': 8.5},
    'Organic Carbon': {'Low': 0.25, 'Medium': 0.55, 'High': 0.90},     # L<0.5 M0.5-0.75 H>0.75
}
WANT = list(BANDS)

def load():
    rows = []
    for ch in pd.read_csv('soil-nutrient-analysis.csv', chunksize=500_000):
        m = ch[ch.nutrient_name.isin(WANT)]
        if len(m): rows.append(m)
    return pd.concat(rows, ignore_index=True)

df = load()
print('long rows:', len(df))
df['value'] = pd.to_numeric(df.value, errors='coerce').fillna(0)
df['mid'] = df.apply(lambda r: BANDS.get(r.nutrient_name, {}).get(r.nutrient_level, np.nan), axis=1)
df = df.dropna(subset=['mid'])
df['w'] = df.value * df.mid

g = df.groupby(['state_name','district_name','year','nutrient_name'])
n_samp = df.groupby(['state_name','district_name','year','nutrient_name']).value.sum().rename('n_samples')
wide = (g.w.sum() / g.value.sum().replace(0, np.nan)).unstack('nutrient_name')
out = wide.join(n_samp).reset_index()
out = out.rename(columns={'Nitrogen':'N_kg_ha','Phosphorus':'P_kg_ha','Potassium':'K_kg_ha',
                          'Soil Ph':'pH','Organic Carbon':'OC_pct'})
out = out.dropna(subset=['N_kg_ha','P_kg_ha','K_kg_ha'])
out.to_csv('shc_district_targets.csv', index=False)
print(out.shape)
print(out.groupby('state_name').agg(n=('N_kg_ha','size'), N=('N_kg_ha','mean'), P=('P_kg_ha','mean'), K=('K_kg_ha','mean')).round(1).head(40))
