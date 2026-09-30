import pandas as pd

df = pd.read_csv("datasets/Crop_recommendation.csv")
print(f"Total rows: {len(df)}, columns: {list(df.columns)}")
print(f"Unique crops ({df['label'].nunique()}): {sorted(df['label'].unique())}")
print("\nCrop-by-crop feature ranges:")
header = f"{'Crop':12} | {'N (kg/ha)':13} | {'P (kg/ha)':13} | {'K (kg/ha)':13} | {'Temp (°C)':12} | {'Humidity (%)':14} | {'pH':10} | {'Rain (mm)':12}"
print(header)
print("-" * len(header))

for crop, g in sorted(df.groupby("label")):
    n_str = f"{g['N'].min():.0f}-{g['N'].max():.0f}"
    p_str = f"{g['P'].min():.0f}-{g['P'].max():.0f}"
    k_str = f"{g['K'].min():.0f}-{g['K'].max():.0f}"
    t_str = f"{g['temperature'].min():.1f}-{g['temperature'].max():.1f}"
    h_str = f"{g['humidity'].min():.0f}-{g['humidity'].max():.0f}"
    ph_str = f"{g['ph'].min():.2f}-{g['ph'].max():.2f}"
    r_str = f"{g['rainfall'].min():.0f}-{g['rainfall'].max():.0f}"
    print(f"{crop:12} | {n_str:13} | {p_str:13} | {k_str:13} | {t_str:12} | {h_str:14} | {ph_str:10} | {r_str:12}")
