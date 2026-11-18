"""
validate_lookup_against_shc.py
──────────────────────────────
Phase 4: Compare current Karnataka NPK lookup values against official Karnataka SHC dominant fertility classes.
"""

import os
import json
import pandas as pd
import numpy as np

LOOKUP_PATH = os.path.join('data', 'karnataka_main_places_npk_project_ready_v1.csv')
SHC_SHARE_PATH = os.path.join('research', 'shc_karnataka', 'karnataka_npk_district_share.csv')
SHC_WIDE_PATH = os.path.join('research', 'shc_karnataka', 'karnataka_npk_wide.csv')

# Standard Indian SHC / ICAR Fertility Classification Thresholds (kg/ha)
# Documented in research/shc_calibration/build_dataset.py lines 7-13:
# Nitrogen: Low < 280, Medium 280-560, High > 560
# Phosphorus:
#   Elemental P convention: Low < 10, Medium 10-25, High > 25
#   P2O5 convention: Low < 23, Medium 23-56, High > 56
# Potassium:
#   Elemental K convention: Low < 110, Medium 110-280, High > 280
#   K2O convention: Low < 144, Medium 144-336, High > 336

def classify_n(val):
    if val < 280: return "Low"
    elif val <= 560: return "Medium"
    else: return "High"

def classify_p(val, convention="elemental"):
    if convention == "elemental":
        if val < 10.0: return "Low"
        elif val <= 25.0: return "Medium"
        else: return "High"
    else: # P2O5
        if val < 23.0: return "Low"
        elif val <= 56.0: return "Medium"
        else: return "High"

def classify_k(val, convention="elemental"):
    if convention == "elemental":
        if val < 110.0: return "Low"
        elif val <= 280.0: return "Medium"
        else: return "High"
    else: # K2O
        if val < 144.0: return "Low"
        elif val <= 336.0: return "Medium"
        else: return "High"

def normalize_district_name(name):
    n = str(name).strip().lower()
    mapping = {
        'bagalkot': 'bagalkote',
        'chikkaballapur': 'chikkaballapura',
        'chamarajanagara': 'chamarajanagar',
        'bengaluru south': 'ramanagara', # Bengaluru South taluk / Ramanagara district
        'vijayanagar': 'vijayanagara'
    }
    return mapping.get(n, n)

