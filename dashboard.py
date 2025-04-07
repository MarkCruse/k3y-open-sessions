import streamlit as st
import csv
import io
import json
from k3y_open_time_slots import (
    load_settings, convert_to_utc, convert_to_local,
    fetch_k3y_data, find_gaps, get_open_slots, VALID_TIME_ZONES
)

# Page configuration
st.set_page_config(
    page_title="K3Y Open Slot Finder",
    page_icon="📅",
    layout="centered"
)

# Load settings from file
@st.cache_data(ttl=600)
def get_settings():
    return load_settings()

settings = get_settings()

# Sidebar configuration
st.sidebar.header("Settings")

# Time zone selector (overrides settings)
time_zone_options = list(VALID_TIME_ZONES.keys())
selected_tz = st.sidebar.selectbox(
    "Select Time Zone",
    options=time_zone_options,
    index=time_zone_options.index(settings["TIME_ZONE_ABBR"]) if settings["TIME_ZONE_ABBR"] in time_zone_options else 0
)

# K3Y area selector
k3y_area_options = [f"K3Y/{i}" for i in range(10)]
selected_area = st.sidebar.selectbox(
    "K3Y Area",
    options=k3y_area_options,
    index=k3y_area_options.index(settings["K3Y_AREA"]) if settings["K3Y_AREA"] in k3y_area_options else 0
)

# Update title based on selected K3Y area
st.title(f"K3Y Open Slot Finder - {selected_area}")

# Create a list of hours in 24-hour format
hour_options = [f"{h:02d}:00" for h in range(24)]

# Default selections based on settings values
default_day_start_str = settings["LOCAL_DAY_START"]
default_day_end_str = settings["LOCAL_DAY_END"]

# Time range selectors
selected_day_start_str = st.sidebar.selectbox(
    "Day Start (24 hour format local time)", 
    hour_options, 
    index=hour_options.index(default_day_start_str) if default_day_start_str in hour_options else 8
)

selected_day_end_str = st.sidebar.selectbox(
    "Day End (24 hour format local time)", 
    hour_options, 
    index=hour_options.index(default_day_end_str) if default_day_end_str in hour_options else 22
)

# Save settings button
if st.sidebar.button('Save Settings'):
    # Update settings dictionary
    settings["TIME_ZONE_ABBR"] = selected_tz
    settings["K3Y_AREA"] = selected_area
    settings["LOCAL_DAY_START"] = selected_day_start_str
    settings["LOCAL_DAY_END"] = selected_day_end_str

    # Write to settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

    # Clear cache to reload settings
    get_settings.clear()
    st.sidebar.success("Settings saved successfully!")

# Refresh button
refresh = st.button("🔄 Refresh Data")

# Cache the gap results with optional clearing on refresh
@st.cache_data(ttl=600)
def get_cached_open_slots(timezone, area, start_local_str, end_local_str):
    return get_open_slots(
        area=area,
        time_zone_abbr=timezone,
        local_day_start=start_local_str,
        local_day_end=end_local_str
    )

# Clear cache if refresh is clicked
if refresh:
    get_cached_open_slots.clear()
    st.success("Data refreshed!")

# Fetch and display gaps
gaps = get_cached_open_slots(
    timezone=selected_tz,
    area=selected_area,
    start_local_str=selected_day_start_str,
    end_local_str=selected_day_end_str
)

if gaps:
    st.write("### Available Open Slots")

    local_col = f"Open Slot ({selected_tz})"
    # Create base data with a selection column
    gaps_data = [{
        "Select Time Slot": False,
        "Date": gap["Date"],
        "Open Slot (UTC)": gap["Open Slot (UTC)"],
        local_col: gap[local_col]
    } for gap in gaps if local_col in gap]

    edited_df = st.data_editor(
        gaps_data,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select time slots to copy",
                width="small",
            ),
            "Date": st.column_config.TextColumn(
                "Date",
                width="small",
            ),
            "UTC": st.column_config.TextColumn(
                "UTC Time",
                width="medium",
            ),
            local_col: st.column_config.TextColumn(
                local_col,
                width="medium",
            )
        },   
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key="editable_gaps"
    )

    # Filter selected rows
    selected_rows = [
        row for row in edited_df if row["Select Time Slot"]
    ]

    # Button to copy selected rows
    if st.button("📋 Copy Selected Rows"):
        if selected_rows:
            # Format selected rows for clipboard
            formatted_rows = [
                f"{row['Date']}\t {row['Open Slot (UTC)']}"
                for row in selected_rows
            ]
            st.code("\n".join(formatted_rows), language="text")
            st.success(f"{len(selected_rows)} row(s) ready to copy. Click the copy icon in the code block above. Paste the copied rows into an email to your area coordinator/scheduler to request the dates/times.")
        else:
            st.warning("No rows selected!")

    # Download CSV functionality
    def convert_to_csv(data):
        output = io.StringIO()
        if data:
            fieldnames = [key for key in data[0].keys() if key != "Select Time Slot"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow({k: v for k, v in row.items() if k != "Select Time Slot"})
        return output.getvalue().encode("utf-8")

    csv_data = convert_to_csv(gaps_data)
    st.download_button(
        label="📥 Download table to CSV file",
        data=csv_data,
        file_name="k3y_open_slots.csv",
        mime="text/csv"
    )
else:
    st.info("No gaps found for selected time range!")

# Footer with information
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool helps you identify available time slots for K3Y operations. Simply choose your time zone, K3Y call area, and preferred operating hours to view open times. You can also select specific slots, copy them to your clipboard, and paste them into an email to your area coordinator or scheduler to request those dates and times.
""")