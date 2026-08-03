"""World Bank indicators for India + world -> data/processed/worldbank_indicators.csv"""
from pathlib import Path

import wbgapi as wb

ROOT = Path(__file__).resolve().parents[1]
INDICATORS = [
    "NY.GDP.MKTP.KD.ZG",  # GDP growth %
    "NV.SRV.TOTL.ZS",     # services % of GDP
    "IT.NET.USER.ZS",     # internet users %
    "SL.UEM.TOTL.ZS",     # unemployment %
]
df = wb.data.DataFrame(INDICATORS, ["IND", "WLD"], range(2000, 2026))
out = ROOT / "data" / "processed" / "worldbank_indicators.csv"
df.to_csv(out)
print(f"wrote {out}")
