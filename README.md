# Vehicle Registration Tracker

This project tracks daily vehicle registration data for major two-wheeler manufacturers in India, focusing on electric vehicles.

## Features

- **Automated Data Collection**: Fetches data from Parivahan Analytics Dashboard
- **Interactive Visualizations**: Generates Plotly HTML charts for web display
- **Resilient Fetching**: Multiple daily attempts with smart duplicate prevention
- **Data Snapshots**: Maintains historical CSV data for analysis
- **Live Documentation**: Auto-updates HTML charts and documentation

## Data Sources

- **Manufacturers**: Bajaj Auto, TVS Motor, Ola Electric, Ather Energy, Hero Motocorp
- **Vehicle Type**: Two Wheelers
- **EV Types**: Electric BOV, Pure EV
- **Time Period**: 2024-2025
- **Source**: Parivahan Analytics Dashboard

## Output Files

### Data Files
- `data/*_two_wheeler_data.csv`: Individual manufacturer snapshots
- `data/daily_changes.csv`: Daily registration changes
- `data/monthly_changes.csv`: Monthly registration totals
- `data/fetch_log.csv`: Fetch attempt logs

### Documentation
- `docs/daily_changes.html`: Interactive daily changes chart
- `docs/monthly_changes.html`: Interactive monthly totals chart
- `docs/index.html`: Main dashboard page

## Resilient Data Fetching System

The system now implements a resilient fetching mechanism that runs multiple times per day to ensure data reliability while preventing duplicate fetches.

### How It Works

1. **Multiple Fetch Attempts**: The system runs 5 times daily at:

   - 04:30 UTC (10:00 AM IST)
   - 05:30 UTC (11:00 AM IST)
   - 06:30 UTC (12:00 PM IST)
   - 10:30 UTC (4:00 PM IST)
   - 16:30 UTC (10:00 PM IST)

2. **Smart Duplicate Prevention**:

   - Each fetch attempt checks if data has already been retrieved for the current day
   - If data exists, the fetch is skipped but plots and documentation are still regenerated
   - Only the first successful fetch of the day actually retrieves new data

3. **Data Attribution**:

   - Each data record includes both `fetch_date` (date) and `fetch_timestamp` (exact time)
   - A `fetch_log.csv` tracks all attempts, successes, and failures
   - Failed attempts are logged with detailed error information

4. **Benefits**:

   - **Reliability**: Multiple attempts ensure data is captured even if some fail
   - **Efficiency**: No duplicate data fetching on the same day
   - **Transparency**: Complete audit trail of all fetch attempts
   - **Resilience**: System continues to function even with intermittent API failures

### Fetch Log

The system maintains a detailed log at `data/fetch_log.csv` with columns:

- `date`: Date of the fetch attempt
- `time`: Exact time of the attempt
- `attempt_number`: Which attempt this was (1-5)
- `total_attempts`: Total attempts scheduled (5)
- `success`: Whether any data was successfully fetched
- `successful_fetches`: Number of manufacturers successfully fetched
- `total_manufacturers`: Total manufacturers attempted
- `error_details`: Any error messages encountered
- `fetch_times`: All scheduled fetch times for the day

### Example Scenarios

**Scenario 1: First fetch of the day (4:30 AM)**

- Data doesn't exist for today
- System fetches data from all manufacturers
- Data is saved with current timestamp
- Interactive HTML charts and documentation are generated

**Scenario 2: Subsequent fetch (5:30 AM)**

- Data already exists for today
- Fetch is skipped
- HTML charts and documentation are regenerated
- Fetch attempt is logged as "Data already fetched today"

**Scenario 3: Partial failure (6:30 AM)**

- Some manufacturers fail to fetch
- Successful fetches are saved
- Failed attempts are logged with error details
- System will retry at next scheduled time

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
