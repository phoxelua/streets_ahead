import csv
import os
import googlemaps
from datetime import datetime
from utils import mean, weighted_mean
from walkscore import WalkScoreClient


MONDAY_9_AM = datetime(2018, 6, 18, 9)
EXTRA_COLUMNS = ["Walk", "Transit", "Average", "Wt. Average"]


class Location:
    def __init__(self, address, name=None, comment=None, weight=None, lat=None, lon=None):
        self.address = address
        self.name = name or address

        # Destination fields
        self.comment = comment
        self.weight = weight

        # Origin fields
        self.lat = lat
        self.lon = lon


class StreetsAheadService:
    """
    Super wrapper for Google Maps APIs and WalkScoreClient.
    """

    def __init__(self):
        self._gclient = googlemaps.Client(key=str(os.environ["GOOGLE_API_KEY"]))
        self._walk_client = WalkScoreClient()
        self.matrix = self._load_matrix()

    def _load_matrix(self):
        with open("matrix.csv") as f:
            matrix = []
            reader = csv.reader(f)
            for row in reader:
                # The header is the apt then all the points of interest
                # We exclude the EXTRA_COLUMNS on load to force recalculation every time.
                matrix.append(row[:-len(EXTRA_COLUMNS)])
        return matrix

    def _save_matrix(self):
        with open("matrix.csv", "w") as f:
            writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            # Each row is origin, destination, miles, EXTRA_COLUMNS
            for row in self.matrix:
                writer.writerow(row)

    def geocode(self, address):
        result = self._gclient.geocode(address)[0]["geometry"]["location"]
        lat, lon = result["lat"], result["lng"]
        return Location(address=address, lat=lat, lon=lon)

    def is_dirty(self, origins, destinations):
        # We want to trigger an API call and discard our stored results when changes happen in
        # origins.txt, destinations.csv, and matrix.csv.
        # See "Refreshing" in the README for more details.
        if not self.matrix:
            return True
        matrix_origins = set([row[0] for row in self.matrix[1:]])

        # The matrix header has all the destinations but need to subtract out labels and EXTRA_COLUMNS
        matrix_destinations = set(self.matrix[0][1:]) - set(["Apartment"] + EXTRA_COLUMNS)
        return matrix_origins != set(origins) or matrix_destinations != set(destinations)

    def distance_matrix(self, origins, destinations):
        """
        Hits and parses the results from Google Distance Matrix API.
        Does not calculate the values in EXTRA_COLUMNS.
        """
        destinations_list = [destination.name for destination in destinations]
        print("Calculating distance matrix...")
        print("Origins:", ','.join(origins))
        print("Destinations:", ','.join(destinations_list))
        response = self._gclient.distance_matrix(units="imperial",
                                                 mode="transit",
                                                 departure_time=MONDAY_9_AM,
                                                 origins=origins,
                                                 destinations=[destination.address for destination in destinations])
        if response["status"] != "OK":
            raise Exception("Failed to caclulate w/ status code: {}".format(response["status"]))

        matrix = [["Apartment"] + destinations_list]
        for i, row in enumerate(response["rows"]):
            minutes = [int(col["duration"]["value"] / 60) for col in row["elements"]]
            matrix.append([origins[i]] + minutes)
        return matrix

    def scores(self, address):
        location = self.geocode(address)
        data = self._walk_client.get(location)
        return [data["walk"]["score"] or "NA", data["transit"]["score"] or "NA"]

    def summary(self, origins, destinations):
        print("Generating summary...")
        origins = [origin.address for origin in origins]
        if self.is_dirty(origins, [destination.name for destination in destinations]):
            self.matrix = self.distance_matrix(origins, destinations)

        # Extend the Google Distance matrix with our own calculated columns EXTRA_COLUMNS.
        # We handle calculated columns after so that it can be independent of the API call
        weights = [destination.weight for destination in destinations]

        # Add EXTRA_COLUMNS headers
        print("Calculating extra columns...")
        self.matrix[0].extend(EXTRA_COLUMNS)

        for row in self.matrix[1:]:
            origin, minutes = row[0], row[1:]
            minutes = list(map(int, minutes))
            row.extend(self.scores(origin) + [mean(minutes), weighted_mean(minutes, weights)])

        # Override old matrix with new matrix
        self._save_matrix()

        return self.matrix
