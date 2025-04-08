# K3Y Open Slot Finder

## Project Description

The K3Y Open Slot Finder helps amateur radio operators track available time slots during the [SKCC Straight Key Month](https://www.skccgroup.com/k3y/k3y.php) event.  
The app allows users to select a specific area, time zone, and displays available open slots within a user-defined time range. The app is designed to make it easy to find available slots for the K3Y event, which can be filtered and saved for later use.

## Features

- **Time Zone Selection**: Choose the appropriate time zone.
- **Select K3Y Area**: Filter available slots based on the selected K3Y area.
- **View Available Time Slots**: Check open slots in the event schedule.
- **Download Available Slots**: Export available time slots to a CSV file.
- **Save Settings**: Save the time zone, K3Y area, and start/end time preferences for future use.

## File Analysis

### k3y_open_time_slots.py  
This is the core logic file that:  

- Loads settings from a settings.json file
- Converts between UTC and local time zones
- Fetches K3Y slot data from the SKCC website
- Identifies open time slots based on user preferences

### dashboard.py
This is the Streamlit interface that:

- Provides a user-friendly web UI for the slot finder
- Allows users to select time zones, K3Y areas, and preferred hours
- Displays available slots in a table
- Offers CSV export and clipboard copying features

### Key Features:

- Settings sidebar with configuration options
- Data caching to reduce web scraping frequency
- Editable data table to select desired slots
- Export functionality for sharing selected slots

## Installation

To get started with K3Y Open Slot Finder, follow these steps:

1. Clone this repository:
   ```bash
   git clone https://github.com/MarkCruse/k3y-open-sessions.git
   cd k3y-open-sessions
2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install streamlit requests
   ```
4. Save the New Environment
   ```bash
   pip freeze > requirements.txt
   ```  
5. Run as app:
   ```bash
   streamlit run dashboard.py
   ```
6. Run locally at command prompt:
   ```bash
   python k3y_open_time_slots.py
   ```
7. Run locally at command prompt with parameters:
   ```bash
   python k3y_open_time_slots.py --time-zone CST --area K3Y/0 --start 08:00 --end 22:00
   ```
    **options for command line parameters**:  
      -h, --help              show this help message and exit  
      --time-zone TIME_ZONE   Time zone abbreviation (e.g., 'EST','CST','PST'...)   
      --area AREA           K3Y area code (e.g., 'K3Y/0')  
      --start START         Start time of the local day (e.g., '08:00')  
      --end END             End time of the local day (e.g., '22:00')  

## Usage

**Select Time Zone**: In the sidebar, choose your desired time zone from the list.

**Select K3Y Area**: Choose the K3Y area you want to filter available slots by.

**Set Time Range**: Define the start and end times (in local time) for your search.

**View Open Slots**: The available open slots will be displayed in a table.

**Download CSV**: Download the results by clicking on the "📥 Download CSV" button.

**Save Settings**: You can save your preferences (selected time zone, K3Y area, start/end times) for future use by clicking the "Save Settings" button.

## Configuration File
The settings are saved in settings.json. This file includes preferences such as the selected time zone, K3Y area, and start/end times for the day. You can modify the file directly if needed.

Here’s an example of the settings.json file:

   ```json
   {
       "TIME_ZONE_ABBR": "CST",
       "K3Y_AREA": "K3Y/0",
       "LOCAL_DAY_START": "08:00",
       "LOCAL_DAY_END": "22:00"
   }
```

## Requirements
- Streamlit
- Requests

## License
This project is licensed under the MIT License - see the LICENSE file for details.
