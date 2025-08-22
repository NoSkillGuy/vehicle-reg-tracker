import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

"""
Two-Wheeler Registration Data Collector

This script fetches daily vehicle registration data for:
- Manufacturers: OLA ELECTRIC TECHNOLOGIES PVT LTD, BAJAJ AUTO LTD
- Vehicle Type: Two Wheeler
- EV Types: ELECTRIC BOV, PURE EV
- Time Period: 2024-2025
- Data Source: Parivahan Analytics Dashboard
"""

# API endpoint
URL = "https://analytics.parivahan.gov.in/analytics/publicdashboard/vahandashboard/durationWiseRegistrationTable"

# Define manufacturers to track
MANUFACTURERS = [
    {
        "name": "Bajaj Auto Ltd",
        "code": "BAJAJ AUTO LTD",
        "filename": "bajaj_auto"
    },
    {
        "name": "Tvs Motor Company Ltd",
        "code": "TVS MOTOR COMPANY LTD",
        "filename": "tvs_motor_company"
    },
    {
        "name": "Ola Electric Technologies Pvt Ltd",
        "code": "OLA ELECTRIC TECHNOLOGIES PVT LTD",
        "filename": "ola_electric"
    },
    {
        "name": "Ather Energy Ltd",
        "code": "ATHER ENERGY LTD",
        "filename": "ather_energy"
    },
    {
        "name": "Mahindra Last Mile Mobility Ltd",
        "code": "MAHINDRA LAST MILE MOBILITY LTD",
        "filename": "mahindra_last_mile_mobility"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://analytics.parivahan.gov.in/analytics/publicdashboard/vahan?lang=en",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"'
}

def fetch_manufacturer_data(manufacturer_info):
    """Fetch data for a specific manufacturer"""
    params = {
        "stateCode": "",
        "rtoCode": "0",
        "toYear": "2025",
        "fromYear": "2024",
        "vehicleMakers[]": manufacturer_info["code"],
        "calendarType": "3",
        "timePeriod": "0",
        "evType[]": ["ELECTRIC BOV", "PURE EV"],
        "fitnessCheck": "0",
        "vehicleType": ""
    }
    
    try:
        resp = requests.get(URL, params=params, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        
        if not data:
            print(f"⚠️ No data received for {manufacturer_info['name']}")
            return None
            
        df_today = pd.DataFrame(data)
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        df_today["fetch_date"] = today_date
        
        return df_today, today_date
        
    except Exception as e:
        print(f"❌ Error fetching data for {manufacturer_info['name']}: {e}")
        return None

def process_manufacturer_data(manufacturer_info, df_today, today_date):
    """Process and save data for a specific manufacturer"""
    yesterday_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # File paths
    snapshot_path = f"data/{manufacturer_info['filename']}_two_wheeler_data.csv"
    daily_changes_path = "data/daily_changes.csv"
    
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
        df_merged["registeredVehicleCount"] = df_merged["registeredVehicleCount_today"] - df_merged["registeredVehicleCount_yesterday"]
        df_changes = df_merged[df_merged["registeredVehicleCount"] != 0].copy()
        
        # Always create a change row, even if no change (set to 0)
        change_value = df_changes['registeredVehicleCount'].sum() if not df_changes.empty else 0
        
        # Create a simple dataframe with date and manufacturer's change
        df_change_row = pd.DataFrame({
            'date': [yesterday_date],
            manufacturer_info['name']: [change_value]
        })
        
        # Append or create daily_changes.csv
        if os.path.exists(daily_changes_path):
            df_existing_changes = pd.read_csv(daily_changes_path)
            
            # Ensure column for this manufacturer exists
            if manufacturer_info['name'] not in df_existing_changes.columns:
                df_existing_changes[manufacturer_info['name']] = 0
            
            # Check if date already exists
            if yesterday_date in df_existing_changes['date'].values:
                # Update existing row for this date
                mask = df_existing_changes['date'] == yesterday_date
                df_existing_changes.loc[mask, manufacturer_info['name']] = df_change_row[manufacturer_info['name']].iloc[0]
            else:
                # Add new row for this date
                # Fill NaN values for other manufacturers
                for other_manufacturer in MANUFACTURERS:
                    if other_manufacturer['name'] != manufacturer_info['name'] and other_manufacturer['name'] not in df_change_row.columns:
                        df_change_row[other_manufacturer['name']] = 0
                
                df_all_changes = pd.concat([df_existing_changes, df_change_row], ignore_index=True)
                df_existing_changes = df_all_changes
            
            df_existing_changes.to_csv(daily_changes_path, index=False)
        else:
            # Create new file with all manufacturers as columns
            df_new_changes = df_change_row.copy()
            for other_manufacturer in MANUFACTURERS:
                if other_manufacturer['name'] != manufacturer_info['name']:
                    df_new_changes[other_manufacturer['name']] = 0
            
            df_new_changes.to_csv(daily_changes_path, index=False)
        
        if change_value != 0:
            print(f"📈 Daily {manufacturer_info['name']} changes added to: {daily_changes_path}")
        else:
            print(f"ℹ️ No changes detected today for {manufacturer_info['name']} vehicles (recorded as 0).")

    else:
        print(f"📌 No previous {manufacturer_info['name']} data snapshot found. Creating baseline...")

    # Save today's snapshot (overwrite)
    df_today.to_csv(snapshot_path, index=False)
    print(f"✅ {manufacturer_info['name']} two-wheeler snapshot updated: {snapshot_path}")

def main():
    """Main function to fetch and process data for all manufacturers"""
    # Ensure data folder exists
    os.makedirs("data", exist_ok=True)
    
    print("🚗 Starting data collection for two-wheeler manufacturers...")
    
    for manufacturer in MANUFACTURERS:
        print(f"\n🔍 Fetching data for {manufacturer['name']}...")
        
        result = fetch_manufacturer_data(manufacturer)
        if result:
            df_today, today_date = result
            process_manufacturer_data(manufacturer, df_today, today_date)
        else:
            print(f"❌ Failed to fetch data for {manufacturer['name']}")
    
    print("\n🎉 Data collection completed!")

if __name__ == "__main__":
    main()