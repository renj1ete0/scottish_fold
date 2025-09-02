import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory of this script
SCRIPT_DIR = Path(__file__).resolve().parent

# Go two levels up and point to .env
ENV_PATH = SCRIPT_DIR / "../../.env"

# Load .env from that path
load_dotenv(dotenv_path=ENV_PATH)

EMAIL = os.getenv("ONEMAP_EMAIL")
PASSWORD = os.getenv("ONEMAP_PASSWORD")
print(EMAIL, PASSWORD)

TOKEN_URL = "https://www.onemap.gov.sg/api/auth/post/getToken"

# Get JWT token (replace with your OneMap email & password)
def get_token(email = EMAIL, password = PASSWORD):
    r = requests.post(TOKEN_URL, json={"email": email, "password": password})
    r.raise_for_status()
    return r.json().get("access_token")