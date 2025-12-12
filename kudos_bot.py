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

def get_athlete_activities(access_token, athlete_id, after_timestamp):
    """Get activities for a specific athlete"""
    url = f'https://www.strava.com/api/v3/athletes/{athlete_id}/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'after': after_timestamp, 'per_page': 30}
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else []

def get_followers(access_token):
    """Get list of followers"""
    url = 'https://www.strava.com/api/v3/athlete/followers'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 200}
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else []

def give_kudos(access_token, activity_id):
    """Give kudos to an activity"""
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/kudos'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(url, headers=headers)
    return response.status_code == 200

def main():
    print(f"Starting Strava Kudos Bot at {datetime.now()}")
    
    # Get access token
    access_token = get_access_token()
    print("Access token obtained")
    
    # Get followers
    followers = get_followers(access_token)
    print(f"Found {len(followers)} followers")
    
    # Get activities from the last 24 hours
    yesterday = int((datetime.now() - timedelta(days=1)).timestamp())
    
    kudos_given = 0
    for follower in followers:
        follower_id = follower['id']
        follower_name = f"{follower.get('firstname', '')} {follower.get('lastname', '')}"
        
        # Get follower's activities
        activities = get_athlete_activities(access_token, follower_id, yesterday)
        
        for activity in activities:
            activity_id = activity['id']
            activity_name = activity['name']
            kudos_count = activity.get('kudos_count', 0)
            
            # Give kudos if the activity has 0 kudos
            if kudos_count == 0:
                if give_kudos(access_token, activity_id):
                    kudos_given += 1
                    print(f"✓ Gave kudos to {follower_name}: {activity_name}")
                else:
                    print(f"✗ Failed to give kudos to {follower_name}: {activity_name}")
    
    print(f"\nBot finished! Gave {kudos_given} kudos total")

if __name__ == '__main__':
    main()
