import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(page_title="Sofia Heat Map 2020-2024", layout="wide")
st.title("🗺️ Sofia Urban Heat Island Map (2020-2024)")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("sofia_heat_всички_2020-2024.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# Get date range
min_date = df['date'].min()
max_date = df['date'].max()

# Sidebar controls
st.sidebar.header("📅 Select Date")
selected_date = st.sidebar.date_input(
    "Choose a date:",
    value=datetime(2023, 6, 15),
    min_value=min_date,
    max_value=max_date,
)

st.sidebar.header("🌡️ Color Scale Settings")
color_scale = st.sidebar.radio(
    "Temperature ranges:",
    options=["Auto (Data-based)", "Custom"],
    horizontal=True
)

if color_scale == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        temp_cold = st.number_input("🟢 Green (≤°C):", value=5, step=1)
    with col2:
        temp_cool = st.number_input("🟡 Yellow (°C):", value=15, step=1)
    with col1:
        temp_warm = st.number_input("🟠 Orange (°C):", value=25, step=1)
    with col2:
        st.write("")  # spacing
else:
    # Auto-calculate from data
    temps = df['temp_mean'].dropna()
    temp_cold = temps.quantile(0.25)
    temp_cool = temps.quantile(0.5)
    temp_warm = temps.quantile(0.75)

# Filter data for selected date
date_str = pd.Timestamp(selected_date).strftime('%Y-%m-%d')
day_data = df[df['date'].dt.strftime('%Y-%m-%d') == date_str].copy()

if day_data.empty:
    st.warning(f"⚠️ No data available for {selected_date}. Please select another date.")
else:
    # Function to assign color based on temperature
    def get_color(temp):
        if pd.isna(temp):
            return '#CCCCCC'  # Gray for missing data
        elif temp <= temp_cold:
            return '#00AA00'  # Green
        elif temp <= temp_cool:
            return '#FFFF00'  # Yellow
        elif temp <= temp_warm:
            return '#FFA500'  # Orange
        else:
            return '#FF0000'  # Red

    # Normalize temperature to 0-1 for heatmap intensity
    min_temp = day_data['temp_mean'].min()
    max_temp = day_data['temp_mean'].max()
    
    # Create map centered on Sofia
    sofia_center = [42.6977, 23.3219]  # Center coordinates
    m = folium.Map(location=sofia_center, zoom_start=11, tiles="OpenStreetMap")

    # Prepare data for heatmap
    heat_data = []
    for _, row in day_data.iterrows():
        lat = row['lat']
        lon = row['lon']
        temp = row['temp_mean']
        
        # Normalize temperature to intensity (0-1)
        if max_temp > min_temp:
            intensity = (temp - min_temp) / (max_temp - min_temp)
        else:
            intensity = 0.5
        
        heat_data.append([lat, lon, intensity])

    # Add heatmap layer
    HeatMap(heat_data, radius=30, blur=25, max_zoom=1, gradient={0.2: 'green', 0.5: 'yellow', 0.7: 'orange', 1.0: 'red'}).add_to(m)

    # Add district markers with information
    for _, row in day_data.iterrows():
        district = row['district']
        temp = row['temp_mean']
        lat = row['lat']
        lon = row['lon']
        color = get_color(temp)
        
        # Create popup text
        popup_text = f"""
        <b>{district}</b><br>
        Date: {date_str}<br>
        Temp: {temp:.1f}°C<br>
        Max: {row['temp_max']:.1f}°C<br>
        Min: {row['temp_min']:.1f}°C
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=folium.Popup(popup_text, max_width=250),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.9,
            weight=2,
            opacity=0.9
        ).add_to(m)

    # Display map
    st.subheader(f"🌡️ Temperature Heatmap on {selected_date}")
    st_folium(m, width=1400, height=700)

    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌡️ Average Temp", f"{day_data['temp_mean'].mean():.1f}°C")
    with col2:
        st.metric("🔴 Max Temp", f"{day_data['temp_max'].max():.1f}°C")
    with col3:
        st.metric("🔵 Min Temp", f"{day_data['temp_min'].min():.1f}°C")
    with col4:
        st.metric("📍 Districts", f"{len(day_data)}")

    # Show color legend
    st.subheader("📊 Temperature Scale")
    legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
    with legend_col1:
        st.write("🟢 **Green** (Cold)")
        st.write(f"≤ {temp_cold:.1f}°C")
    with legend_col2:
        st.write("🟡 **Yellow** (Cool)")
        st.write(f"{temp_cold:.1f} - {temp_cool:.1f}°C")
    with legend_col3:
        st.write("🟠 **Orange** (Warm)")
        st.write(f"{temp_cool:.1f} - {temp_warm:.1f}°C")
    with legend_col4:
        st.write("🔴 **Red** (Hot)")
        st.write(f"> {temp_warm:.1f}°C")

    # Show district data table
    st.subheader("📋 District Temperature Data")
    display_df = day_data[['district', 'temp_mean', 'temp_max', 'temp_min']].copy()
    display_df.columns = ['District', 'Avg Temp (°C)', 'Max Temp (°C)', 'Min Temp (°C)']
    display_df = display_df.sort_values('Avg Temp (°C)', ascending=False)
    st.dataframe(display_df, width='stretch', hide_index=True)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **How to use:**\n\n"
    "1. Select a date from 2020-2024\n"
    "2. Map colors show temperature per district\n"
    "3. Click on districts for details\n"
    "4. Adjust color scale in sidebar"
)
