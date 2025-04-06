import streamlit as st
from k3y_open_time_slots import main, load_settings

# Set the title of the Streamlit app
st.title("K3Y Open Slot Finder")

# Load settings from the settings.ini file
settings = load_settings()

# Display current configuration settings in the sidebar
st.sidebar.header("Settings")
st.sidebar.write(f"K3Y Area: {settings['K3Y_AREA']}")
st.sidebar.write(f"Time Zone: {settings['TIME_ZONE_ABBR']}")
st.sidebar.write(f"Day Start: {settings['LOCAL_DAY_START']}")
st.sidebar.write(f"Day End: {settings['LOCAL_DAY_END']}")

# Define a cached function to fetch open time slots
# This avoids hitting the website or recomputing unless necessary
# `ttl=600` means the cache is valid for 10 minutes
@st.cache_data(ttl=600)
def get_gaps():
    return main()

# Call the cached function to get the data
gaps = get_gaps()

# Check if any gaps were found and display them
if gaps:
    # Reformat the gap data into a clean list of dictionaries
    # This avoids showing an index column and ensures consistent column ordering
    gaps_data = [
        {
            "Date": gap["Date"],
            "Open Slot (UTC)": gap["Open Slot (UTC)"],
            f"Open Slot ({settings['TIME_ZONE_ABBR']})": gap[f"Open Slot ({settings['TIME_ZONE_ABBR']})"]
        }
        for gap in gaps
    ]

    # Display the results in a scrollable, styled table with full width
    st.write("### Available Open Slots")
    st.dataframe(gaps_data, use_container_width=True)

else:
    # If no gaps found, show a success message
    st.success("No gaps found for selected time range!")
