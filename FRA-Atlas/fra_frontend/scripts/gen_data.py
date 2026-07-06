#!/usr/bin/env python3
"""Regenerate src/data/fraData.js from CSV. Run after ML team updates CSV."""
import csv, json, sys, os
csv_path = sys.argv[1] if len(sys.argv) > 1 else 'fra_risk_scores.csv'
out_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'fraData.js')
rows = []
with open(csv_path) as f:
    for row in csv.DictReader(f):
        rows.append({'state': row['state'], 'district': row['district'],
            'ri': round(float(row['Risk_Index']),2), 'cl': int(row['Cluster']),
            'rl': row['Risk_Level'], 'rr': int(row['Risk_Rank']),
            'ar': round(float(row['Approval Rate']),4),
            'pr': round(float(row['Pending Claims Rate']),4),
            'pt': round(float(row['Avg Processing Time']),1),
            'fl': round(float(row['Forest Loss Rate']),3),
            'tc': round(float(row['Tribal Pop. Coverage']),4),
            'cr': round(float(row['CFR Recognition Rate']),4),
            'rjr': round(float(row['Rejection Rate']),4),
            'enc': round(float(row['Encroachment Density']),4)})
content = f'// Auto-generated\nexport const FRA_DATA = {json.dumps(rows, separators=(",",":"))};'
with open(out_path, 'w') as f:
    f.write(content)
print(f'Written {len(rows)} records to {out_path}')
