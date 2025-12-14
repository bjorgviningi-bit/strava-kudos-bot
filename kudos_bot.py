import os
import requests
from datetime import datetime, timedelta

# Strava API credentials
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# List of club IDs to monitor
CLUB_IDS = [
    '728834',          # Your clubs
    'utadhlаupa',
    'hlaupdeloitte',
    'vectcommunity'
]

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
    # Returns True if kudos given successfully or already given (409)
    return response.status_code in [200, 201]

def get_club_activities(access_token, club_id, page=1):
    url = f'https://www.strava.com/api/v3/clubs/{club_id}/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'page': page, 'per_page': 200}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching club {club_id}: {e}")
    return []

def main():
    print(f"Starting Strava Kudos Bot at {datetime.now()}")
    print(f"Monitoring {len(CLUB_IDS)} clubs...\n")
    
    # Get access token
    try:
        access_token = get_access_token()
        print("✓ Access token obtained")
    except Exception as e:
        print(f"✗ Error getting access token: {e}")
        return
    
    # Collect all activities from clubs
    all_activities = []
    for club_id in CLUB_IDS:
        try:
            activities = get_club_activities(access_token, club_id)
            if activities:
                all_activities.extend(activities)
                print(f"✓ Club {club_id}: Found {len(activities)} activities")
            else:
                print(f"X Club {club_id}: No activities or error")
        except Exception as e:
            print(f"X Club {club_id}: Error {e}")
    
    print(f"\nTotal activities fetched: {len(all_activities)}")
    
    # Remove duplicates by activity ID
    seen = set()
    unique_activities = []
    for activity in all_activities:
            seen.add(activity.get('id'))            unique_activities.append(activity)
    
    print(f"Unique activities: {len(unique_activities)}")
    
    # Give kudos to all activities
    kudos_given = 0
    kudos_failed = 0
    
    for activity in unique_activities:
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
    print(f"Total processed: {len(unique_activities)}")

if __name__ == "__main__":
    main()