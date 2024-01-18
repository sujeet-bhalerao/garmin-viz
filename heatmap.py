import os
import pandas as pd
import gmplot
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from datetime import datetime, timedelta


email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")


token_file = os.path.expanduser("~/.garmin-tokens")
if os.path.isfile(token_file):
    print("Using existing Garmin tokens.")
else:
    if not email or not password:
        raise ValueError("Please set EMAIL and PASSWORD environment variables.")
    print("No Garmin tokens found. Authenticating...")


try:
    garmin_client = Garmin(email, password)
    garmin_client.login()
except (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
) as e:
    print(f"Error occurred during Garmin Connect Client init: {e}")
    raise SystemExit

# Define date range to fetch activities
end_date = datetime.now()
start_date = end_date - timedelta(days=90)  # last 90 days


activities = garmin_client.get_activities_by_date(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), "")
print(f"Fetched {len(activities)} activities from Garmin Connect.")


all_act = []
for activity in activities:
    activity_id = activity["activityId"]
    details = garmin_client.get_activity_details(activity_id)
    
    if 'geoPolylineDTO' in details and details['geoPolylineDTO']:
        polyline_data = details['geoPolylineDTO'].get('polyline')
        if polyline_data:
            print(f"Found polyline for activity {activity_id}")
            # Extract lat/longitude from polyline data
            latlngs = [(point['lat'], point['lon']) for point in polyline_data if 'lat' in point and 'lon' in point]
            if latlngs:
                df = pd.DataFrame(latlngs, columns=['lat', 'lon'])
                all_act.append(df)

if all_act:
    combined_df = pd.concat(all_act, ignore_index=True)
    gmap = gmplot.GoogleMapPlotter(combined_df['lat'].mean(), combined_df['lon'].mean(), 13, apikey='your_api_key')
    gmap.heatmap(combined_df['lat'], combined_df['lon'], radius=20)
    gmap.draw("garmin_heatmap.html")
    print("Heatmap saved as 'garmin_heatmap.html'.")
else:
    print("No data available to create heatmap.")



