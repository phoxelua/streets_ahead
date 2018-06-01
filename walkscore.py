import os
import requests
import urllib


BASE_URL = "http://api.walkscore.com"


class WalkScoreClient:
    """
    Client wrapper for WalkScore API.
    Documentation: https://www.walkscore.com/professional/api.php
    """

    def __init__(self, api_key=None):
        if api_key is None:
            self.api_key = str(os.environ["WALKSCORE_API_KEY"])
        else:
            self.api_key = api_key
        if not self.api_key:
            raise Exception("WALKSCORE_API_KEY not found.")

    def get(self, location, compact=True):
        # TODO: get lat lon from addy using https://developers.google.com/maps/documentation/geocoding/intro
        query = {
            "format": "json",
            "transit": 1,
            "bike": 1,
            "address": location.address,
            "lat": location.lat,
            "lon": location.lon,
            "wsapikey": self.api_key,
        }
        score_url = "{}/score?{}".format(BASE_URL, urllib.parse.urlencode(query))
        response = requests.get(score_url)
        response.raise_for_status()

        body = response.json()
        if compact is False:
            return body
        else:
            return {
                "link": body["ws_link"],
                "walk": {
                    "score": body["walkscore"],
                    "description": body["description"]
                },
                "transit": body["transit"],
                "bike": body["bike"],
            }
