#!/usr/bin/env python3
"""
NSW Crime Explorer - data processor.

Downloads the latest BOCSAR "Recorded Criminal Incidents by Suburb" dataset,
aggregates it, and writes the compact JSON the dashboard consumes:

  data/index.json          - search index (suburb names + slugs + 2025 total) + metadata
  data/suburbs/<slug>.json - per-suburb annual totals (by category) + last-24-month monthly

Run:  python scripts/process.py
"""

import csv, json, os, re, sys, zipfile, io, urllib.request
from collections import defaultdict

# ---- Config -----------------------------------------------------------------
SUBURB_ZIP_URL = "https://bocsarblob.blob.core.windows.net/bocsar-open-data/SuburbData.zip"
ANNUAL_FROM = 2010          # keep annual totals from this year
MONTHLY_MONTHS = 24         # keep this many most-recent monthly columns
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MONTHS = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
          'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}


def log(msg):
    print(f"[process] {msg}", flush=True)


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def download_csv():
    """Download the suburb ZIP and return the path to the extracted CSV."""
    log(f"Downloading {SUBURB_ZIP_URL} ...")
    req = urllib.request.Request(SUBURB_ZIP_URL, headers={'User-Agent': 'nsw-crime-explorer/1.0'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        blob = resp.read()
    log(f"Downloaded {len(blob)/1024/1024:.1f} MB. Extracting ...")
    zf = zipfile.ZipFile(io.BytesIO(blob))
    csv_name = [n for n in zf.namelist() if n.lower().endswith('.csv')][0]
    tmp_dir = os.path.join(os.path.dirname(__file__), "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    zf.extract(csv_name, tmp_dir)
    path = os.path.join(tmp_dir, csv_name)
    log(f"Extracted {csv_name}")
    return path, csv_name


def latest_year(month_cols):
    return max(int(c.split(' ')[1]) for c in month_cols)


def process(csv_path):
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        header = next(csv.reader(f))
    month_cols = header[3:]
    col_year = [int(c.split(' ')[1]) for c in month_cols]
    last_year = latest_year(month_cols)
    years = list(range(ANNUAL_FROM, last_year + 1))
    monthly_labels = month_cols[-MONTHLY_MONTHS:]

    # data[suburb][category] = {'annual':{year:count}, 'monthly':[...]}
    data = defaultdict(lambda: defaultdict(
        lambda: {'annual': defaultdict(int), 'monthly': [0] * MONTHLY_MONTHS}))

    n = 0
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            n += 1
            sub, cat = row[0], row[1]
            vals = row[3:]
            d = data[sub][cat]
            ann = d['annual']
            for i, v in enumerate(vals):
                if v and v != '0':
                    y = col_year[i]
                    if y >= ANNUAL_FROM:
                        ann[y] += int(v)
            mvals = vals[-MONTHLY_MONTHS:]
            mon = d['monthly']
            for i, v in enumerate(mvals):
                if v and v != '0':
                    mon[i] += int(v)
    log(f"Processed {n:,} rows across {len(data):,} suburbs")

    # Build outputs
    os.makedirs(os.path.join(OUT_DIR, "suburbs"), exist_ok=True)
    index = []
    used = {}
    for name, cats in data.items():
        sl = slugify(name)
        base, k = sl, 2
        while sl in used:
            sl = f"{base}-{k}"; k += 1
        used[sl] = name

        cat_obj = {}
        total_last = 0
        for cat, d in cats.items():
            annual = [d['annual'].get(y, 0) for y in years]
            if sum(annual) == 0 and sum(d['monthly']) == 0:
                continue
            cat_obj[cat] = {'a': annual, 'm': d['monthly']}
            total_last += d['annual'].get(last_year, 0)
        if not cat_obj:
            continue
        with open(os.path.join(OUT_DIR, "suburbs", f"{sl}.json"), 'w') as fp:
            json.dump({'name': name, 'c': cat_obj}, fp, separators=(',', ':'))
        index.append({'n': name, 's': sl, 't': total_last})

    index.sort(key=lambda x: x['n'])
    meta = {
        'years': years,
        'monthly_labels': monthly_labels,
        'categories': sorted({c for s in data.values() for c in s}),
        'release': f"to {monthly_labels[-1]}",
        'last_year': last_year,
        'source': 'NSW BOCSAR Recorded Criminal Incidents by Suburb',
    }
    with open(os.path.join(OUT_DIR, "index.json"), 'w') as fp:
        json.dump({'meta': meta, 'suburbs': index}, fp, separators=(',', ':'))
    log(f"Wrote index.json ({len(index):,} suburbs) and per-suburb files to {OUT_DIR}")


def main():
    csv_path, _ = download_csv()
    process(csv_path)
    # tidy up the big temp file so it isn't committed
    try:
        os.remove(csv_path)
    except OSError:
        pass
    log("Done.")


if __name__ == "__main__":
    main()
