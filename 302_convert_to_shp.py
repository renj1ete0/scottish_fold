import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load dataset (must contain latitude, longitude columns)
df = pd.read_csv("gen_data/hdb_blocks_with_coords.csv")

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326"  # WGS84 lat/lon
)

# 1. All records
gdf.to_file("gen_data/hdb_all.shp")

# 2. Only residential = 1
gdf[gdf["residential"] == "Y"].to_file("gen_data/hdb_residential.shp")

# 3. Only market_hawker = 1
gdf[gdf["market_hawker"] == "Y"].to_file("gen_data/hdb_market_hawker.shp")

# 4. Only commercial = 1
gdf[gdf["commercial"] == "Y"].to_file("gen_data/hdb_commercial.shp")
