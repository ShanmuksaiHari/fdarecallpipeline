# One-off EDA script used to sample reason_for_recall text and design the
# hazard categorization rules in src/hazard.py. Not part of the pipeline -
# run manually from the repo root: python exploration/explore_reasons.py

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fetch import fetch_window

records, meta = fetch_window("20260101", "20260909")

print(f"\n{len(records)} records\n")

for r in records[:40]:
    print(f"[{r.get('classification')}] {r.get('reason_for_recall')}")
    print()
