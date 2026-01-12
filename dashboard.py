import streamlit as st
import csv
import io
import json
import time
from datetime import datetime, timedelta
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

# Add CSS for tooltip border styling
st.markdown("""
<style>
/* Add white border to tooltips */
div[data-baseweb="tooltip"],
div[role="tooltip"],
.stTooltipIcon + div {
    border: 2px solid white !important;
    box-shadow: 0 0 5px rgba(255, 255, 255, 0.5) !important;
}
</style>
""", unsafe_allow_html=True)

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

    # DEBUG: Check the time zone keys
    print("VALID_TIME_ZONES keys:", list(VALID_TIME_ZONES.keys()))
    
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
    #hour_options = [f"{h:02d}:00" for h in range(24)]

    # Create a list of hours in 12-hour AM/PM format
    hour_options = [(datetime.strptime(f"{h:02d}:00", "%H:%M").strftime("%I:%M %p")) for h in range(24)]


    # Default selections based on settings values
    default_day_start_str = st.session_state.settings["LOCAL_DAY_START"]
    default_day_end_str = st.session_state.settings["LOCAL_DAY_END"]

    # Time range selectors
    selected_day_start_str = st.sidebar.selectbox(
        "Day Start", 
        hour_options, 
        index=hour_options.index(default_day_start_str) if default_day_start_str in hour_options else "6:00 AM",
        help="Select the start time of your operating day"
    )

    selected_day_end_str = st.sidebar.selectbox(
        "Day End", 
        hour_options, 
        index=hour_options.index(default_day_end_str) if default_day_end_str in hour_options else "12:00 PM",
        help="Select the end time of your operating day."
    )

    # Save settings button
    if st.sidebar.button('Save Settings', help="Save current settings as defaults."):
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


    # Convert AM/PM string back to 24-hour format
    day_start_24hr = datetime.strptime(selected_day_start_str, "%I:%M %p").strftime("%H:%M")
    day_end_24hr = datetime.strptime(selected_day_end_str, "%I:%M %p").strftime("%H:%M")
    # Return the selected values
    return selected_tz, selected_area, day_start_24hr, day_end_24hr


# Function to render the results table
def render_results_table(gaps, selected_tz, key):

    current_year = datetime.now().year  # only used for calculations

    if not gaps:
        st.info("No gaps found for selected time range!")
        return [], []

    start_ampm = datetime.strptime(selected_day_start_str, "%H:%M").strftime("%I:%M %p")
    end_ampm = datetime.strptime(selected_day_end_str, "%H:%M").strftime("%I:%M %p")

    st.markdown(
        f"""
        <div style="font-family: system-ui, sans-serif; font-size:18px; font-weight:500;">
            <p style="margin-bottom: 0;"><strong>
                Available K3Y Session Times for: <span style="color:#99b4f2;">&nbsp;{selected_area}&nbsp;&nbsp;{start_ampm}-{end_ampm} {selected_tz}</span></strong>
            </p>
            <div style="height:10px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
        help="Looking for different times? Use the sidebar to adjust time zone, area, and operating time range."
    )

    local_col = f"Open Slot ({selected_tz})"
    local_label = f"Converted UTC to {selected_tz}"

    gaps_data = []

    offset_hours = VALID_TIME_ZONES[selected_tz]

    for gap in gaps:
        if "Open Slot (UTC)" not in gap:
            continue
        #session_utc = f"{datetime.strptime(gap['Date'], '%m-%d').strftime('%a %b %d,')} {gap['Open Slot (UTC)']}"
        session_utc = f"{datetime.strptime(f'{gap['Date']}-{current_year}', '%m-%d-%Y').strftime('%a %b %d,')} {gap['Open Slot (UTC)']}"


        # Split UTC start/end times and remove " UTC"
        utc_start_str, utc_end_str = gap["Open Slot (UTC)"].replace(" UTC", "").split(" - ")

        # Convert to local time using offset and current year
        start_local = datetime.strptime(f"{gap['Date']}-{current_year} {utc_start_str}", "%m-%d-%Y %H:%M") + timedelta(hours=offset_hours)
        end_local   = datetime.strptime(f"{gap['Date']}-{current_year} {utc_end_str}", "%m-%d-%Y %H:%M") + timedelta(hours=offset_hours)

        # Format for display WITHOUT the year, using a hyphen between times
        local_str = f"{start_local.strftime('%a %b %d, %I:%M %p')} - {end_local.strftime('%I:%M %p')} {selected_tz}"


        gaps_data.append({
            "Select Time Slot": False,
            "Session (UTC)": session_utc,
            local_col: local_str
        })

    edited_df = st.data_editor(
        gaps_data,
        column_config={
            "Select Time Slot": st.column_config.CheckboxColumn(
                "Select",
                help="Select time slots to copy",
                width="small",
            ),
            "Session (UTC)": st.column_config.TextColumn(
                "Session (UTC)",
                width="medium",
                help="Date and time of the session in UTC"
            ),
            local_col: st.column_config.TextColumn(
                local_label,
                width="medium",
                help=f"Date and time of the session in your local time zone ({selected_tz})"
            )
        },
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key=key
    )

    return edited_df, gaps_data, local_col

# Function to handle copying and downloading data
def handle_data_actions(edited_df, gaps_data, local_col):
    selected_rows = [row for row in edited_df if row["Select Time Slot"]]
        
    # Button to copy selected rows
    if st.button("📋 Copy Selected Rows", help="Generate text for email requests"):
        if selected_rows:
            email_body = "I would like to request the following K3Y operating times:\n"
            formatted_rows = [
                f"{row['Session (UTC)']}\t {row[local_col]}"
                for row in selected_rows
            ]
            full_text = "\n".join([email_body, *formatted_rows])
            st.code(full_text, language="text")
            st.success(f"{len(selected_rows)} slot(s) selected. Copy the message above and paste it into your email when requesting operating times.")
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
        help="Download all open sessions for the selected settings to a CSV file."
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
refresh = st.button("🔄 Refresh Data", help="Refresh data from the server.")

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
    #st.write(f"###### SKCC OP Schedule last update: {update_text}")
    st.markdown(
    f"""
    <div style="font-family: system-ui, sans-serif; font-size:12px; font-weight:500;">
        <p style="margin-bottom: 0;">
            SKCC OP Schedule last update: <strong>&nbsp; {update_text}</strong>
        </p>
        <div style="height:20px;"></div>
    </div>
    """,
    unsafe_allow_html=True,
    )

# Render the results table
edited_df, gaps_data, local_col = render_results_table(gaps, selected_tz, st.session_state.editor_key)

if gaps_data:
    handle_data_actions(edited_df, gaps_data, local_col)


# Footer with information
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool helps you identify available time slots for K3Y operations. Simply choose your time zone, K3Y call area, and preferred operating hours to view open times. You can also select specific session times, copy them to your clipboard, and paste them into an email to your area coordinator or scheduler to request those dates and times.
""")
st.sidebar.markdown(
    "Made for the SKCC community. View the source on [GitHub](https://github.com/MarkCruse/k3y-open-sessions)."
)