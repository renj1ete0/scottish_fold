from common.scripts.zzz_onemap_auth import get_token as auth
from common.scripts.zzz_onemap_retrieve_theme import retrieve_theme as ret_theme
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

res = ret_theme(theme_name = "ssot_hawkercentres", auth = auth())

# Extract only features (skip first element which contains metadata)
records = [rec for rec in res["SrchResults"] if "NAME" in rec]

# Build GeoDataFrame
features = []
for rec in records:
    if "LatLng" not in rec:
        continue
    
    try:
        lat, lon = map(float, rec["LatLng"].split(","))
        geometry = Point(lon, lat)  # shapely Point (lon, lat)
    except Exception:
        continue
    
    props = rec.copy()
    props.pop("LatLng", None)  # remove LatLng since we have geometry
    features.append({**props, "geometry": geometry})

gdf = gpd.GeoDataFrame(features, geometry="geometry", crs="EPSG:4326")

gdf.to_file(f"gen_data/test.shp")