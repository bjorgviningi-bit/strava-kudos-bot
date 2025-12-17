import os
import requests
from datetime import datetime
from collections import defaultdict
import json

# Strava API credentials
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

def get_access_token():
    url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload)
    return response.json()['access_token']

def get_athlete_activities(access_token, per_page=200):
    """Fetch all athlete activities"""
    url = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    activities = []
    page = 1
    
    while True:
        params = {'per_page': per_page, 'page': page}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching activities: {response.status_code}")
            break
        
        page_activities = response.json()
        
        if not page_activities:
            break
        
        activities.extend(page_activities)
        print(f"Fetched page {page} ({len(page_activities)} activities)")
        page += 1
    
    return activities

def print_table(data, title):
    """Print data in year x month table format"""
    if not data:
        print(f"\n{title}")
        print("No data available\n")
        return
    
    # Get all years
    years = sorted(set(year for year, month in data.keys()), reverse=True)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    print(f"\n{title}")
    print("=" * 150)
    
    # Header row
    header = f"{'Year':<6}" + "".join(f"{month:>8}" for month in months) + f"{'Total':>10}"
    print(header)
    print("-" * 150)
    
    # Data rows
    for year in years:
        row_values = []
        row_total = 0
        for month in range(1, 13):
            key = (year, month)
            value = data.get(key, 0)
            row_values.append(value)
            row_total += value
        
        # Format values based on type
        if isinstance(next(iter(data.values())), float):
            row_str = f"{year:<6}" + "".join(f"{v:>8.1f}" if v > 0 else f"{'':>8}" for v in row_values)
            row_str += f"{row_total:>10.1f}"
        else:
            row_str = f"{year:<6}" + "".join(f"{v:>8}" if v > 0 else f"{'':>8}" for v in row_values)
            row_str += f"{row_total:>10}"
        
        print(row_str)
    
    print("=" * 150 + "\n")

