import requests
from time import sleep

# OneMap API endpoints
ROUTING_URL = "https://www.onemap.gov.sg/api/public/routingsvc/route"


def get_route(start_coords, end_coords, routetype = "pt", date = "09-01-2025", time = "[08][00][00]", mode = "TRANSIT", maxwalkdist = None, auth = None):
    error = 0
    while error != 200:
        headers = {"Authorization": f"Bearer {auth}"}

        if maxwalkdist is not None:
            parameters = {
                "start": start_coords,
                "end": end_coords,
                "routeType": routetype,
                "date": date,
                "time": time,
                "mode": mode,
                "maxwalkdist": maxwalkdist
            }
        else:
            parameters = {
                "start": start_coords,
                "end": end_coords,
                "routeType": routetype,
                "date": date,
                "time": time,
                "mode": mode,
            }

        response = requests.get(ROUTING_URL, headers=headers, params=parameters)
        response.raise_for_status()
        error = response.status_code
        sleep(0.05)  # add delay
    return response.json()
