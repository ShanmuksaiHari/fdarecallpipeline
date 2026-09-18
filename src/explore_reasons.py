from fetch import fetch_window

records, meta = fetch_window("20260101", "20260909")

print(f"\n{len(records)} records\n")

for r in records[:40]:
    print(f"[{r.get('classification')}] {r.get('reason_for_recall')}")
    print()
