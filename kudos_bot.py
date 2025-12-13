import os
import requests
from datetime import datetime, timedelta

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

def give_kudos(access_token, activity_id):
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/kudos'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(url, headers=headers)
    return response.status_code in [200, 201]

def get_following_activities(access_token, page=1):
    # Get activities from following feed
    url = 'https://www.strava.com/api/v3/activities/following'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'page': page, 'per_page': 200}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return []

def main():
    print(f"Starting Strava Kudos Bot at {datetime.now()}")
    print("Fetching activities from following feed...\n")
    
    # Get access token
    try:
        access_token = get_access_token()
        print("✓ Access token obtained")
    except Exception as e:
        print(f"✗ Error getting access token: {e}")
        return
    
    # Get recent activities from following
    all_activities = []
    for page in range(1, 3):  # Get first 2 pages (up to 400 activities)
        try:
            activities = get_following_activities(access_token, page)
            if not activities:
                break
            all_activities.extend(activities)
            print(f"✓ Page {page}: Found {len(activities)} activities")
        except Exception as e:
            print(f"✗ Page {page}: Error {e}")
    
    print(f"\nTotal activities fetched: {len(all_activities)}")
    
    # Give kudos to all activities
    kudos_given = 0
    kudos_failed = 0
    
    for activity in all_activities:
        activity_id = activity.get('id')
        athlete_name = activity.get('athlete', {}).get('firstname', 'Unknown')
        
        if activity_id:
            if give_kudos(access_token, activity_id):
                kudos_given += 1
                print(f"✓ Gave kudos to {athlete_name} (ID: {activity_id})")
            else:
                kudos_failed += 1
    
    print(f"\n=== Summary ===")
    print(f"Kudos given: {kudos_given}")
    print(f"Failed: {kudos_failed}")
    print(f"Total processed: {len(all_activities)}")

if __name__ == "__main__":
    main()