def analyze_running_activities(activities):
    """Analyze running activities"""
    
    # Filter for runs only
    runs = [act for act in activities if act.get('type') == 'Run']
    
    if not runs:
        print("No running activities found.")
        return
    
    # Monthly aggregations
    monthly_count = defaultdict(int)
    monthly_distance = defaultdict(float)
    monthly_time = defaultdict(float)
    monthly_elevation = defaultdict(float)
    monthly_pace = defaultdict(float)
    monthly_hr_sum = defaultdict(float)
    monthly_hr_count = defaultdict(int)
    
    # Overall stats
    total_distance = 0
    total_time = 0
    total_elevation = 0
    longest_run = None
    fastest_pace = float('inf')
    fastest_run = None
    
    for run in runs:
        # Parse date (format: "2024-01-15T10:30:00Z")
        date_str = run['start_date']
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        year = dt.year
        month = dt.month
        key = (year, month)
        
        # Distance (meters to km)
        distance_km = run['distance'] / 1000
        monthly_distance[key] += distance_km
        total_distance += distance_km
        
        # Time (seconds to hours)
        time_hours = run['moving_time'] / 3600
        monthly_time[key] += time_hours
        total_time += time_hours
        
        # Elevation
        elevation = run.get('total_elevation_gain', 0)
        monthly_elevation[key] += elevation
        total_elevation += elevation
        
        # Count
        monthly_count[key] += 1
        
        # Heart rate (if available)
        avg_hr = run.get('average_heartrate')
        if avg_hr:
            monthly_hr_sum[key] += avg_hr
            monthly_hr_count[key] += 1
        
        # Track longest run
        if longest_run is None or distance_km > longest_run['distance'] / 1000:
            longest_run = run
        
        # Track fastest pace (only for runs > 1km)
        if distance_km > 1:
            pace = (run['moving_time'] / 60) / distance_km  # min per km
            if pace < fastest_pace:
                fastest_pace = pace
                fastest_run = run
    
    # Calculate monthly average pace
    for key in monthly_distance:
        if monthly_distance[key] > 0:
            monthly_pace[key] = (monthly_time[key] * 60) / monthly_distance[key]
    
    # Calculate monthly average heart rate
    monthly_avg_hr = {}
    for key in monthly_hr_sum:
        if monthly_hr_count[key] > 0:
            monthly_avg_hr[key] = monthly_hr_sum[key] / monthly_hr_count[key]
    
    # Print overall stats
    print("\n" + "="*80)
    print("OVERALL RUNNING STATISTICS")
    print("="*80)
    print(f"Total runs: {len(runs):,}")
    print(f"Total distance: {total_distance:,.1f} km")
    print(f"Total time: {total_time:,.1f} hours")
    print(f"Total elevation gain: {total_elevation:,.0f} m")
    print(f"Average distance per run: {total_distance / len(runs):.1f} km")
    print(f"Average pace: {(total_time * 60) / total_distance:.2f} min/km")
    print("="*80 + "\n")
    
    # Print monthly tables
    print_table(monthly_count, "MONTHLY RUN COUNT (Number of Runs)")
    print_table(monthly_distance, "MONTHLY DISTANCE (km)")
    print_table(monthly_time, "MONTHLY TIME (hours)")
    print_table(monthly_elevation, "MONTHLY ELEVATION GAIN (m)")
    print_table(monthly_pace, "MONTHLY AVERAGE PACE (min/km)")
    
    if monthly_avg_hr:
        print_table(monthly_avg_hr, "MONTHLY AVERAGE HEART RATE (bpm)")
    else:
        print("\nMONTHLY AVERAGE HEART RATE (bpm)")
        print("No heart rate data available\n")
    
    # Best performances
    print("\n" + "="*80)
    print("BEST PERFORMANCES")
    print("="*80)
    if longest_run:
        print(f"Longest run: {longest_run['distance']/1000:.1f} km on {longest_run['start_date'][:10]}")
        print(f"  Name: {longest_run.get('name', 'N/A')}")
    if fastest_run:
        print(f"Fastest pace: {fastest_pace:.2f} min/km on {fastest_run['start_date'][:10]}")
        print(f"  Name: {fastest_run.get('name', 'N/A')}")
        print(f"  Distance: {fastest_run['distance']/1000:.1f} km")
    print("="*80 + "\n")
    
    # Export to JSON
    export_data = {
        'monthly': {
            'count': {f"{y}-{m:02d}": monthly_count[(y, m)] for y, m in sorted(monthly_count.keys())},
            'distance_km': {f"{y}-{m:02d}": round(monthly_distance[(y, m)], 2) for y, m in sorted(monthly_distance.keys())},
            'time_hours': {f"{y}-{m:02d}": round(monthly_time[(y, m)], 2) for y, m in sorted(monthly_time.keys())},
            'elevation_m': {f"{y}-{m:02d}": round(monthly_elevation[(y, m)], 1) for y, m in sorted(monthly_elevation.keys())},
            'pace_min_per_km': {f"{y}-{m:02d}": round(monthly_pace[(y, m)], 2) for y, m in sorted(monthly_pace.keys()) if (y, m) in monthly_pace},
            'avg_hr_bpm': {f"{y}-{m:02d}": round(monthly_avg_hr[(y, m)], 1) for y, m in sorted(monthly_avg_hr.keys())}
        },
        'overall': {
            'total_runs': len(runs),
            'total_distance_km': round(total_distance, 2),
            'total_time_hours': round(total_time, 2),
            'total_elevation_m': round(total_elevation, 1),
            'avg_distance_per_run': round(total_distance / len(runs), 2),
            'avg_pace_min_per_km': round((total_time * 60) / total_distance, 2)
        }
    }
    
    # Write JSON file
    with open('running_data.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    print("✓ Data exported to running_data.json\n")

def main():
    print("Starting Running Analysis...\n")
    
    # Get access token
    access_token = get_access_token()
    print("✓ Access token obtained\n")
    
    # Fetch all activities
    print("Fetching activities...")
    activities = get_athlete_activities(access_token)
    print(f"✓ Fetched {len(activities)} total activities\n")
    
    # Analyze running activities
    analyze_running_activities(activities)

if __name__ == "__main__":
    main()
