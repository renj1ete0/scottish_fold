import requests

# OneMap API endpoints
SEARCH_URL = "https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme"


def retrieve_theme(theme_name, auth):
    headers = {"Authorization": f"Bearer {auth}"}
    response = requests.get(SEARCH_URL, headers=headers, params={"queryName": theme_name})
    response.raise_for_status()
    return response.json()
