import csv
import os
import googlemaps
from collections import defaultdict
from utils import mean, weighted_mean, next_monday
from walkscore import WalkScoreClient


MONDAY_9_AM = next_monday()
EXTRA_COLUMNS = ["Walk", "Transit", "Average", "Wt. Average"]


class Location:
    def __init__(self, address, name=None, comment=None, weight=None, mode=None, lat=None, lon=None):
        self.address = address
        self.name = name or address

        # Destination fields
        self.comment = comment
        self.weight = weight
        self.mode = mode or "transit"

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

    def _group_by_mode(self, destinations):
        by_mode = defaultdict(list)
        for destination in destinations:
            by_mode[destination.mode].append(destination.address)
        return by_mode

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

    def _distance_matrix_by_mode(self, origins, destinations):
        origins_to_times = defaultdict(lambda: defaultdict(int))
        address_to_name = {d.address: d.name for d in destinations}
        by_mode = self._group_by_mode(destinations)
        for mode, destination_addresses in by_mode.items():

            print(f"Calculating distance matrix for mode={mode}...")
            print(f"Origins: {origins}")
            print(f"Destinations: {destination_addresses}\n")

            response = self._gclient.distance_matrix(units="imperial",
                                                     mode=mode,
                                                     departure_time=MONDAY_9_AM,
                                                     origins=origins,
                                                     destinations=destination_addresses)
            if response["status"] != "OK":
                raise Exception("Failed to caclulate w/ status code: {}".format(response["status"]))

            for i, row in enumerate(response["rows"]):
                for j, col in enumerate(row["elements"]):
                    destination = address_to_name[destination_addresses[j]]
                    origins_to_times[origins[i]][destination] = int(col["duration"]["value"] / 60)
        return origins_to_times

    def distance_matrix(self, origins, destinations):
        """
        Hits and parses the results from Google Distance Matrix API.
        Does not calculate the values in EXTRA_COLUMNS.
        """
        destination_names = [destination.name for destination in destinations]
        matrix = [["Apartment"] + destination_names]
        origins_to_times = self._distance_matrix_by_mode(origins, destinations)
        for origin, dest_times in origins_to_times.items():
            matrix.append([origin] + [dest_times[dname] for dname in destination_names])
        return matrix

    def scores(self, address):
        location = self.geocode(address)
        data = self._walk_client.get(location)
        return [data["walk"]["score"] or "NA", data["transit"]["score"] or "NA"]

    def summary(self, origins, destinations, force=False):
        print(f"Generating summary for {MONDAY_9_AM}...")
        origins = [origin.address for origin in origins]
        if force or self.is_dirty(origins, [destination.name for destination in destinations]):
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
