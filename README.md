# K3Y Open Slot Finder

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-brightgreen?logo=streamlit)](https://k3y-open-sessions.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/MarkCruse/k3y-open-sessions/issues)



## Project Description

The K3Y Open Slot Finder is a tool for SKCC K3Y operators to easily identify available time slots during the [SKCC Straight Key Month](https://www.skccgroup.com/k3y/k3y.php) event.  

K3Y operators can select a region, adjust for their local time zone, and view open operating slots within a custom time window—making it simple to find and request times to participate.

## Live Demo

You can try the app instantly using the **Streamlit Cloud-hosted version** — no installation required:

**[Launch the K3Y Open Session Finder](https://k3y-open-sessions.streamlit.app/)**

This hosted version offers the full feature set, including time zone selection, area filtering, session copying, and CSV export — all accessible from any modern web browser.

## Features

- **Time Zone Selection**: Choose the appropriate time zone.
- **Select K3Y Area**: Focus on a specific operating region.
- **View Available Time Slots**: Display open operating times based on your selected criteria.
- **Save Settings**: Save your time zone, K3Y area, and time range preferences for future use.
- **Copy Selected Rows**: Copy selected time slots to your clipboard—perfect for pasting into an email or web form when requesting an operating time.
- **CSV Export**: Download the filtered time slots as a CSV file for offline use or sharing.


## Installation

To get started with K3Y Open Slot Finder:

1. Clone this repository:
   ```bash
   git clone https://github.com/MarkCruse/k3y-open-sessions.git
   cd k3y-open-sessions
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install streamlit requests beautifulsoup4
    ```
4. (Optional) Save the environment
   ```bash
   pip freeze > requirements.txt
   ```  

## How to Use
### Streamlit UI
Launch the web interface:
   ```bash
   streamlit run dashboard.py
   ```
   In the sidebar you can:
   - Select your time zone
   - Choose a K3Y area
   - Define your preferred operating hours
   - View and export open slots
   - Copy selected rows to clipboard
   - Save your settings for future use

## Command-Line Interface
Run with saved settings:
   ```bash
   python k3y_open_time_slots.py
   ```
Run with custom parameters:
   ```bash
   python k3y_open_time_slots.py --time-zone CST --area K3Y/0 --start 08:00 --end 22:00
   ```
   **Command-line options**:
   ```bash
      -h, --help              show this help message and exit  
      --time-zone TIME_ZONE   Time zone abbreviation (e.g., 'EST','CST','PST')   
      --area AREA           K3Y area code (e.g., 'K3Y/0')  
      --start START         Start time of the local day (e.g., '08:00')  
      --end END             End time of the local day (e.g., '22:00')  
   ```

## Configuration File
Preferences are saved in a settings.json file:

   ```json
   {
       "TIME_ZONE_ABBR": "CST",
       "K3Y_AREA": "K3Y/0",
       "LOCAL_DAY_START": "08:00",
       "LOCAL_DAY_END": "22:00"
   }
```
You can edit this file manually or save your selections via the Streamlit UI.

## Code Structure

### ```k3y_open_time_slots.py```  
This is the core logic script that:  
- Loads settings from a ```settings.json``` file
- Converts UTC to view local times
- Scrapes the K3Y Operator Schedule from the SKCC website
- Identifies and prints open slots
- Supports both command-line Streamlit usage

### ```dashboard.py```
This is the Streamlit interface that:
   - Provides an intuitive user interface
   - Offers time zone and area selectors
   - Displays an interactive table of open slots
   - Includes options to export, copy, and save data
   - Uses caching to reduce unnecessary data fetching

## Requirements
- ```streamlit```
- ```requests```
- ```beautifulsoup4```

## Contributing

Contributions are welcome!

If you'd like to help improve the K3Y Open Slot Finder, please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to get started.


## License
This project is licensed under the MIT License. See the ```LICENSE``` file for details.
