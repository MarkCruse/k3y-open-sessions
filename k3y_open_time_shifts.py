import requests
from datetime import datetime, timedelta
import json
import logging
import argparse
from bs4 import BeautifulSoup

# USING argparse
# options:
#   -h, --help            show this help message and exit
#   --time-zone TIME_ZONE
#                         Time zone abbreviation (e.g., 'EST').
#   --area AREA           K3Y area code (e.g., 'K3Y/0').
#   --start START         Start time of the local day (e.g., '08:00').
#   --end END             End time of the local day (e.g., '22:00').
# example: python k3y_open_time_slots.py --time-zone CST --area K3Y/0 --start 08:00 --end 22:00

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        #logging.FileHandler("k3y_slots.log"), #uncomment to write to file
        logging.StreamHandler()
    ]
)

# Valid U.S. time zone abbreviations and their UTC offsets
VALID_TIME_ZONES = {
    "EST": -5, "CST": -6, "MST": -7, "PST": -8, "AKST": -9, 
    "HAST": -10, "SST": -11, "CHST": 10
}

# Command-line argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Fetch K3Y data and find available time slots.")
    
    # Optional arguments (defaults will be loaded from settings)
    parser.add_argument("--time-zone", type=str, default=None, help="Time zone abbreviation (e.g., 'EST').")
    parser.add_argument("--area", type=str, default=None, help="K3Y area code (e.g., 'K3Y/0').")
    parser.add_argument("--start", type=str, default=None, help="Start time of the local day (e.g., '08:00').")
    parser.add_argument("--end", type=str, default=None, help="End time of the local day (e.g., '22:00').")
    
    return parser.parse_args()

# Update settings based on command-line args
def update_settings_from_args(settings, args):
    if args.time_zone:
        settings["TIME_ZONE_ABBR"] = args.time_zone
    if args.area:
        settings["K3Y_AREA"] = args.area
    if args.start:
        settings["LOCAL_DAY_START"] = args.start
    if args.end:
        settings["LOCAL_DAY_END"] = args.end
    
    logging.info(f"Updated settings: {settings}")
    return settings

# Load settings from settings.json
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
    except FileNotFoundError:
        logging.info("Loading default settings - JSON file missing")
        settings = {
            'TIME_ZONE_ABBR': "EST",
            'K3Y_AREA': "K3Y/4",
            'LOCAL_DAY_START': "07:00 AM",
            'LOCAL_DAY_END': "10:00 PM"
        }
    
    logging.info("Settings loaded")
    return settings

# Convert local time to UTC using the time zone offset
def convert_to_utc(local_time_str, time_zone_abbr):
    if time_zone_abbr not in VALID_TIME_ZONES:
        raise ValueError(f"Invalid TIME_ZONE '{time_zone_abbr}'. Must be one of: {', '.join(VALID_TIME_ZONES)}")
    
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
    utc_time = utc_dt.strftime("%H:%M")  # Return time in HH:MM format
    return utc_time

# Convert UTC time to local time using the time zone offset
def convert_to_local(utc_time_str, time_zone_abbr):
    if time_zone_abbr not in VALID_TIME_ZONES:
        raise ValueError(f"Invalid TIME_ZONE '{time_zone_abbr}'. Must be one of: {', '.join(VALID_TIME_ZONES)}")
    
    try:
        utc_time = datetime.strptime(utc_time_str, "%H:%M")  # Parse UTC time
        offset = timedelta(hours=VALID_TIME_ZONES[time_zone_abbr])  # Get the time zone offset
        local_time = utc_time + offset  # Apply the offset to get local time
        local_time_str = local_time.strftime("%I:%M %p")  # Return time in 12-hour format
        return local_time_str
    except ValueError:
        return None

# Fetch K3Y data from the website using BeautifulSoup
def fetch_k3y_data(url, area):
    logging.info(f"Fetching data from website for area {area}")
    update_info = None

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        logging.info(f"Successfully fetched data from {url} for area {area}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data: {str(e)}")
        return [], None

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the update information - look for <em> tags
    em_tags = soup.find_all('em')
    for em in em_tags:
        if '(Update:' in em.text:
            update_text = em.text.strip()
            update_text = update_text.replace('(Update:', '').replace(')', '').strip()
            update_info = update_text
            break
            
    # Alternative: look for text containing '(Update:' if not found in <em> tags
    if not update_info:
        for element in soup.find_all(text=True):
            if '(Update:' in element:
                update_text = em.text.strip()
                update_text = update_text.replace('(Update:', '').replace(')', '').strip()
                update_info = update_text
                break
    
    # Find the table in the page
    table = soup.find('table')
    rows = []
    
    if table:
        # Skip the header row and get all data rows
        data_rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in data_rows:
            cells = row.find_all('td')
            
            if len(cells) >= 4:
                date = cells[0].text.strip()
                start_time = cells[1].text.strip()
                end_time = cells[2].text.strip()
                k3y_area = cells[3].text.strip()
                
                if area in k3y_area:
                    rows.append((date, start_time, end_time, k3y_area))
    
    logging.info(f"Found {len(rows)} slots for {area}")
    return rows, update_info

