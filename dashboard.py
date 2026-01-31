import streamlit as st
import csv
import io
import json
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# from k3y_open_time_shifts import (
#     load_settings, convert_to_utc, convert_to_local,
#     fetch_k3y_data, find_gaps, get_open_slots, VALID_TIME_ZONES
from k3y_open_time_shifts import (
    load_settings, get_open_slots, VALID_TIME_ZONES
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

# Initialize settings in session state
def initialize_settings():
    if 'settings' not in st.session_state:
        st.session_state.settings = load_settings()

    # Detect system timezone (works locally and on Cloud)
    try:
        # Get current local timezone name, e.g., 'EST' or 'EDT'
        local_tz_name = time.tzname[time.localtime().tm_isdst]
    except Exception:
        local_tz_name = "UTC"

    # Only override if it's in our VALID_TIME_ZONES
    if local_tz_name in VALID_TIME_ZONES:
        st.session_state.settings["TIME_ZONE_ABBR"] = local_tz_name

    return st.session_state.settings

# Sidebar settings
def render_settings_sidebar():
    st.sidebar.header("Settings")

    # --- Time zone selector ---
    time_zone_options = list(VALID_TIME_ZONES.keys())
    selected_tz = st.sidebar.selectbox(
        "Select Time Zone",
        options=time_zone_options,
        index=time_zone_options.index(st.session_state.settings["TIME_ZONE_ABBR"])
              if st.session_state.settings["TIME_ZONE_ABBR"] in time_zone_options else 0,
        help="Select your preferred timezone (auto-detected on first load)."
    )

    # Update session state if user changes it
    st.session_state.settings["TIME_ZONE_ABBR"] = selected_tz

    # --- K3Y area selector ---
    k3y_area_options = [f"K3Y/{i}" for i in range(10)]
    selected_area = st.sidebar.selectbox(
        "K3Y Area",
        options=k3y_area_options,
        index=k3y_area_options.index(st.session_state.settings["K3Y_AREA"])
              if st.session_state.settings["K3Y_AREA"] in k3y_area_options else 0
    )

    # --- Operating hours ---
    hour_options = [(datetime.strptime(f"{h:02d}:00", "%H:%M").strftime("%I:%M %p")) for h in range(24)]
    default_day_start_str = st.session_state.settings["LOCAL_DAY_START"]
    default_day_end_str   = st.session_state.settings["LOCAL_DAY_END"]

    selected_day_start_str = st.sidebar.selectbox(
        "Day Start",
        hour_options,
        index=hour_options.index(default_day_start_str) if default_day_start_str in hour_options else 0,
        help="Select the start time of your operating day"
    )

    selected_day_end_str = st.sidebar.selectbox(
        "Day End",
        hour_options,
        index=hour_options.index(default_day_end_str) if default_day_end_str in hour_options else 12,
        help="Select the end time of your operating day."
    )

    # Convert to 24-hour format for later use
    day_start_24hr = datetime.strptime(selected_day_start_str, "%I:%M %p").strftime("%H:%M")
    day_end_24hr   = datetime.strptime(selected_day_end_str, "%I:%M %p").strftime("%H:%M")

    return selected_tz, selected_area, day_start_24hr, day_end_24hr

# Render table
def render_results_table(gaps, selected_tz, key):
    local_col = f"Open Slot ({selected_tz})"
    gaps_data = []

    if not gaps:
        st.info("No gaps found for selected time range!")
        return [], [], local_col

    offset_hours = VALID_TIME_ZONES[selected_tz]
    today_utc = datetime.now(timezone.utc).date()

    for gap in gaps:
        if "Open Slot (UTC)" not in gap:
            continue

        gap_date_utc = datetime.strptime(gap["Date"], "%m/%d/%y").date()
        if gap_date_utc < today_utc:
            continue

        session_utc = f"{datetime.strptime(gap['Date'], '%m/%d/%y').strftime('%a %b %d,')} {gap['Open Slot (UTC)']}"

        try:
            utc_start_str, utc_end_str = gap["Open Slot (UTC)"].replace(" UTC", "").split(" - ")
            start_local = datetime.strptime(f"{gap['Date']} {utc_start_str}", "%m/%d/%y %H:%M") + timedelta(hours=offset_hours)
            end_local = datetime.strptime(f"{gap['Date']} {utc_end_str}", "%m/%d/%y %H:%M") + timedelta(hours=offset_hours)
            local_str = f"{start_local.strftime('%a %b %d, %I:%M %p')} - {end_local.strftime('%I:%M %p')} {selected_tz}"
        except Exception as e:
            local_str = "Error converting time"
            st.warning(f"Failed to convert time for {gap['Date']}: {str(e)}")

        gaps_data.append({
            "Select Time Slot": False,
            "Session (UTC)": session_utc,
            local_col: local_str
        })

    if not gaps_data:
        st.info("No available sessions match your time range.")
        return [], [], local_col

    # --- FIX: Remove 'width' from data_editor entirely ---
    edited_df = st.data_editor(
        gaps_data,
        column_config={
            "Select Time Slot": st.column_config.CheckboxColumn(
                "Select",
                width=80
            ),
            "Session (UTC)": st.column_config.TextColumn(
                "Session (UTC)",
                width=200
            ),
            local_col: st.column_config.TextColumn(
                f"Converted UTC to {selected_tz}",
                width=240
            )
        },
        num_rows="fixed",
        hide_index=True,
        key=key
    )

    return edited_df, gaps_data, local_col


# Handle copy/download
def handle_data_actions(edited_df, gaps_data, local_col):
    selected_rows = [row for row in edited_df if row["Select Time Slot"]]
    if st.button("📋 Copy Selected Rows", help="Generate text for email requests"):
        if selected_rows:
            email_body = "I would like to request the following K3Y operating times:\n"
            formatted_rows = [f"{row['Session (UTC)']}\t {row[local_col]}" for row in selected_rows]
            full_text = "\n".join([email_body, *formatted_rows])
            st.code(full_text, language="text")
            st.success(f"{len(selected_rows)} slot(s) selected. Copy the message above and paste it into your email when requesting operating times.")
        else:
            st.warning("No rows selected!")

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

# Cache settings
@st.cache_data(ttl=600)
def get_settings():
    if 'settings' in st.session_state:
        return st.session_state.settings
    else:
        return initialize_settings()

# Cache open slots
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

# Initialize session state
initialize_settings()
settings = st.session_state.settings
settings = st.session_state.settings

if "editor_key" not in st.session_state:
    st.session_state.editor_key = "editable_gaps_0"

# Main flow
selected_tz, selected_area, selected_day_start_str, selected_day_end_str = render_settings_sidebar()
st.title(f"K3Y Open Session Finder")

refresh = st.button("🔄 Refresh Data", help="Refresh data from the server.")
if refresh:
    get_cached_open_slots.clear()
    msg_container = st.empty()
    msg_container.success("Data refreshed!")
    time.sleep(1)
    msg_container.empty()
    key_id = int(st.session_state.editor_key.split("_")[-1])
    st.session_state.editor_key = f"editable_gaps_{key_id + 1}"

gaps, update_info = get_cached_open_slots(
    timezone=selected_tz,
    area=selected_area,
    start_local_str=selected_day_start_str,
    end_local_str=selected_day_end_str
)

if update_info:
    update_text = ''
    update_text = update_info.replace('(Update:', '').replace(')', '').strip()
    st.markdown(
        f"""
        <div style="font-family: system-ui, sans-serif; font-size:12px; font-weight:500;">
            <p style="margin-bottom: 0;">
                SKCC Op Schedule Calendar last update: <strong>&nbsp; {update_text}</strong>
            </p>
            <div style="height:20px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

edited_df, gaps_data, local_col = render_results_table(gaps, selected_tz, st.session_state.editor_key)


if gaps_data:
    handle_data_actions(edited_df, gaps_data, local_col)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool helps you identify available time slots for K3Y operations. Simply choose your time zone, K3Y call area, and preferred operating hours to view open times. You can also select specific session times, copy them to your clipboard, and paste them into an email to your area coordinator or scheduler to request those dates and times.
""")
st.sidebar.markdown(
    "Made for the SKCC community. View the source on [GitHub](https://github.com/MarkCruse/k3y-open-sessions)."
)
