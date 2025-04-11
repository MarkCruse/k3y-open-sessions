import streamlit as st
import csv
import io
import json
import time
from k3y_open_time_slots import (
    load_settings, convert_to_utc, convert_to_local,
    fetch_k3y_data, find_gaps, get_open_slots, VALID_TIME_ZONES
)

# Page configuration
st.set_page_config(
    page_title="K3Y Open Session Finder",
    page_icon="📅",
    layout="centered"
)

# Function to initialize settings in session state
def initialize_settings():
    # Check if settings already exist in session state
    if 'settings' not in st.session_state:
        # Load from file
        st.session_state.settings = load_settings()
    
    return st.session_state.settings

# Function to render the settings sidebar
def render_settings_sidebar():
    st.sidebar.header("Settings")

    # Time zone selector (overrides settings)
    time_zone_options = list(VALID_TIME_ZONES.keys())
    selected_tz = st.sidebar.selectbox(
        "Select Time Zone",
        options=time_zone_options,
        index=time_zone_options.index(st.session_state.settings["TIME_ZONE_ABBR"]) if st.session_state.settings["TIME_ZONE_ABBR"] in time_zone_options else 0
    )

    # K3Y area selector
    k3y_area_options = [f"K3Y/{i}" for i in range(10)]
    selected_area = st.sidebar.selectbox(
        "K3Y Area",
        options=k3y_area_options,
        index=k3y_area_options.index(st.session_state.settings["K3Y_AREA"]) if st.session_state.settings["K3Y_AREA"] in k3y_area_options else 0
    )

    # Create a list of hours in 24-hour format
    hour_options = [f"{h:02d}:00" for h in range(24)]

    # Default selections based on settings values
    default_day_start_str = st.session_state.settings["LOCAL_DAY_START"]
    default_day_end_str = st.session_state.settings["LOCAL_DAY_END"]

    # Time range selectors
    selected_day_start_str = st.sidebar.selectbox(
        "Day Start (24 hour format local time)", 
        hour_options, 
        index=hour_options.index(default_day_start_str) if default_day_start_str in hour_options else 8,
        help="Select the start time of your operating day"
    )

    selected_day_end_str = st.sidebar.selectbox(
        "Day End (24 hour format local time)", 
        hour_options, 
        index=hour_options.index(default_day_end_str) if default_day_end_str in hour_options else 22,
        help="Select the end time of your operating day"
    )

    # Save settings button
    if st.sidebar.button('Save Settings', help="Save current settings as defaults"):
        # Update settings dictionary
        settings_to_save = {
            "TIME_ZONE_ABBR": selected_tz,
            "K3Y_AREA": selected_area,
            "LOCAL_DAY_START": selected_day_start_str,
            "LOCAL_DAY_END": selected_day_end_str
        }
        
        # Save to session state
        st.session_state.settings = settings_to_save
        
        # Try to write to settings.json (works locally, may fail on Cloud)
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings_to_save, f, indent=4)
            file_saved = True
        except Exception as e:
            file_saved = False
        
        # Clear cache to reload settings
        get_cached_open_slots.clear()
        
        if file_saved:
            st.sidebar.success("Settings saved successfully to file and session!")
        else:
            st.sidebar.success("Settings saved for this session!")

    # Return the selected values
    return selected_tz, selected_area, selected_day_start_str, selected_day_end_str

# Function to render the results table
def render_results_table(gaps, selected_tz, key):
    if not gaps:
        st.info("No gaps found for selected time range!")
        return []

    st.write(f"#### Available K3Y Session Times for {selected_area}")

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
            "Select Time Slot": st.column_config.CheckboxColumn(
                "Select",
                help="Select time slots to copy",
                width="small",
            ),
            "Date": st.column_config.TextColumn(
                "Date",
                width="small",
                help="The date of the open slot"
            ),
            "Open Slot (UTC)": st.column_config.TextColumn(
                "UTC Time",
                width="medium",
                help="The time slot in UTC"
            ),
            local_col: st.column_config.TextColumn(
                local_col,
                width="medium",
                help="The time slot in your local time zone"
            )
        },   
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key=key
    )
    
    return edited_df

# Function to handle copying and downloading data
def handle_data_actions(edited_df, gaps_data):
    # Filter selected rows
    selected_rows = [
        row for row in edited_df if row["Select Time Slot"]
    ]
        
    # Button to copy selected rows
    if st.button("📋 Copy Selected Rows", help="Generate text for email requests"):
        if selected_rows:
            email_body = "I would like to request the following operating slots:\n"
            # Format selected rows for clipboard
            formatted_rows = [
                f"{row['Date']}\t {row['Open Slot (UTC)']}"
                for row in selected_rows
            ]
            full_text = "\n".join([email_body, *formatted_rows])
            st.code(full_text, language="text")
            st.success(f"{len(selected_rows)} slot(s) selected. Click the ⧉ icon in the window above to copy. Paste into your email to request operating times.")
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
        mime="text/csv",
        help="Download all slots to a CSV file"
    )

# Load settings from session state or file
@st.cache_data(ttl=600)
def get_settings():
    if 'settings' in st.session_state:
        return st.session_state.settings
    else:
        return initialize_settings()

# Initialize settings in session state
initialize_settings()
settings = st.session_state.settings

# Initialize or update the editable key (used to force reset of checkboxes)
if "editor_key" not in st.session_state:
    st.session_state.editor_key = "editable_gaps_0"

# Cache the gap results with optional clearing on refresh
@st.cache_data(ttl=600)
def get_cached_open_slots(timezone, area, start_local_str, end_local_str):
    try:
        with st.spinner("Fetching open slots..."):
            return get_open_slots(
                area=area,
                time_zone_abbr=timezone,
                local_day_start=start_local_str,
                local_day_end=end_local_str
            )
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return [], None

# Main application flow
# Update title based on selected K3Y area
selected_tz, selected_area, selected_day_start_str, selected_day_end_str = render_settings_sidebar()
st.title(f"K3Y Open Session Finder")

# Refresh button
refresh = st.button("🔄 Refresh Data", help="Refresh data from the server")

# Clear cache if refresh is clicked
if refresh:
    get_cached_open_slots.clear()
    msg_container = st.empty()  # Create a placeholder
    msg_container.success("Data refreshed!")
    time.sleep(1)              # Wait 1 second
    msg_container.empty()       # Clear the message

    # Increment editor key to force widget reinitialization
    key_id = int(st.session_state.editor_key.split("_")[-1])
    st.session_state.editor_key = f"editable_gaps_{key_id + 1}"

# Fetch and display gaps
gaps, update_info = get_cached_open_slots(
    timezone=selected_tz,
    area=selected_area,
    start_local_str=selected_day_start_str,
    end_local_str=selected_day_end_str
)

# Display update information if available
if update_info:
    # Clean up the update info by removing parentheses and "Update: " prefix
    update_text = update_info.replace('(Update:', '').replace(')', '').strip()
    st.write(f"###### SKCC OP Schedule last update: {update_text}")

# Render the results table
edited_df = render_results_table(gaps, selected_tz, st.session_state.editor_key)

if gaps:
    # Handle data actions (copy/download)
    handle_data_actions(edited_df, gaps)

# Footer with information
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool helps you identify available time slots for K3Y operations. Simply choose your time zone, K3Y call area, and preferred operating hours to view open times. You can also select specific session times, copy them to your clipboard, and paste them into an email to your area coordinator or scheduler to request those dates and times.
""")
st.sidebar.markdown(
    "Made for the SKCC community. View the source on [GitHub](https://github.com/MarkCruse/k3y-open-sessions)."
)