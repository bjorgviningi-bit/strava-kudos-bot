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

def analyze_running_activities(activities):
    """Analyze running activities"""
    running_activities = [a for a in activities if a['type'] == 'Run']
    
    if not running_activities:
        print("No running activities found.")
        return
    
    # Calculate statistics
    total_runs = len(running_activities)
    total_distance = sum(a['distance'] for a in running_activities) / 1000  # Convert to km
    total_time = sum(a['moving_time'] for a in running_activities) / 3600  # Convert to hours
    total_elevation = sum(a.get('total_elevation_gain', 0) for a in running_activities)
    
    # Average pace (min/km)
    avg_pace = (total_time * 60) / total_distance if total_distance > 0 else 0
    
    # Monthly breakdown
    monthly_stats = defaultdict(lambda: {'count': 0, 'distance': 0, 'time': 0})
    
    for activity in running_activities:
        date = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
        month_key = date.strftime('%Y-%m')
        
        monthly_stats[month_key]['count'] += 1
        monthly_stats[month_key]['distance'] += activity['distance'] / 1000
        monthly_stats[month_key]['time'] += activity['moving_time'] / 3600
    
    # Print overall statistics
    print("\n" + "="*50)
    print("RUNNING STATISTICS")
    print("="*50)
    print(f"Total Runs: {total_runs}")
    print(f"Total Distance: {total_distance:.2f} km")
    print(f"Total Time: {total_time:.2f} hours")
    print(f"Total Elevation Gain: {total_elevation:.2f} m")
    print(f"Average Pace: {avg_pace:.2f} min/km")
    print(f"Average Distance per Run: {total_distance/total_runs:.2f} km")
    
    # Print monthly breakdown
    print("\n" + "="*50)
    print("MONTHLY BREAKDOWN")
    print("="*50)
    
    for month in sorted(monthly_stats.keys(), reverse=True):
        stats = monthly_stats[month]
        avg_pace_month = (stats['time'] * 60) / stats['distance'] if stats['distance'] > 0 else 0
        print(f"\n{month}:")
        print(f"  Runs: {stats['count']}")
        print(f"  Distance: {stats['distance']:.2f} km")
        print(f"  Time: {stats['time']:.2f} hours")
        print(f"  Avg Pace: {avg_pace_month:.2f} min/km")
    
    # Find best performances
    print("\n" + "="*50)
    print("BEST PERFORMANCES")
    print("="*50)
    
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
        
        print("\n" + "="*50)
        print("Analysis complete!")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
