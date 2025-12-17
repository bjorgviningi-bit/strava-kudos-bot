import os
import requests
from datetime import datetime
from collections import defaultdict

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
        page += 1
        
    return activities

def print_table(data, title):
    """Print a formatted table"""
    print(f"\n{title}")
    print("=" * 160)
    
    # Get all years and months
    years = sorted(set(year for year, month in data.keys()), reverse=True)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Print header
    print(f"{'Year':<8}", end="")
    for month in months:
        print(f"{month:>10}", end="")
    print(f"{'Total':>12}")
    print("-" * 160)
    
    # Print data for each year
    for year in years:
        print(f"{year:<8}", end="")
        year_total = 0
        
        for month_num in range(1, 13):
            key = (year, month_num)
            value = data.get(key, 0)
            year_total += value
            
            if value == 0:
                print(f"{'':>10}", end="")
            else:
                if isinstance(value, float):
                    print(f"{value:>10.1f}", end="")
                else:
                    print(f"{value:>10}", end="")
        
        if isinstance(year_total, float):
            print(f"{year_total:>12.1f}")
        else:
            print(f"{year_total:>12}")
    
    print("=" * 160)

def analyze_running_activities(activities):
    """Analyze running activities with tables"""
    running_activities = [a for a in activities if a['type'] == 'Run']
    
    if not running_activities:
        print("No running activities found.")
        return
    
    # Calculate statistics by year and month
    monthly_count = {}
    monthly_distance = {}
    monthly_time = {}
    monthly_elevation = {}
    monthly_pace = {}
    
    for activity in running_activities:
        date = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
        key = (date.year, date.month)
        
        distance_km = activity['distance'] / 1000
        time_hours = activity['moving_time'] / 3600
        elevation = activity.get('total_elevation_gain', 0)
        
        # Count
        monthly_count[key] = monthly_count.get(key, 0) + 1
        
        # Distance
        monthly_distance[key] = monthly_distance.get(key, 0) + distance_km
        
        # Time
        monthly_time[key] = monthly_time.get(key, 0) + time_hours
        
        # Elevation
        monthly_elevation[key] = monthly_elevation.get(key, 0) + elevation
    
    # Calculate average pace for each month
    for key in monthly_distance:
        if monthly_distance[key] > 0:
            pace = (monthly_time[key] * 60) / monthly_distance[key]
            monthly_pace[key] = pace
    
    # Print overall statistics
    total_runs = len(running_activities)
    total_distance = sum(a['distance'] for a in running_activities) / 1000
    total_time = sum(a['moving_time'] for a in running_activities) / 3600
    total_elevation = sum(a.get('total_elevation_gain', 0) for a in running_activities)
    avg_pace = (total_time * 60) / total_distance if total_distance > 0 else 0
    
    print("\n" + "="*80)
    print("OVERALL RUNNING STATISTICS")
    print("="*80)
    print(f"Total Runs: {total_runs}")
    print(f"Total Distance: {total_distance:.2f} km")
    print(f"Total Time: {total_time:.2f} hours")
    print(f"Total Elevation Gain: {total_elevation:.2f} m")
    print(f"Average Pace: {avg_pace:.2f} min/km")
    print(f"Average Distance per Run: {total_distance/total_runs:.2f} km")
    
    # Print tables
    print("\n")
    print_table(monthly_count, "MONTHLY RUN COUNT (Number of Runs)")
    print("\n")
    print_table(monthly_distance, "MONTHLY DISTANCE (km)")
    print("\n")
    print_table(monthly_time, "MONTHLY TIME (hours)")
    print("\n")
    print_table(monthly_elevation, "MONTHLY ELEVATION GAIN (m)")
    print("\n")
    print_table(monthly_pace, "MONTHLY AVERAGE PACE (min/km)")
    
    # Find best performances
    print("\n" + "="*80)
    print("BEST PERFORMANCES")
    print("="*80)
    
    # Longest run
    longest_run = max(running_activities, key=lambda x: x['distance'])
    print(f"\nLongest Run: {longest_run['distance']/1000:.2f} km")
    print(f"  Date: {longest_run['start_date'][:10]}")
    print(f"  Name: {longest_run['name']}")
    
    # Fastest pace (for runs > 1km)
    long_runs = [a for a in running_activities if a['distance'] > 1000]
    if long_runs:
        fastest_run = min(long_runs, key=lambda x: (x['moving_time']/60) / (x['distance']/1000))
        fastest_pace = (fastest_run['moving_time']/60) / (fastest_run['distance']/1000)
        print(f"\nFastest Pace: {fastest_pace:.2f} min/km")
        print(f"  Date: {fastest_run['start_date'][:10]}")
        print(f"  Name: {fastest_run['name']}")
        print(f"  Distance: {fastest_run['distance']/1000:.2f} km")
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    print("Starting Running Analysis...")
    
    try:
        # Get access token
        access_token = get_access_token()
        print("✓ Access token obtained")
        
        # Fetch all activities
        print("Fetching activities...")
        activities = get_athlete_activities(access_token)
        print(f"✓ Fetched {len(activities)} total activities")
        
        # Analyze running activities
        analyze_running_activities(activities)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
