import os
import requests
from datetime import datetime, timedelta

# Strava API credentials from environment variables
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# Club IDs to monitor
CLUB_IDS = [
    'utadhlaupa',       # Útihlaup
    '728834',           # Club 728834  
    'hlaupdeloitte',    # Hlaup Deloitte
    'vecctcommunity',   # VECCT Community
    '186819',           # Club 186819
    '168720'            # Club 168720
]def get_access_token():
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
    return response.status_code in [200, 201]

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
        try:
            activities = get_club_activities(access_token, club_id, per_page=100)
            
            if activities:
                print(f"  Found {len(activities)} activities")
                # Add to list, avoiding duplicates
                for activity in activities:
                    # Club activities have different structure - activity_id instead of id
                    act_id = activity.get('activity_id') or activity.get('id')
                    if act_id and act_id not in seen_activity_ids:
                        all_activities.append(activity)
                        seen_activity_ids.add(act_id)
            else:
                print(f"  No activities found")
        except Exception as e:
            print(f"  Error fetching club {club_id}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Total unique activities found: {len(all_activities)}")
    print(f"{'='*60}\n")
    
    if not all_activities:
        print("No activities to process")
        return
    
    # Filter activities from last 24 hours and give kudos
    yesterday = datetime.now() - timedelta(days=1)
    
    kudos_given = 0
    kudos_skipped = 0
    errors = 0
    
    for activity in all_activities:
        try:
            # Get activity ID - club activities use 'activity_id'
            activity_id = activity.get('activity_id') or activity.get('id')
            if not activity_id:
                continue
            
            # Get activity details
            activity_name = activity.get('name', 'Unnamed Activity')
            activity_type = activity.get('type', 'Unknown')
            
            # Get athlete info
            athlete = activity.get('athlete', {})
            athlete_firstname = athlete.get('firstname', '')
            athlete_lastname = athlete.get('lastname', '')
            athlete_name = f"{athlete_firstname} {athlete_lastname}".strip() or 'Unknown Athlete'
            
            # Check if activity is from last 24 hours
            # Try different date field names
            activity_date_str = None
            for date_field in ['start_date', 'activity_date', 'date']:
                if date_field in activity:
                    activity_date_str = activity[date_field]
                    break
            
            if not activity_date_str:
                # Skip if no date found
                continue
            
            # Parse date (handle both formats)
            try:
                if 'T' in activity_date_str:
                    activity_date = datetime.strptime(activity_date_str[:19], '%Y-%m-%dT%H:%M:%S')
                else:
                    activity_date = datetime.strptime(activity_date_str[:10], '%Y-%m-%d')
            except:
                continue
            
            if activity_date < yesterday:
                continue
            
            # Give kudos
            if give_kudos(access_token, activity_id):
                kudos_given += 1
                print(f"✓ Gave kudos to {athlete_name}: {activity_name} ({activity_type})")
            else:
                kudos_skipped += 1
                
        except Exception as e:
            errors += 1
            if errors <= 3:  # Only print first 3 errors to avoid spam
                print(f"✗ Error processing activity: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Bot finished!")
    print(f"Gave {kudos_given} new kudos")
    print(f"Skipped {kudos_skipped} activities")
    if errors > 0:
        print(f"Encountered {errors} errors")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
