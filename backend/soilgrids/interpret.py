"""
Derived, rule-based interpretation of SoilGrids estimates.

Everything here is computed from the retrieved numbers with published, general
classification rules (USDA texture triangle, USDA pH classes, Indian Soil Health
Card organic-carbon classes). These are screening indicators, not lab results.
"""
from typing import Dict, List, Optional


def usda_texture_class(sand: float, silt: float, clay: float) -> Optional[str]:
    """USDA soil texture class from sand/silt/clay percentages."""
    if None in (sand, silt, clay):
        return None
    total = sand + silt + clay
    if total <= 0:
        return None
    sand, silt, clay = (100 * v / total for v in (sand, silt, clay))  # normalise to 100 %

    if silt + 1.5 * clay < 15:
        return "Sand"
    if silt + 1.5 * clay >= 15 and silt + 2 * clay < 30:
        return "Loamy sand"
    if (7 <= clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50 and silt + 2 * clay >= 30):
        return "Sandy loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return "Loam"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "Silt loam"
    if silt >= 80 and clay < 12:
        return "Silt"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "Sandy clay loam"
    if 27 <= clay < 40 and 20 < sand <= 45:
        return "Clay loam"
    if 27 <= clay < 40 and sand <= 20:
        return "Silty clay loam"
    if clay >= 35 and sand > 45:
        return "Sandy clay"
    if clay >= 40 and silt >= 40:
        return "Silty clay"
    if clay >= 40 and sand <= 45 and silt < 40:
        return "Clay"
    return None


def ph_class(ph: Optional[float]) -> Optional[str]:
    """USDA soil reaction classes."""
    if ph is None:
        return None
    for upper, name in [(4.5, "extremely acidic"), (5.05, "very strongly acidic"), (5.55, "strongly acidic"),
                        (6.05, "moderately acidic"), (6.55, "slightly acidic"), (7.35, "neutral"),
                        (7.85, "slightly alkaline"), (8.45, "moderately alkaline"), (9.05, "strongly alkaline")]:
        if ph < upper:
            return name
    return "very strongly alkaline"


def organic_carbon_class(soc_g_per_kg: Optional[float]) -> Optional[str]:
    """Soil Health Card (India) organic carbon classes: <0.5 % low, 0.5-0.75 % medium, >0.75 % high."""
    if soc_g_per_kg is None:
        return None
    oc_pct = soc_g_per_kg / 10.0
    return "low" if oc_pct < 0.5 else "medium" if oc_pct <= 0.75 else "high"


def screening_flags(top: Dict[str, Optional[float]], texture: Optional[str]) -> List[Dict[str, str]]:
    """
    Possible soil limitations worth checking, each with the evidence that triggered it.
    `top` holds 0-30 cm weighted means in display units.
    """
    flags = []
    ph, soc, sand, clay = top.get("phh2o"), top.get("soc"), top.get("sand"), top.get("clay")
    cec, bd, cf = top.get("cec"), top.get("bdod"), top.get("cfvo")

    if ph is not None and ph < 5.5:
        flags.append({"flag": "Soil acidity", "evidence": f"pH ≈ {ph:.1f} (below 5.5)",
                      "check": "Acid soils can limit phosphorus availability and some crops; a lab test with lime requirement is advised."})
    if ph is not None and ph > 8.5:
        flags.append({"flag": "Possible sodicity / high alkalinity", "evidence": f"pH ≈ {ph:.1f} (above 8.5)",
                      "check": "pH above 8.5 often indicates sodium problems; test EC and ESP (gypsum requirement) at a soil lab."})
    if soc is not None and soc / 10.0 < 0.5:
        flags.append({"flag": "Low organic carbon", "evidence": f"organic carbon ≈ {soc / 10:.2f} % (Soil Health Card 'low' < 0.5 %)",
                      "check": "Adding farmyard manure, compost, green manure or crop residues improves soil structure and fertility."})
    if sand is not None and sand >= 70:
        flags.append({"flag": "Low water and nutrient holding (sandy)", "evidence": f"sand ≈ {sand:.0f} %",
                      "check": "Sandy soils drain fast; frequent light irrigation, mulching and organic matter help."})
    if clay is not None and clay >= 45:
        flags.append({"flag": "Heavy clay: drainage and workability", "evidence": f"clay ≈ {clay:.0f} %",
                      "check": "High-clay soils can waterlog when wet and crack when dry; good drainage and timely tillage matter."})
    if cec is not None and cec < 10:
        flags.append({"flag": "Low nutrient-holding capacity", "evidence": f"CEC ≈ {cec:.1f} cmol(c)/kg (below ~10)",
                      "check": "Split fertiliser applications and organic matter reduce nutrient losses."})
    if bd is not None and bd >= 1.6:
        flags.append({"flag": "Possible compaction", "evidence": f"bulk density ≈ {bd:.2f} kg/dm³",
                      "check": "Values around 1.6 or more can restrict root growth in many soils; avoid tillage when wet, add organic matter."})
    if cf is not None and cf >= 15:
        flags.append({"flag": "Stony / gravelly soil", "evidence": f"coarse fragments ≈ {cf:.0f} % by volume",
                      "check": "Stones reduce the soil volume available for roots and water."})
    return flags