def run_validation():
    print("==================================================================")
    print("PHASE 4: SHC VALIDATION OF CURRENT NPK LOOKUP")
    print("==================================================================")
    
    df_lookup = pd.read_csv(LOOKUP_PATH)
    # Filter out fallback row
    df_lookup = df_lookup[df_lookup['district'] != 'Karnataka coverage'].copy()
    
    df_share = pd.read_csv(SHC_SHARE_PATH)
    
    # Clean district names for merging
    df_lookup['dist_norm'] = df_lookup['district'].apply(normalize_district_name)
    df_share['dist_norm'] = df_share['district_name'].apply(normalize_district_name)
    
    # Pivot share table: district_name x nutrient_name -> Low, Medium, High shares
    piv = df_share.pivot(index='dist_norm', columns='nutrient_name', values=['Low', 'Medium', 'High'])
    
    records = []
    
    for _, row in df_lookup.iterrows():
        dist = row['district']
        d_norm = row['dist_norm']
        n_val = float(row['N_model_input'])
        p_val = float(row['P_model_input'])
        k_val = float(row['K_model_input'])
        source_type = row['source_type']
        
        # Classify lookup values under standard SHC thresholds
        n_class = classify_n(n_val)
        p_class_elem = classify_p(p_val, 'elemental')
        p_class_ox = classify_p(p_val, 'p2o5')
        k_class_elem = classify_k(k_val, 'elemental')
        k_class_ox = classify_k(k_val, 'k2o')
        
        if d_norm in piv.index:
            # SHC Nitrogen shares
            n_shares = {
                'Low': piv.loc[d_norm, ('Low', 'Nitrogen')],
                'Medium': piv.loc[d_norm, ('Medium', 'Nitrogen')],
                'High': piv.loc[d_norm, ('High', 'Nitrogen')]
            }
            shc_dom_n = max(n_shares, key=n_shares.get)
            shc_dom_n_pct = n_shares[shc_dom_n] * 100
            
            # SHC Phosphorus shares
            p_shares = {
                'Low': piv.loc[d_norm, ('Low', 'Phosphorus')],
                'Medium': piv.loc[d_norm, ('Medium', 'Phosphorus')],
                'High': piv.loc[d_norm, ('High', 'Phosphorus')]
            }
            shc_dom_p = max(p_shares, key=p_shares.get)
            shc_dom_p_pct = p_shares[shc_dom_p] * 100
            
            # SHC Potassium shares
            k_shares = {
                'Low': piv.loc[d_norm, ('Low', 'Potassium')],
                'Medium': piv.loc[d_norm, ('Medium', 'Potassium')],
                'High': piv.loc[d_norm, ('High', 'Potassium')]
            }
            shc_dom_k = max(k_shares, key=k_shares.get)
            shc_dom_k_pct = k_shares[shc_dom_k] * 100
            
            # Consistency evaluation
            # Nitrogen consistency
            if n_class == shc_dom_n:
                n_status = "CONSISTENT"
            elif n_shares[n_class] >= 0.25:
                n_status = "PARTIALLY_CONSISTENT"
            else:
                n_status = "DIVERGENT"
                
            # Phosphorus consistency (check both elemental and oxide)
            if p_class_ox == shc_dom_p or p_class_elem == shc_dom_p:
                p_status = "CONSISTENT"
            elif p_shares.get(p_class_ox, 0) >= 0.25 or p_shares.get(p_class_elem, 0) >= 0.25:
                p_status = "PARTIALLY_CONSISTENT"
            else:
                p_status = "DIVERGENT"
                
            # Potassium consistency
            if k_class_ox == shc_dom_k or k_class_elem == shc_dom_k:
                k_status = "CONSISTENT"
            elif k_shares.get(k_class_ox, 0) >= 0.25 or k_shares.get(k_class_elem, 0) >= 0.25:
                k_status = "PARTIALLY_CONSISTENT"
            else:
                k_status = "DIVERGENT"
                
            records.append({
                'district': dist,
                'source_type': source_type,
                'lookup_N': n_val,
                'lookup_N_class': n_class,
                'shc_dominant_N': f"{shc_dom_n} ({shc_dom_n_pct:.1f}%)",
                'shc_N_shares': f"L:{n_shares['Low']:.2f}, M:{n_shares['Medium']:.2f}, H:{n_shares['High']:.2f}",
                'N_consistency': n_status,
                'lookup_P': p_val,
                'lookup_P_class_ox': p_class_ox,
                'shc_dominant_P': f"{shc_dom_p} ({shc_dom_p_pct:.1f}%)",
                'shc_P_shares': f"L:{p_shares['Low']:.2f}, M:{p_shares['Medium']:.2f}, H:{p_shares['High']:.2f}",
                'P_consistency': p_status,
                'lookup_K': k_val,
                'lookup_K_class_ox': k_class_ox,
                'shc_dominant_K': f"{shc_dom_k} ({shc_dom_k_pct:.1f}%)",
                'shc_K_shares': f"L:{k_shares['Low']:.2f}, M:{k_shares['Medium']:.2f}, H:{k_shares['High']:.2f}",
                'K_consistency': k_status,
            })
            
    df_res = pd.DataFrame(records)
    out_csv = os.path.join('research', 'shc_karnataka', 'lookup_vs_shc_validation.csv')
    df_res.to_csv(out_csv, index=False)
    print(f"Validation completed for {len(df_res)} districts. Saved to {out_csv}")
    
    print("\n--- Summary Consistency Rates ---")
    for nut in ['N', 'P', 'K']:
        col = f"{nut}_consistency"
        counts = df_res[col].value_counts().to_dict()
        pct_con = 100 * (counts.get('CONSISTENT', 0) + counts.get('PARTIALLY_CONSISTENT', 0)) / len(df_res)
        print(f"Nutrient {nut}: {counts} -> Broadly Consistent (Consistent + Partial): {pct_con:.1f}%")
        
    print("\n--- Breakdown by Source Type (published_measured vs regional_proxy) ---")
    pub = df_res[df_res['source_type'] == 'published_measured']
    proxy = df_res[df_res['source_type'] == 'regional_proxy']
    print(f"Published/Measured anchors (n={len(pub)}):")
    for _, r in pub.iterrows():
        print(f"  {r['district']}: N={r['lookup_N']} ({r['lookup_N_class']} vs SHC {r['shc_dominant_N']}: {r['N_consistency']}) | P={r['lookup_P']} ({r['lookup_P_class_ox']} vs SHC {r['shc_dominant_P']}: {r['P_consistency']}) | K={r['lookup_K']} ({r['lookup_K_class_ox']} vs SHC {r['shc_dominant_K']}: {r['K_consistency']})")

if __name__ == '__main__':
    run_validation()
