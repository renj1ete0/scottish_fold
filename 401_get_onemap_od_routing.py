from common.scripts.zzz_onemap_auth import get_token as auth
from common.scripts.zzz_onemap_routing import get_route as route

import pandas as pd
import geopandas as gpd
import json

# Load hdb_residential.shp
hdb_resi = gpd.read_file("hdb_residential.shp")

# Load test.shp
test_gdf = gpd.read_file("test.shp")

# Get OneMap API token
AUTH_TOKEN = auth()
PRIORITIZE = "duration" 
# Copies in meters CRS for distance
hdb_resi_m = hdb_resi.to_crs(epsg=3414)   # SVY21 / Singapore TM
test_gdf_m = test_gdf.to_crs(epsg=3414)

# Add stable IDs if missing
if "orig_id" not in hdb_resi.columns:
    hdb_resi["orig_id"] = hdb_resi.index.astype(str)
if "dest_id" not in test_gdf.columns:
    test_gdf["dest_id"] = test_gdf.index.astype(str)

# ------------------ helpers ------------------
def extract_itinerary_metric(route_json, metric="duration"):
    """
    Returns the best itinerary metric (seconds for duration) from OneMap response.
    If missing, returns +inf.
    """
    try:
        plans = route_json.get("plan", {}).get("itineraries", [])
        vals = []
        for it in plans:
            if metric == "duration":
                v = it.get("duration")
            elif metric == "distance":  # some responses include "walkDistance" etc.; fall back to duration if needed
                v = it.get("distance")
                if v is None:
                    v = it.get("duration")
            else:
                v = it.get("duration")
            if isinstance(v, (int, float)):
                vals.append(float(v))
        return min(vals) if vals else float("inf")
    except Exception:
        return float("inf")

def latlon_string(geom_4326):
    # OneMap expects "lat,lon" (note y,x)
    return f"{geom_4326.y:.6f},{geom_4326.x:.6f}"

# ------------------ core routing logic ------------------
best_routes = []  # to build a summary table if needed

# Precompute (keep WGS84 geoms to call API)
hdb_geoms_4326 = hdb_resi.geometry
test_geoms_4326 = test_gdf.geometry

for i, (orig_idx, orig_row) in enumerate(hdb_resi.iterrows(), start=1):
    orig_id = orig_row["orig_id"]
    orig_pt_wgs = hdb_geoms_4326.loc[orig_idx]
    orig_pt_m   = hdb_resi_m.geometry.loc[orig_idx]

    # Straight-line distances (meters) from this origin to all tests
    dists = test_gdf_m.geometry.distance(orig_pt_m)  # pandas Series aligned to test_gdf index

    # Find nearest straight-line distance
    d_min = dists.min()
    if pd.isna(d_min) or d_min == float("inf"):
        # Nothing to route to
        hdb_resi.at[orig_idx, "best_route_file"] = None
        hdb_resi.at[orig_idx, "best_route_dest"] = None
        hdb_resi.at[orig_idx, "best_route_metric"] = None
        continue

    # Candidate set = any destination with distance <= (nearest + 1000 m)
    candidate_mask = dists <= (d_min + 1000.0)
    candidate_idxs = dists.index[candidate_mask]

    start_coords = latlon_string(orig_pt_wgs)

    best_json = None
    best_metric = float("inf")
    best_dest_id = None
    best_straight_dist_m = None
    print(orig_idx)

    for dest_idx in candidate_idxs:
        dest_row = test_gdf.loc[dest_idx]
        dest_id = dest_row["dest_id"]
        dest_pt_wgs = test_geoms_4326.loc[dest_idx]

        end_coords = latlon_string(dest_pt_wgs)

        try:
            route_json = route(
                start_coords=start_coords,
                end_coords=end_coords,
                auth=AUTH_TOKEN
            )
        except Exception as e:
            # Skip on errors, keep going
            print(e)
            continue

        metric_val = extract_itinerary_metric(route_json, PRIORITIZE)
        if metric_val < best_metric:
            best_metric = metric_val
            best_json = route_json
            best_dest_id = dest_id
            best_straight_dist_m = float(dists.loc[dest_idx])

    # Write best route JSON to disk (avoid shapefile field limits)
    if best_json is not None:
        out_path = f"zz_onemap_temp_data/route_{orig_id}__to__{best_dest_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(best_json, f, ensure_ascii=False)

        hdb_resi.at[orig_idx, "best_route_file"] = str(out_path)
        hdb_resi.at[orig_idx, "best_route_dest"] = best_dest_id
        hdb_resi.at[orig_idx, "best_route_metric"] = best_metric
        hdb_resi.at[orig_idx, "best_route_straight_m"] = best_straight_dist_m
    else:
        hdb_resi.at[orig_idx, "best_route_file"] = None
        hdb_resi.at[orig_idx, "best_route_dest"] = None
        hdb_resi.at[orig_idx, "best_route_metric"] = None
        hdb_resi.at[orig_idx, "best_route_straight_m"] = None

# ------------------ save outputs ------------------
# Shapefile has string-length limits; GeoPackage is safer.
hdb_resi.to_file("gen_data/hdb_resi_with_best_routes.gpkg", layer="hdb_resi", driver="GPKG")
# If you really need a shapefile (will truncate long paths):
# hdb_resi.to_file("hdb_resi_with_best_routes.shp", driver="ESRI Shapefile")