# Fetch K3Y data from Github
def fetch_k3y_data_new(area):
    logging.info(f"Fetching data from Github for area {area}")
    update_info = None

    GITHUB_SCHEDULE_URL = (
        "https://raw.githubusercontent.com/MarkCruse/"
        "k3y-schedule-updater/main/data/schedule-cache.json"
    )

    resp = requests.get(GITHUB_SCHEDULE_URL, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("schedule-cache.json must contain a list")

    rows = [
        (
            d["session_date"],
            d["utc_start"],
            d["utc_end"],
            d["k3y_area"],
        )
        for d in data
    ]
    #print(rows)

    logging.info(f"Found {len(rows)} slots for {area}")
    return rows, update_info


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
def find_gaps(data, required_ranges, time_zone_abbr, area):
    # Initialize a dictionary to track scheduled hours by date
    daily_hours = {}

    # Update daily hours with scheduled slots
    for date, start, end, k3y_area in data:
        if area in k3y_area:  # Filter by the selected area
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
                    gap_start_local = convert_to_local(hour, time_zone_abbr)  # Convert to local time
                    gap_end_local = convert_to_local(end_time.strftime("%H:%M"), time_zone_abbr)  # Convert to local time

                    gap_label = f"Open Slot ({time_zone_abbr})"
                    gaps.append({
                        "Date": f"{date}",
                        "Open Slot (UTC)": f"{hour} - {end_time.strftime('%H:%M')} UTC",
                        gap_label: f"{gap_start_local} - {gap_end_local}"
                    })
    
    logging.info(f"Found {len(gaps)} open slots for area {area}")
    #logging.info(gaps[0])
    # Sort gaps by date and time
    gaps.sort(key=lambda x: (x['Date'], datetime.strptime(x['Open Slot (UTC)'].split(' ')[0], "%H:%M")))
    return gaps

# Main function to fetch data, find gaps, and display results
def get_open_slots(area, time_zone_abbr, local_day_start, local_day_end, url='https://www.skccgroup.com/k3y/slot_list.php'):
    data, update_info = fetch_k3y_data(url, area)  # Fetch K3Y data from the website
    required_ranges = [(convert_to_utc(local_day_start, time_zone_abbr), 
                       convert_to_utc(local_day_end, time_zone_abbr))]  # Required time range in UTC
    gaps = find_gaps(data, required_ranges, time_zone_abbr, area)  # Find gaps in the data
    return gaps, update_info

# Main function to fetch data, find gaps, and display results
def get_open_slots_new(area, time_zone_abbr, local_day_start, local_day_end, url='https://www.skccgroup.com/k3y/slot_list.php'):
    #data, update_info = fetch_k3y_data(url, area)  # Fetch K3Y data from the website
    data, update_info = fetch_k3y_data_new(area)  # Fetch K3Y data from the website
    required_ranges = [(convert_to_utc(local_day_start, time_zone_abbr), 
                       convert_to_utc(local_day_end, time_zone_abbr))]  # Required time range in UTC
    gaps = find_gaps(data, required_ranges, time_zone_abbr, area)  # Find gaps in the data
    return gaps, update_info

# Main function to_new(area, time_zone_abbr, local_day_start, local_day_end, url='https://www.skccgroup.com/k3y/slot_list.php'):
    # data, update_info = fetch_k3y_data(url, area)  # Fetch K3Y data from the website
    # required_ranges = [(convert_to_utc(local_day_start, time_zone_abbr), 
    #                    convert_to_utc(local_day_end, time_zone_abbr))]  # Required time range in UTC
    # gaps = find_gaps(data, required_ranges, time_zone_abbr, area)  # Find gaps in the data
    # return gaps, update_info
    data, update_info = fetch_k3y_data_new(area)  # Fetch K3Y data from the website
    required_ranges = [(convert_to_utc(local_day_start, time_zone_abbr), 
                       convert_to_utc(local_day_end, time_zone_abbr))]  # Required time range in UTC
    gaps = find_gaps(data, required_ranges, time_zone_abbr, area)  # Find gaps in the data
    return gaps, update_info

# Command-line interface
if __name__ == "__main__":
    args = parse_args()  # Parse command-line arguments

    # Only log command-line arguments if they are provided
    if any([args.time_zone, args.area, args.start, args.end]):
        logging.info(f"Command-line arguments: {args}")
    
    settings = load_settings()  # Load default settings from JSON
    
    # Update settings with command-line args (if provided)
    settings = update_settings_from_args(settings, args)

    gaps, update_info = get_open_slots(
        settings['K3Y_AREA'],
        settings['TIME_ZONE_ABBR'],
        settings['LOCAL_DAY_START'],
        settings['LOCAL_DAY_END']
    )
    
    # Print update information if available
    if update_info:
        print(f"\nSKCC OP Schedule last update: {update_info} \n\nOpen Slots for area {settings['K3Y_AREA']}")
    
    # Print results
    if gaps:
        print(f"\n{'Date'}\t {'Open Slot (UTC)'}\t  {'Open Slot ({})'.format(settings['TIME_ZONE_ABBR'])}")
        previous_date = None
        for gap in gaps:
            if gap['Date'] != previous_date:
                if previous_date is not None:
                    print()
                previous_date = gap['Date']
            print(f"{gap['Date']}\t {gap['Open Slot (UTC)']}\t  {gap[f'Open Slot ({settings['TIME_ZONE_ABBR']})']}")
    else:
        print("\nNo open slots found for the specified time range.")
    print('\n')
    logging.info(f"Completed processing for area {settings['K3Y_AREA']}")
      