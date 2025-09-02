import pandas as pd
import requests
import time
from common.scripts.zzz_onemap_auth import get_token as get_token

# Load the dataset
df = pd.read_csv("common/non_geo/HDBPropertyInformation.csv")  # replace with actual dataset

# Add columns
df["latitude"] = None
df["longitude"] = None
df["onemap_raw"] = None

# OneMap API endpoints
SEARCH_URL = "https://www.onemap.gov.sg/api/common/elastic/search"

TOKEN = get_token()

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def get_coords(blk_no, street_name):
    search_text = f"{blk_no} {street_name}"
    params = {
        "searchVal": search_text,
        "returnGeom": "Y",
        "getAddrDetails": "Y",
        "pageNum": 1
    }
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()

        if data.get("found", 0) == 0:
            return None, None, data

        results = data["results"]

        for res in results:
            addr = res.get("ADDRESS", "").lower()
            if str(blk_no).lower() in addr and str(street_name).lower() in addr:
                return res["LATITUDE"], res["LONGITUDE"], data

        first = results[0]
        return first["LATITUDE"], first["LONGITUDE"], data

    except Exception as e:
        print(f"Error for {blk_no} {street_name}: {e}")
        return None, None, None

# Loop with a delay to avoid rate-limiting
for idx, row in df.iterrows():
    lat, lon, raw = get_coords(row["blk_no"], row["street"])
    df.at[idx, "latitude"] = lat
    df.at[idx, "longitude"] = lon
    df.at[idx, "onemap_raw"] = raw
    time.sleep(0.05)  # add delay
    print(idx)
    if idx % 100 == 0:
        df.to_csv("gen_data/hdb_blocks_with_coords_partial.csv", index=False)

df.to_csv("gen_data/hdb_blocks_with_coords.csv", index=False)
