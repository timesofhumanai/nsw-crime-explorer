# NSW Crime Explorer

An interactive dashboard for comparing recorded crime across New South Wales suburbs,
built on open data from the NSW Bureau of Crime Statistics and Research (BOCSAR).

Compare 1, 2 or 3 suburbs side by side across 21 offence categories, see trends from
2010 to the latest year and over the last 24 months, and view each suburb's offence
breakdown as a donut chart. Light and dark themes.

## How it works

- `index.html` - the dashboard (single self-contained file, no build step)
- `data/index.json` - search index: every suburb, its slug, and its latest-year total
- `data/suburbs/<slug>.json` - per-suburb data, loaded on demand when a suburb is selected
- `scripts/process.py` - downloads the latest BOCSAR suburb dataset and regenerates the JSON
- `.github/workflows/update.yml` - re-runs the processor once a year and commits the result

The dashboard fetches `data/index.json` on load, then loads individual suburb files only
as needed, so the initial page is light even though the full dataset covers ~4,500 suburbs.

## Updating the data

The data refreshes automatically once a year via GitHub Actions. To refresh manually,
go to the **Actions** tab, choose **Update crime data**, and click **Run workflow**.

To run locally:

```bash
python scripts/process.py
```

## Data source and attribution

NSW Bureau of Crime Statistics and Research (BOCSAR), *Recorded Criminal Incidents by
Suburb*, released under Creative Commons Attribution. Figures are counts of incidents
recorded by police, not a measure of how dangerous an area is. Larger suburbs record
more incidents simply because more people live and pass through them.

This tool is informational only and is not advice of any kind.
