# Vehicle Registration Tracker (EV Two-Wheelers)

Track daily and monthly registrations of electric two-wheelers in India by manufacturer using data from the Parivahan Analytics public dashboard. The repo fetches data, maintains CSV snapshots, computes daily changes, and generates both static PNG charts and Plotly HTML charts (embedded on the index page and published via GitHub Pages).

## Live Site

- GitHub Pages: https://noskillguy.github.io/vehicle-reg-tracker/

## Data Source

- Parivahan Analytics public dashboard: durationWiseRegistrationTable endpoint
- Manufacturers tracked are configured in `fetch_data.py`

## Quick Start

### 1) Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the fetcher

```bash
python fetch_data.py
```

This will:

- Fetch latest monthly totals per manufacturer and save per-manufacturer snapshots under `data/`
- Compute and update a consolidated `data/daily_changes.csv` (one row per date; one column per manufacturer)
- Render static charts: `data/daily_changes.png`, `data/monthly_changes.png`
- Generate HTML charts: `docs/daily_changes.html`, `docs/monthly_changes.html` (both are embedded on `docs/index.html`)

## Outputs

- CSV snapshots (per manufacturer):
  - `data/<slug>_two_wheeler_data.csv`
  - Columns: `year`, `yearAsString`, `registeredVehicleCount`, `monthlyCountList`, `fetch_date`
- Consolidated daily changes:
  - `data/daily_changes.csv` → columns: `date` (YYYY-MM-DD), one column per manufacturer
  - Always records 0 when no change for a day/manufacturer
- Consolidated monthly (merged from snapshots):
  - `data/monthly_changes.csv` → columns: `date` (YYYY-MM), one column per manufacturer
- Charts:
  - Static PNGs: `data/daily_changes.png`, `data/monthly_changes.png`
  - Interactive HTML (Plotly): `docs/daily_changes.html`, `docs/monthly_changes.html`

## GitHub Pages

This repo includes a Pages workflow to publish the `docs/` directory.

1. Push to `master`.
2. In GitHub: Settings → Pages → Source: select “GitHub Actions”.
3. After the workflow runs, open your Pages URL (for this repo: https://noskillguy.github.io/vehicle-reg-tracker/). The index page embeds both charts one below the other, each with a fullscreen button.

## Automation (Optional)

There is a workflow in `.github/workflows/fetch.yml` (if enabled) that can be set to run on a schedule to refresh data and regenerate charts. Adjust the cron as needed.

## Customization

- Manufacturers are defined in `fetch_data.py` under `MANUFACTURERS`:
  - `name`: display name used as a column header
  - `code`: exact maker string required by the Parivahan API
  - `filename`: slug used for CSV filenames in `data/`
- To add a manufacturer, append a new entry to `MANUFACTURERS` with the correct API `code`.

## Notes & Caveats

- This project queries a public dashboard endpoint; availability/rate-limits or schema may change.
- If an endpoint changes, you may need to update headers/parameters in `fetch_data.py`.
- The script records daily changes by diffing the latest snapshot against the previous snapshot and writing a value (including 0 for no change) for every manufacturer for each date.

## Troubleshooting

- Empty or missing charts:
  - Ensure `data/daily_changes.csv` and `data/monthly_changes.csv` exist and have data.
  - Re-run `python fetch_data.py`.
- Pages not updating:
  - Confirm the Pages workflow ran successfully and Source is set to GitHub Actions.
- SSL/proxy issues:
  - Set environment variables for your proxy if required by your network.

## License

This repository is provided as-is for educational/analytical use. Ensure your use of data complies with the source’s terms.
