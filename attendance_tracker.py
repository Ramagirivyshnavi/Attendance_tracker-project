import pandas as pd
from datetime import datetime, timedelta
import os

# Constants
DEFAULT_START_TIME = datetime.strptime("21:00", "%H:%M").time()  # Default start time (9:00 PM)
DEFAULT_END_TIME = datetime.strptime("23:00", "%H:%M").time()  # Default end time (11:00 PM)
SESSION_DURATION = timedelta(hours=2)  # Total session duration (2 hours)

def parse_timestamp(timestamp_str):
    """Parse a timestamp string into a datetime object."""
    return datetime.strptime(timestamp_str, "%m/%d/%y, %I:%M:%S %p")

def clean_name(name):
    """Clean student names by stripping spaces and removing (Unverified)."""
    if pd.isna(name):
        return name
    return name.strip().replace("(Unverified)", "").strip()

def calculate_attendance(df):
    """Calculate attendance duration for each student."""
    attendance = {}
    for _, row in df.iterrows():
        name = row['Full Name']
        action = row['User Action']
        timestamp = parse_timestamp(row['Timestamp'])

        if name not in attendance:
            attendance[name] = {"join_times": [], "leave_times": []}

        if action == "Joined":
            attendance[name]["join_times"].append(timestamp)
        elif action == "Left":
            attendance[name]["leave_times"].append(timestamp)

    # Calculate total duration for each student
    total_durations = {}
    for name, times in attendance.items():
        join_times = times["join_times"]
        leave_times = times["leave_times"]

        total_duration = timedelta()
        for i in range(len(join_times)):
            join_time = join_times[i]
            leave_time = leave_times[i] if i < len(leave_times) else datetime.combine(join_time.date(), DEFAULT_END_TIME)

            # If the join time is before the default start time, set it to the default start time
            if join_time.time() < DEFAULT_START_TIME:
                join_time = datetime.combine(join_time.date(), DEFAULT_START_TIME)

            # If the leave time is after the default end time, set it to the default end time
            if leave_time.time() > DEFAULT_END_TIME:
                leave_time = datetime.combine(leave_time.date(), DEFAULT_END_TIME)

            total_duration += leave_time - join_time

        total_durations[name] = total_duration

    return total_durations

def update_monthly_attendance(daily_file, date):
    """Generate the monthly attendance sheet based on daily attendance data."""
    print("Starting update_monthly_attendance...")
    try:
        # Read daily attendance file with UTF-16 encoding and tab delimiter
        daily_df = pd.read_csv(daily_file, encoding='utf-16', sep='\t')
        print("Daily file read successfully.")
        
        # Clean column names (strip spaces and replace hidden characters)
        daily_df.columns = daily_df.columns.str.strip().str.replace('\xa0', ' ')
        print("Cleaned columns:", daily_df.columns.tolist())
    except UnicodeError:
        print("Error: The file is not encoded in UTF-16. Please check the file encoding.")
        return
    except Exception as e:
        print(f"Error reading the daily attendance file: {e}")
        return

    # Check if required columns exist
    required_columns = ["Full Name", "User Action", "Timestamp"]
    if not all(col in daily_df.columns for col in required_columns):
        print(f"Error: The daily attendance file must contain the following columns: {required_columns}")
        return

    # Calculate attendance durations
    print("Calculating attendance durations...")
    total_durations = calculate_attendance(daily_df)
    print("Attendance durations calculated.")

    # Create a new DataFrame for the monthly attendance
    print("Creating monthly attendance DataFrame...")
    monthly_df = pd.DataFrame(columns=["Name", date])

    # Add students to the monthly attendance sheet
    print("Adding students to the monthly attendance sheet...")
    for name, duration in total_durations.items():
        cleaned_name = clean_name(name)
        if duration >= SESSION_DURATION * 0.8:  # At least 80% attendance
            attendance_status = "Y"
        else:
            attendance_status = "N"
        # Add the student to the monthly attendance sheet
        monthly_df = pd.concat([monthly_df, pd.DataFrame({"Name": [cleaned_name], date: [attendance_status]})], ignore_index=True)

    # Save the generated monthly attendance sheet
    updated_file = f"Monthly_Attendance_{date.replace('/', '_')}.csv"
    monthly_df.to_csv(updated_file, index=False)
    print(f"Monthly attendance generated and saved to {updated_file}")

if __name__ == "__main__":
    print("Script is running...")
    
    # Define file paths and date
    daily_file = "daily_attendance1.csv"  # Path to the daily attendance file
    date = "2/8/2025"  # Date for the daily attendance (format: M/D/YYYY)

    # Check if daily file exists
    if not os.path.exists(daily_file):
        print(f"Error: Daily attendance file '{daily_file}' not found.")
    else:
        # Update monthly attendance
        update_monthly_attendance(daily_file, date)