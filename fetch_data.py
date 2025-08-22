import requests
import pandas as pd
from datetime import datetime
import os

"""
OLA Electric Two-Wheeler Registration Data Collector

This script fetches daily vehicle registration data for:
- Manufacturer: OLA ELECTRIC TECHNOLOGIES PVT LTD
- Vehicle Type: Two Wheeler
- EV Types: ELECTRIC BOV, PURE EV
- Time Period: 2024-2025
- Data Source: Parivahan Analytics Dashboard
"""

# API endpoint
URL = "https://analytics.parivahan.gov.in/analytics/publicdashboard/vahandashboard/durationWiseRegistrationTable"

PARAMS = {
    "stateCode": "",
    "rtoCode": "0",
    "toYear": "2025",
    "fromYear": "2024",
    "vehicleMakers[]": "OLA ELECTRIC TECHNOLOGIES PVT LTD",
    "calendarType": "3",
    "timePeriod": "0",
    "vehicleCategoryGroup[]": "Two Wheeler",
    "evType[]": ["ELECTRIC BOV", "PURE EV"],
    "fitnessCheck": "0",
    "vehicleType": ""
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://analytics.parivahan.gov.in/analytics/publicdashboard/vahan?lang=en",
}

# Fetch today's data
resp = requests.get(URL, params=PARAMS, headers=HEADERS)
resp.raise_for_status()
data = resp.json()

df_today = pd.DataFrame(data)
today_date = datetime.utcnow().strftime("%Y-%m-%d")
df_today["fetch_date"] = today_date

# Ensure data folder exists
os.makedirs("data", exist_ok=True)
snapshot_path = "data/ola_electric_two_wheeler_data.csv"
diff_path = "data/ola_electric_daily_changes.csv"

# Compare with yesterday (if exists)
if os.path.exists(snapshot_path):
    df_yesterday = pd.read_csv(snapshot_path)

    # Merge on yearAsString
    df_merged = df_today.merge(
        df_yesterday[["yearAsString", "registeredVehicleCount"]],
        on="yearAsString",
        suffixes=("_today", "_yesterday")
    )

    # Calculate change
    df_merged["change"] = df_merged["registeredVehicleCount_today"] - df_merged["registeredVehicleCount_yesterday"]
    df_changes = df_merged[df_merged["change"] != 0].copy()
    df_changes["date"] = today_date

    if not df_changes.empty:
        # Append or create daily_diff.csv
        if os.path.exists(diff_path):
            df_existing_diff = pd.read_csv(diff_path)
            df_all_diff = pd.concat([df_existing_diff, df_changes[["date", "yearAsString", "change"]]], ignore_index=True)
        else:
            df_all_diff = df_changes[["date", "yearAsString", "change"]]

        df_all_diff.to_csv(diff_path, index=False)
        print("📈 Daily OLA Electric changes saved:", diff_path)
    else:
        print("ℹ️ No changes detected today for OLA Electric vehicles.")

else:
    print("📌 No previous OLA Electric data snapshot found. Creating baseline...")

# Save today's snapshot (overwrite)
df_today.to_csv(snapshot_path, index=False)
print("✅ OLA Electric two-wheeler snapshot updated:", snapshot_path)