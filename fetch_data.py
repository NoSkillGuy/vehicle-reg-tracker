import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.offline as pyo

"""
Two-Wheeler Registration Data Collector

This script fetches daily vehicle registration data for:
- Manufacturers: OLA ELECTRIC TECHNOLOGIES PVT LTD, BAJAJ AUTO LTD
- Vehicle Type: Two Wheeler
- EV Types: ELECTRIC BOV, PURE EV
- Time Period: 2024-2025
- Data Source: Parivahan Analytics Dashboard

Resilient fetching: Runs multiple times per day but only fetches data once per day.
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
        "name": "Hero Motocorp Ltd",
        "code": "HERO MOTOCORP LTD",
        "filename": "hero_motocorp"
    },
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
        "vehicleCategoryGroup[]": "Two Wheeler",
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
        now = datetime.now(timezone.utc)
        today_date = now.strftime("%Y-%m-%d")
        fetch_timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        df_today["fetch_date"] = today_date
        df_today["fetch_timestamp"] = fetch_timestamp
        
        return df_today, today_date, fetch_timestamp
        
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

def plot_daily_changes():
    """Read data/daily_changes.csv and save a multi-line plot as data/daily_changes.png"""
    csv_path = "data/daily_changes.csv"
    output_path = "data/daily_changes.png"
    if not os.path.exists(csv_path):
        print("ℹ️ No daily_changes.csv found; skipping plot.")
        return
    
    df = pd.read_csv(csv_path)
    if df.empty:
        print("ℹ️ daily_changes.csv is empty; skipping plot.")
        return

    # Ensure date is parsed and sorted
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    
    # Melt or plot directly by columns (excluding date)
    manufacturers = [c for c in df.columns if c != 'date']
    plt.figure(figsize=(12, 6))
    for m in manufacturers:
        plt.plot(df['date'], df[m], marker='o', linewidth=2, label=m)
    
    plt.title('Daily Registration Changes by Manufacturer')
    plt.xlabel('Date')
    plt.ylabel('Change in Registered Vehicles')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(loc='upper left', ncol=2)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"📊 Saved plot: {output_path}")

def plot_monthly_changes():
    """Aggregate monthly registeredVehicleCount across manufacturers and save plot and CSV."""
    combined_df = None
    # Collect per-manufacturer monthly data
    for m in MANUFACTURERS:
        path = f"data/{m['filename']}_two_wheeler_data.csv"
        if not os.path.exists(path):
            print(f"ℹ️ Missing snapshot for {m['name']} at {path}; skipping in monthly plot.")
            continue
        df = pd.read_csv(path)
        if 'yearAsString' not in df.columns or 'registeredVehicleCount' not in df.columns:
            print(f"⚠️ Unexpected schema in {path}; skipping.")
            continue
        df = df[['yearAsString', 'registeredVehicleCount']].copy()
        df = df.rename(columns={'registeredVehicleCount': m['name']})
        if combined_df is None:
            combined_df = df
        else:
            combined_df = combined_df.merge(df, on='yearAsString', how='outer')
    
    if combined_df is None or combined_df.empty:
        print("ℹ️ No monthly data available to plot.")
        return
    
    # Parse year-month and sort
    try:
        combined_df['date'] = pd.to_datetime(combined_df['yearAsString'], format='%Y-%B')
    except Exception:
        # Fallback: attempt generic parse
        combined_df['date'] = pd.to_datetime(combined_df['yearAsString'])
    combined_df = combined_df.sort_values('date')
    
    # Fill missing with 0 so all lines render
    value_cols = [c for c in combined_df.columns if c not in ['yearAsString', 'date']]
    combined_df[value_cols] = combined_df[value_cols].fillna(0)
    
    # Save merged CSV
    combined_csv_path = 'data/monthly_changes.csv'
    combined_df_out = combined_df[['date'] + value_cols].copy()
    combined_df_out['date'] = combined_df_out['date'].dt.strftime('%Y-%m')
    combined_df_out.to_csv(combined_csv_path, index=False)
    
    # Plot
    plt.figure(figsize=(12, 6))
    for col in value_cols:
        plt.plot(combined_df['date'], combined_df[col], marker='o', linewidth=2, label=col)
    plt.title('Monthly Registration Totals by Manufacturer')
    plt.xlabel('Month')
    plt.ylabel('Registered Vehicles')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(loc='upper left', ncol=2)
    plt.tight_layout()
    output_path = 'data/monthly_changes.png'
    plt.savefig(output_path)
    plt.close()
    print(f"📊 Saved monthly plot: {output_path}\n🗂️ Saved combined CSV: {combined_csv_path}")

def plotly_daily_changes():
    os.makedirs('docs', exist_ok=True)
    csv_path = 'data/daily_changes.csv'
    output_path = 'docs/daily_changes.html'
    if not os.path.exists(csv_path):
        print('ℹ️ No daily_changes.csv found; skipping interactive daily plot.')
        return
    df = pd.read_csv(csv_path)
    if df.empty:
        print('ℹ️ daily_changes.csv is empty; skipping interactive daily plot.')
        return
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    fig = go.Figure()
    for col in [c for c in df.columns if c != 'date']:
        pct = df[col].pct_change() * 100
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df[col],
                mode='lines+markers',
                name=col,
                customdata=pct.round(2),
                hovertemplate='%{x|%Y-%m-%d}<br>%{fullData.name}: Δ %{y} (%{customdata}%)<extra></extra>'
            )
        )
    fig.update_layout(
        title='Daily Registration Changes by Manufacturer',
        xaxis_title='Date', yaxis_title='Change in Registered Vehicles',
        template='plotly_white', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0)
    )
    pyo.plot(fig, filename=output_path, auto_open=False, include_plotlyjs='cdn')
    print(f'🕸️ Saved interactive daily plot: {output_path}')


def plotly_monthly_changes():
    os.makedirs('docs', exist_ok=True)
    csv_path = 'data/monthly_changes.csv'
    output_path = 'docs/monthly_changes.html'
    if not os.path.exists(csv_path):
        print('ℹ️ No monthly_changes.csv found; skipping interactive monthly plot.')
        return
    df = pd.read_csv(csv_path)
    if df.empty:
        print('ℹ️ monthly_changes.csv is empty; skipping interactive monthly plot.')
        return
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    fig = go.Figure()
    for col in [c for c in df.columns if c != 'date']:
        pct = df[col].pct_change() * 100
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df[col],
                mode='lines+markers',
                name=col,
                customdata=pct.round(2),
                hovertemplate='%{x|%Y-%m}<br>%{fullData.name}: %{y} (%{customdata}% MoM)<extra></extra>'
            )
        )
    fig.update_layout(
        title='Monthly Registration Totals by Manufacturer',
        xaxis_title='Month', yaxis_title='Registered Vehicles',
        template='plotly_white', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0)
    )
    pyo.plot(fig, filename=output_path, auto_open=False, include_plotlyjs='cdn')
    print(f'🕸️ Saved interactive monthly plot: {output_path}')

def check_data_already_fetched_today():
    """Check if data has already been fetched for the current day"""
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check if any manufacturer's data file has today's date
    for manufacturer in MANUFACTURERS:
        snapshot_path = f"data/{manufacturer['filename']}_two_wheeler_data.csv"
        if os.path.exists(snapshot_path):
            try:
                df = pd.read_csv(snapshot_path)
                if 'fetch_date' in df.columns and not df.empty:
                    # Check if any row has today's date
                    if today_date in df['fetch_date'].values:
                        print(f"✅ Data already fetched today ({today_date}) for {manufacturer['name']}")
                        return True
            except Exception as e:
                print(f"⚠️ Error reading {snapshot_path}: {e}")
                continue
    
    print(f"🔄 No data found for today ({today_date}), proceeding with fetch...")
    return False

def get_fetch_attempt_info():
    """Get information about the current fetch attempt"""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    
    # Determine which fetch attempt this is based on current time
    fetch_times = ["04:30", "05:30", "06:30", "10:30", "16:30"]
    attempt_number = 1
    
    for i, fetch_time in enumerate(fetch_times):
        if current_time >= fetch_time:
            attempt_number = i + 1
    
    return {
        "current_time": current_time,
        "attempt_number": attempt_number,
        "total_attempts": len(fetch_times),
        "fetch_times": fetch_times
    }

def log_fetch_attempt(fetch_info, success, successful_fetches, total_manufacturers, error_details=None):
    """Log fetch attempt details to a CSV file"""
    log_file = "data/fetch_log.csv"
    
    now = datetime.now(timezone.utc)
    log_entry = {
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'attempt_number': fetch_info['attempt_number'],
        'total_attempts': fetch_info['total_attempts'],
        'success': success,
        'successful_fetches': successful_fetches,
        'total_manufacturers': total_manufacturers,
        'error_details': error_details or '',
        'fetch_times': ', '.join(fetch_info['fetch_times'])
    }
    
    df_log = pd.DataFrame([log_entry])
    
    if os.path.exists(log_file):
        existing_log = pd.read_csv(log_file)
        df_log = pd.concat([existing_log, df_log], ignore_index=True)
    
    df_log.to_csv(log_file, index=False)
    print(f"📝 Fetch attempt logged to: {log_file}")

def main():
    """Main function to fetch and process data for all manufacturers"""
    # Ensure data folder exists
    os.makedirs("data", exist_ok=True)
    
    # Get fetch attempt information
    fetch_info = get_fetch_attempt_info()
    print(f"🚗 Starting data collection for two-wheeler manufacturers...")
    print(f"⏰ Current time: {fetch_info['current_time']} UTC")
    print(f"🔄 Attempt {fetch_info['attempt_number']} of {fetch_info['total_attempts']} today")
    print(f"📅 Scheduled times: {', '.join(fetch_info['fetch_times'])}")
    
    # Check if data has already been fetched today
    if check_data_already_fetched_today():
        print(f"✅ Data already fetched today. Skipping fetch attempt {fetch_info['attempt_number']}.")
        print("📊 Regenerating plots and documentation...")
        
        # Log the skipped attempt
        log_fetch_attempt(fetch_info, True, 5, 5, "Data already fetched today")
        
        # Still regenerate plots and docs even if no new data
        plot_daily_changes()
        plot_monthly_changes()
        plotly_daily_changes()
        plotly_monthly_changes()
        
        print("🎉 Plot and documentation regeneration completed!")
        return
    
    print(f"🔄 Proceeding with fetch attempt {fetch_info['attempt_number']}...")
    
    # Track successful fetches
    successful_fetches = 0
    total_manufacturers = len(MANUFACTURERS)
    error_details = []
    
    for manufacturer in MANUFACTURERS:
        print(f"\n🔍 Fetching data for {manufacturer['name']}...")
        
        result = fetch_manufacturer_data(manufacturer)
        if result:
            df_today, today_date, fetch_timestamp = result
            process_manufacturer_data(manufacturer, df_today, today_date)
            successful_fetches += 1
        else:
            error_msg = f"Failed to fetch {manufacturer['name']}"
            error_details.append(error_msg)
            print(f"❌ {error_msg}")
    
    print(f"\n📊 Fetch Summary:")
    print(f"   ✅ Successful: {successful_fetches}/{total_manufacturers}")
    print(f"   ❌ Failed: {total_manufacturers - successful_fetches}/{total_manufacturers}")
    
    # Log the fetch attempt
    log_fetch_attempt(fetch_info, successful_fetches > 0, successful_fetches, total_manufacturers, '; '.join(error_details) if error_details else None)
    
    if successful_fetches > 0:
        print(f"🎉 Data collection completed for attempt {fetch_info['attempt_number']}!")
        
        # Generate/update plots
        plot_daily_changes()
        plot_monthly_changes()
        plotly_daily_changes()
        plotly_monthly_changes()
    else:
        print(f"⚠️ No data was successfully fetched in attempt {fetch_info['attempt_number']}.")
        print("🔄 Will retry at the next scheduled time.")

if __name__ == "__main__":
    main()