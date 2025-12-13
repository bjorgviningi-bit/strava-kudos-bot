import os
import requests
from datetime import datetime, timedelta

# Strava API credentials from environment variables
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# Club IDs to monitor
CLUB_IDS = [
    'utadhlaupa',      # Útihlaup
    '728834',          # Club 728834  
    'hlaupdeloitte'    # Hlaup Deloitte
]

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

def get_club_activities(access_token, club_id, per_page=30):
    """Get recent activities from a club"""
    url = f'https://www.strava.com/api/v3/clubs/{club_id}/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': per_page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching activities for club {club_id}: {response.status_code}")
        return []

def give_kudos(access_token, activity_id):
    """Give kudos to an activity"""
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/kudos'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(url, headers=headers)
    return response.status_code == 200

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
    
    # Track activities across all clubs
    all_activities = []
    seen_activity_ids = set()
    
    # Fetch activities from each club
    for club_id in CLUB_IDS:
        print(f"\nFetching activities from club: {club_id}")
        activities = get_club_activities(access_token, club_id, per_page=100)
        
        if activities:
            print(f"  Found {len(activities)} activities")
            # Add to list, avoiding duplicates
            for activity in activities:
                if activity['id'] not in seen_activity_ids:
                    all_activities.append(activity)
                    seen_activity_ids.add(activity['id'])
        else:
            print(f"  No activities found")
    
    print(f"\n{'='*60}")
    print(f"Total unique activities found: {len(all_activities)}")
    print(f"{'='*60}\n")
    
    if not all_activities:
        print("No activities to process")
        return
    
    # Filter activities from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    kudos_given = 0
    kudos_already_given = 0
    
    for activity in all_activities:
        try:
            activity_id = activity.get('id')
            activity_name = activity.get('name', 'Unnamed Activity')
            activity_type = activity.get('type', 'Unknown')
            
            # Get athlete info
            athlete = activity.get('athlete', {})
            athlete_firstname = athlete.get('firstname', '')
            athlete_lastname = athlete.get('lastname', '')
            athlete_name = f"{athlete_firstname} {athlete_lastname}".strip()
            
            # Check if activity is from last 24 hours
            # Club activities use 'activity_date' instead of 'start_date'
            activity_date_str = activity.get('start_date') or activity.get('activity_date')
            if not activity_date_str:
                continue
                
            activity_date = datetime.strptime(activity_date_str[:19], '%Y-%m-%dT%H:%M:%S')
            if activity_date < yesterday:
                continue
            
            # Give kudos
            if give_kudos(access_token, activity_id):
                kudos_given += 1
                print(f"✓ Gave kudos to {athlete_name}: {activity_name} ({activity_type})")
            else:
                # Most likely already gave kudos
                kudos_already_given += 1
                
        except Exception as e:
            print(f"✗ Error processing activity: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Bot finished!")
    print(f"Gave {kudos_given} new kudos")
    print(f"Skipped {kudos_already_given} activities (likely already gave kudos)")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
