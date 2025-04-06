import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Load settings from settings.ini
def load_settings():
    settings = {}
    with open('ham_radio/settings.ini', 'r') as file:
        exec(file.read(), settings)
    return settings

# Load configuration
settings = load_settings()

# Extract values from the loaded settings
K3Y_AREA = settings['K3Y_AREA']
TIME_ZONE_ABBR = settings['TIME_ZONE_ABBR']
LOCAL_DAY_START = settings['LOCAL_DAY_START']
LOCAL_DAY_END = settings['LOCAL_DAY_END']

# URL and area for K3Y data
URL = 'https://www.skccgroup.com/k3y/slot_list.php'

#K3Y_AREA = 'K3Y/9'
# Time zone settings
#TIME_ZONE_ABBR = "CST"  # Change as needed
#LOCAL_DAY_START = "07:00"  # Local start of desired time range
#LOCAL_DAY_END = "23:00"    # Local end of desired time range

# Valid U.S. time zone abbreviations and their UTC offsets
VALID_TIME_ZONES = {
    "EST": -5, "CST": -6, "MST": -7, "PST": -8, "AKST": -9, 
    "HAST": -10, "SST": -11, "CHST": 10
}

# Validate the time zone abbreviation provided by the user
if TIME_ZONE_ABBR not in VALID_TIME_ZONES:
    raise ValueError(f"Invalid TIME_ZONE '{TIME_ZONE_ABBR}'. Must be one of: {', '.join(VALID_TIME_ZONES)}")

# Convert local time to UTC using the time zone offset
def convert_to_utc(local_time_str, time_zone_abbr):
    today = datetime.now()  # Get today's date
    local_hour, local_minute = map(int, local_time_str.split(":"))  # Parse the local time

    # Get the time zone offset
    offset = timedelta(hours=VALID_TIME_ZONES[time_zone_abbr])
    
    # Create the local datetime object
    local_dt = datetime(
        year=today.year, month=today.month, day=today.day,
        hour=local_hour, minute=local_minute
    )

    # Convert to UTC by subtracting the offset
    utc_dt = local_dt - offset
    return utc_dt.strftime("%H:%M")  # Return time in HH:MM format

# Convert UTC time to local time using the time zone offset
def convert_to_local(utc_time_str, time_zone_abbr):
    try:
        utc_time = datetime.strptime(utc_time_str, "%H:%M")  # Parse UTC time
        offset = timedelta(hours=VALID_TIME_ZONES[time_zone_abbr])  # Get the time zone offset
        local_time = utc_time + offset  # Apply the offset to get local time
        return local_time.strftime("%I:%M %p")  # Return time in 12-hour format
    except ValueError:
        return None

# Fetch K3Y data from the website and parse the table
def fetch_k3y_data(url, area):
    response = requests.get(url)  # Send a request to fetch the page
    soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content
    table = soup.find('table')  # Find the table containing the slots
    data = []

    # Parse each row in the table, starting from the second row (skip header)
    if table:
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 4:
                date = cells[0].text.strip().upper()  # Extract date
                start_time = cells[1].text.strip().upper()  # Extract start time
                end_time = cells[2].text.strip().upper()  # Extract end time
                k3y_area = cells[3].text.strip().upper()  # Extract area

                # Only keep rows that match the desired K3Y area
                if area in k3y_area:
                    data.append((date, start_time, end_time))
    return data

# Generate a list of full hour time slots between start_time and end_time
def generate_hours(start_time, end_time):
    start = datetime.strptime(start_time, "%H:%M")  # Convert start time to datetime object
    end = datetime.strptime(end_time, "%H:%M")  # Convert end time to datetime object
    hours = []

    # If the end time is earlier than the start time, adjust to span the next day
    if end < start:
        end += timedelta(days=1)

    # Generate hourly slots
    current = start
    while current < end:
        hours.append(current.strftime("%H:00"))  # Append each full hour
        current += timedelta(hours=1)

    return hours

# Find gaps between scheduled times based on required ranges
def find_gaps(data, required_ranges):
    # Initialize a dictionary to track scheduled hours by date
    daily_hours = {}

    # Update daily hours with scheduled slots
    for date, start, end in data:
        if date not in daily_hours:
            daily_hours[date] = set()
        hours = generate_hours(start, end)  # Generate blocked hours
        daily_hours[date].update(hours)

    gaps = []

    # Iterate over each date and find open slots
    for date, scheduled_hours in daily_hours.items():
        full_day_schedule = set(generate_hours("00:00", "23:00"))  # Full 24-hour schedule
        open_slots = full_day_schedule - scheduled_hours  # Find open slots

        # Check if open slots overlap with required ranges
        for start, end in required_ranges:
            for hour in generate_hours(start, end):
                if hour in open_slots:
                    start_time = datetime.strptime(hour, "%H:%M")
                    end_time = start_time + timedelta(hours=1)  # Calculate end time
                    gap_start_local = convert_to_local(hour, TIME_ZONE_ABBR)  # Convert to local time
                    gap_end_local = convert_to_local(end_time.strftime("%H:%M"), TIME_ZONE_ABBR)  # Convert to local time

                    gap_label = f"Open Slot ({TIME_ZONE_ABBR})"
                    gaps.append({
                        "Date": f"{date}",
                        "Open Slot (UTC)": f"{hour} - {end_time.strftime('%H:%M')} UTC",
                        gap_label: f"{gap_start_local} - {gap_end_local}"
                    })

    return gaps

# Main function to fetch data, find gaps, and display results
def main():
    data = fetch_k3y_data(URL, K3Y_AREA)  # Fetch K3Y data from the website
    required_ranges = [(convert_to_utc(LOCAL_DAY_START, TIME_ZONE_ABBR), 
                        convert_to_utc(LOCAL_DAY_END, TIME_ZONE_ABBR))]  # Required time range in UTC
    gaps = find_gaps(data, required_ranges)  # Find gaps in the data

    # Sort the gaps by date and UTC time
    gaps.sort(key=lambda x: (x['Date'], datetime.strptime(x['Open Slot (UTC)'].split(' ')[0], "%H:%M")))

    # Print results
    if gaps:
        print(f"{'Date'}\t {'Open Slot (UTC)'}\t  {'Open Slot ({})'.format(TIME_ZONE_ABBR)}")
        previous_date = None
        for gap in gaps:
            if gap['Date'] != previous_date:
                if previous_date is not None:
                    print()
                previous_date = gap['Date']
            print(f"{gap['Date']}\t {gap['Open Slot (UTC)']}\t  {gap[f'Open Slot ({TIME_ZONE_ABBR})']}")

# Run the main function
if __name__ == "__main__":
    main()
