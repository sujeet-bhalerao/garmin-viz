import calmap
import matplotlib.pyplot as plt
import pandas as pd
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)
from datetime import date, timedelta
import os


TOKEN_STORE = "~/.garminconnect"

def init_api():
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    token_store_path = os.path.expanduser(TOKEN_STORE)
    
    try:
        garmin = Garmin()
        garmin.login(token_store_path)
    except (GarminConnectAuthenticationError, FileNotFoundError):
        if not email or not password:
            raise ValueError("Set EMAIL and PASSWORD environment variables.")
        garmin = Garmin(email, password)
        garmin.login()
        garmin.garth.dump(token_store_path)
    
    return garmin


def fetch_activities(garmin, start_date, end_date):
    activities = garmin.get_activities_by_date(start_date.isoformat(), end_date.isoformat())
    return activities


def process_activities(activities):
    processed_data = []
    missing_distance_count = 0
    for activity in activities:
        activity_date = activity["startTimeLocal"]
        distance = activity["distance"]
        activity_type = activity["activityType"]["typeKey"]  
        if pd.isnull(distance):
            missing_distance_count += 1
            print(f"Missing distance for activity type: {activity_type} on {activity_date}")
        processed_data.append({"Activity Date": activity_date, "Distance": distance, "Activity Type": activity_type})
    print(f"Total activities with missing distance: {missing_distance_count}")
    return pd.DataFrame(processed_data)


# plot calendar heatmap
def plot_calendar(activities, year_min=None, year_max=None, max_dist=None, fig_height=15, fig_width=9, output_file="calendar.png"):
    plt.figure()
    activities["Activity Date"] = pd.to_datetime(activities["Activity Date"])
    activities["date"] = activities["Activity Date"].dt.date
    activities = activities.groupby(["date"])["Distance"].sum()
    activities.index = pd.to_datetime(activities.index)
    if max_dist:
        activities.clip(0, max_dist, inplace=True)
    if year_min:
        activities = activities[activities.index.year >= year_min]
    if year_max:
        activities = activities[activities.index.year <= year_max]
    colormap = plt.cm.YlGnBu
    fig, ax = calmap.calendarplot(data=activities, cmap=colormap)
    fig.set_figheight(fig_height)
    fig.set_figwidth(fig_width)
    fig.savefig(output_file, dpi=600)

def main():
    garmin = init_api()
    today = date.today()
    end_date = today
    start_date = end_date - timedelta(days=30)
    #start_date = date(today.year-1, today.month, today.day)  # uncomment to start from a year ago


    try:
        activities = fetch_activities(garmin, start_date, end_date)
        print("Fetched activities data")
    except (GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarminConnectAuthenticationError) as e:
        print(f"Error fetching activities: {e}")
        return

    activities_df = process_activities(activities)
    print("Processed activities data")
    print(activities_df)

    plot_calendar(activities_df, year_min=start_date.year, year_max=end_date.year)
    print(f"Calendar heatmap saved to calendar.png")

if __name__ == "__main__":
    main()
