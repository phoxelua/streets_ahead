import os
import requests
import urllib
from datetime import datetime


BASE_URL = "http://api.spotcrime.com/crimes.json"


class SpotCrimeClient:
    """
    Client wrapper for SpotCrime API.
    """

    def __init__(self, api_key=None):
        if api_key is None:
            self.api_key = str(os.environ["SPOT_CRIME_API_KEY"])
        else:
            self.api_key = api_key

    def get(self, lat, lon, radius, compact=True):
        # TODO: get lat lon from addy using https://developers.google.com/maps/documentation/geocoding/intro
        query = {
            "radius": radius,
            "lat": lat,
            "lon": lon,
            "key": self.api_key,
        }
        score_url = "{}/?{}".format(BASE_URL, urllib.urlencode(query))
        response = requests.get(score_url)
        response.raise_for_status()

        body = response.json()
        if compact is False:
            return body
        else:
            return {
                "lat": body["lat"],
                "lon": body["lon"],
                "type": body["type"],
                "link": body["link"],
                "date": datetime.strptime(body["date"], "%m/%d/%y %I:%M %p"),
            }
