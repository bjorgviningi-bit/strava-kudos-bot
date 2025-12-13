import os
import requests
from datetime import datetime, timedelta

# Strava API credentials from environment variables
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

def get_access_token():
    """Get a fresh access token using the refresh token"""
    url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload)
    return response.json()['access_token']

def get_activity_feed(access_token, page=1, per_page=30):
    """Get activities from friends (activity feed)"""
    url = 'https://www.strava.com/api/v3/activities/following'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'page': page, 'per_page': per_page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching feed: {response.status_code}")
        return []

def give_kudos(access_token, activity_id):
    """Give kudos to an activity"""
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/kudos'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(url, headers=headers)
    return response.status_code == 200

def main():
    print(f"Starting Strava Kudos Bot at {datetime.now()}")
    
    # Get access token
    try:
        access_token = get_access_token()
        print("Access token obtained")
    except Exception as e:
        print(f"Error getting access token: {e}")
        return
    
    # Get activity feed from friends
    print("Fetching activity feed...")
    activities = get_activity_feed(access_token, per_page=200)
    
    if not activities:
        print("No activities found in feed")
        return
    
    print(f"Found {len(activities)} activities in feed")
    
    # Filter activities from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    kudos_given = 0
    kudos_already_given = 0
    
    for activity in activities:
        try:
            activity_id = activity['id']
            activity_name = activity['name']
            activity_type = activity.get('type', 'Unknown')
            athlete_name = f"{activity['athlete'].get('firstname', '')} {activity['athlete'].get('lastname', '')}"
            kudos_count = activity.get('kudos_count', 0)
            has_kudoed = activity.get('athlete_kudoed', False)
            
            # Check if activity is from last 24 hours
            activity_date = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
            if activity_date < yesterday:
                continue
            
            # Skip if already gave kudos
            if has_kudoed:
                kudos_already_given += 1
                continue
            
            # Give kudos
            if give_kudos(access_token, activity_id):
                kudos_given += 1
                print(f"✓ Gave kudos to {athlete_name}: {activity_name} ({activity_type})")
            else:
                print(f"✗ Failed to give kudos to {athlete_name}: {activity_name}")
                
        except Exception as e:
            print(f"Error processing activity: {e}")
            continue
    
    print(f"\nBot finished!")
    print(f"Gave {kudos_given} new kudos")
    print(f"Skipped {kudos_already_given} activities (already gave kudos)")

if __name__ == '__main__':
    main()
