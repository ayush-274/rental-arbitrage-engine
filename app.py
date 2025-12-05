import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Page Config
st.set_page_config(page_title="NYC Rental Arbitrage Engine", layout="wide")

# Title
st.title("🏙️ NYC Short-Term Rental Arbitrage Engine")
st.markdown("Identifies high-ROI investment opportunities by combining **Airbnb Revenue** and **Zillow Costs**.")

# Load Data (Cached so it doesn't reload every time you click)
# ... inside app.py ...

@st.cache_data
def load_data():
    # UPDATED PATH: Pointing to the new folder that WILL be on GitHub
    df = pd.read_csv('app_data/nyc_rental_arbitrage_results.csv')
    
    # UPDATED PATH: Pointing to the new folder that WILL be on GitHub
    gdf = gpd.read_file('app_data/nyc_zip_codes.geojson')
    
    # ... rest of the function remains the same ...
    
    # Simple preprocessing to ensure matching types
    df['zipcode'] = df['zipcode'].astype(str)
    
    # Check column name for Zip Code in GeoJSON (usually 'modzcta' or 'postalCode')
    if 'modzcta' in gdf.columns:
        gdf['zipcode'] = gdf['modzcta'].astype(str)
    elif 'postalCode' in gdf.columns:
        gdf['zipcode'] = gdf['postalCode'].astype(str)
    
    # Merge for the map
    gdf_map = gdf.merge(df.groupby('zipcode')['roi_percentage'].mean().reset_index(), on='zipcode')
    
    # CLEANUP: Keep only necessary columns to prevent JSON serialization errors
    # (This fixes the "Timestamp" error if it appears)
    cols_to_keep = ['zipcode', 'roi_percentage', 'geometry']
    gdf_map = gdf_map[cols_to_keep]
    
    return df, gdf_map

try:
    df, gdf_map = load_data()
except FileNotFoundError as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.header("🎯 Investment Filters")
# Expanded slider range to handle outliers
min_roi = st.sidebar.slider("Minimum ROI (%)", -50, 20, -10)
max_budget = st.sidebar.slider("Max Budget ($)", 500_000, 5_000_000, 1_500_000)

# Filter Logic
filtered_df = df[(df['roi_percentage'] >= min_roi) & (df['zillow_price'] <= max_budget)]

# Metrics Row
col1, col2, col3 = st.columns(3)
col1.metric("Properties Found", f"{len(filtered_df)}")
col2.metric("Avg ROI", f"{filtered_df['roi_percentage'].mean():.1f}%")
col3.metric("Avg Entry Price", f"${filtered_df['zillow_price'].mean():,.0f}")
# Map Section
st.subheader(f"📍 Opportunities with ROI > {min_roi}%")

# Create Map
m = folium.Map(location=[40.7128, -74.0060], zoom_start=11, tiles='CartoDB positron')

# --- THE FIX: GROUP DATA BY ZIP CODE FIRST ---
# Folium needs 1 row per Zip Code. We calculate the mean ROI for the filtered data.
grouped_df = filtered_df.groupby('zipcode')['roi_percentage'].mean().reset_index()

# Define bins for the map colors
my_bins = [-1000, -20, -10, 0, 10, 1000]

# Dynamic Map Layer
folium.Choropleth(
    geo_data=gdf_map,
    data=grouped_df,     # <--- UPDATED: Pass the grouped data, not raw df
    columns=['zipcode', 'roi_percentage'],
    key_on='feature.properties.zipcode',
    fill_color='RdYlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    bins=my_bins,
    legend_name='Average ROI (%)'
).add_to(m)

st_folium(m, width=800, height=500)