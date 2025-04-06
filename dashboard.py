import streamlit as st
import csv
import io
import datetime
from k3y_open_time_slots import load_settings, fetch_k3y_data, find_gaps, convert_to_utc, convert_to_local
import json

# Load settings from file
settings = load_settings()

K3Y_AREA = settings['K3Y_AREA']

# Title
# st.title(f"K3Y Open Slot Finder - {K3Y_AREA}")

# Sidebar configuration
st.sidebar.header("Settings")

# Time zone selector (overrides settings.ini)
time_zone_options = [
    "EST", "CST", "MST", "PST", "AKST", "HAST", "SST", "CHST"
]
selected_tz = st.sidebar.selectbox(
    "Select Time Zone",
    options=time_zone_options,
    index=time_zone_options.index(settings["TIME_ZONE_ABBR"])
)
k3y_area_options = [f"K3Y/{i}" for i in range(10)]
selected_area = st.sidebar.selectbox(
    "K3Y Area",
    options=k3y_area_options,
    index=k3y_area_options.index(settings["K3Y_AREA"])
)

# Update title based on selected K3Y area
st.title(f"K3Y Open Slot Finder - {selected_area}")

# Create a list of hours in 24-hour format
hour_options = [f"{h:02d}:00" for h in range(24)]

# Default selections based on settings.ini values
default_day_start_str = settings["LOCAL_DAY_START"]
default_day_end_str = settings["LOCAL_DAY_END"]

# Select start and end hours
selected_day_start_str = st.sidebar.selectbox("Day Start (24 hour format local time)", hour_options, index=hour_options.index(default_day_start_str))
selected_day_end_str = st.sidebar.selectbox("Day End (24 hour format local time)", hour_options, index=hour_options.index(default_day_end_str))

# Save button (after start and end times)
if st.sidebar.button('Save Settings'):
    # Save the selected values into the settings dictionary
    settings["TIME_ZONE_ABBR"] = selected_tz
    settings["K3Y_AREA"] = selected_area
    settings["LOCAL_DAY_START"] = selected_day_start_str
    settings["LOCAL_DAY_END"] = selected_day_end_str

    # Write the updated settings to settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    # Reload the settings to reflect the changes
    settings = load_settings()
    st.sidebar.success("Settings saved successfully!")

# Refresh button
refresh = st.button("🔄 Refresh Data")

# Recalculate the time range in UTC based on the selected time zone
LOCAL_DAY_START_UTC = convert_to_utc(settings['LOCAL_DAY_START'], selected_tz)
LOCAL_DAY_END_UTC = convert_to_utc(settings['LOCAL_DAY_END'], selected_tz)
REQUIRED_RANGES = [(LOCAL_DAY_START_UTC, LOCAL_DAY_END_UTC)]

# Cache the gap results with optional clearing on refresh
@st.cache_data(ttl=600)
def get_gaps_with_timezone(timezone, area, start_local_str, end_local_str):
    local_start_utc = convert_to_utc(start_local_str, timezone)
    local_end_utc = convert_to_utc(end_local_str, timezone)
    required_ranges = [(local_start_utc, local_end_utc)]

    data = fetch_k3y_data("https://www.skccgroup.com/k3y/slot_list.php", area)
    return find_gaps(data, required_ranges, timezone, area)  # Pass `area` here

# Clear cache if refresh is clicked
if refresh:
    get_gaps_with_timezone.clear()

# Fetch and display gaps
gaps = get_gaps_with_timezone(
    timezone=selected_tz,
    area=selected_area,
    start_local_str=selected_day_start_str,  # Ensure this matches
    end_local_str=selected_day_end_str       # Ensure this matches
)

if gaps:
    st.write("### Available Open Slots")

    gaps_data = []
    for gap in gaps:
        local_col = f"Open Slot ({selected_tz})"
        if local_col in gap:
            gaps_data.append({
                "Date": gap["Date"],
                "Open Slot (UTC)": gap["Open Slot (UTC)"],
                local_col: gap[local_col]
            })

    st.dataframe(gaps_data, use_container_width=True)

    # Download CSV functionality
    def convert_to_csv(data):
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return output.getvalue().encode("utf-8")

    csv_data = convert_to_csv(gaps_data)
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="k3y_open_slots.csv",
        mime="text/csv"
    )
else:
    st.success("No gaps found for selected time range!")
