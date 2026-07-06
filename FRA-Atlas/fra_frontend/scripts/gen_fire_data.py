#!/usr/bin/env python3
"""Regenerate src/data/fireData.js from the fire forecast CSV."""
import csv, json, sys, os
csv_path = sys.argv[1] if len(sys.argv) > 1 else 'fire_forecast_7day.csv'
out_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'fireData.js')
rows = []
with open(csv_path) as f:
    for r in csv.DictReader(f):
        rows.append({'id': int(r['location_id']), 'lat': round(float(r['latitude']),4),
            'lng': round(float(r['longitude']),4), 'date': r['date'],
            'prob': round(float(r['fire_probability']),4), 'risk': r['risk_level']})
dates = sorted(set(r['date'] for r in rows))
content = ('// Auto-generated from ' + os.path.basename(csv_path) + '\n'
    + 'export const FIRE_DATA = ' + json.dumps(rows, separators=(',',':')) + ';\n'
    + 'export const FIRE_DATES = ' + json.dumps(dates) + ';\n')
with open(out_path, 'w') as f:
    f.write(content)
print(f'Wrote {len(rows)} fire records across {len(dates)} dates to {out_path}')
