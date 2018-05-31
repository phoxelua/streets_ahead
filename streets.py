import csv
import googlemaps
import os
from datetime import datetime
from tabulate import tabulate

API_KEY = str(os.environ["API_KEY"])
MONDAY_9_AM = datetime(2018, 6, 18, 9)
EXTRA_COLUMNS = ["Average", "Wt. Average"]


def load_origins():
    return [line.strip() for line in open("origins.txt")]


def load_destinations():
    with open("destinations.csv") as f:
        destinations = []
        reader = csv.reader(f)
        for row in reader:
            destinations.append({"name": row[0], "address": row[1], "comment": row[2], "weight": float(row[3])})
    return destinations


def load_matrix():
    with open("matrix.csv") as f:
        matrix = []
        reader = csv.reader(f)
        for row in reader:
            # The header is the apt then all the points of interest
            # We exclude the EXTRA_COLUMNS on load to force recalculation every time.
            matrix.append(row[:-len(EXTRA_COLUMNS)])
    return matrix


def save_matrix(matrix):
    with open("matrix.csv", "w") as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        # Each row is origin, destination, comment, minutes, miles
        for row in matrix:
            writer.writerow(row)


def print_matrix(matrix, sort_by=None):
    header, rows = matrix[0], matrix[1:]
    if sort_by == 'wa':
        rows = sorted(rows, key=lambda row: row[-1])
    elif sort_by == 'a':
        rows = sorted(rows, key=lambda row: row[-2])
    print(tabulate(rows, headers=header))


def is_dirty(origins, destinations, matrix):
    # We want to trigger an API call and discard our stored results when changes happen in
    # origins.txt, destinations.csv, and matrix.csv.
    # See "Refreshing" in the README for more details.
    if not matrix:
        return True
    matrix_origins = set([row[0] for row in matrix[1:]])

    # The matrix header has all the destinations but need to subtract out labels and EXTRA_COLUMNS
    matrix_destinations = set(matrix[0][1:]) - set(["Apartment"] + EXTRA_COLUMNS)
    return matrix_origins != set(origins) or matrix_destinations != set(destinations)


def mean(array):
    return sum(array) / len(array)


def weighted_mean(array, weights):
    assert len(array) == len(weights)
    return sum([num*wt for num, wt in zip(array, weights)]) / sum(weights)


def fetch_distance_matrix(origins, destinations):
    """
    Hits and parses the results from Google Distance Matrix API.
    Does not calculate the values in EXTRA_COLUMNS.
    """
    destinations_list = [destination["name"] for destination in destinations]
    print("Calculating distance matrix...")
    print("Origins:", origins)
    print("Destinations:", destinations_list)
    gmaps = googlemaps.Client(key=API_KEY)
    response = gmaps.distance_matrix(units="imperial",
                                     mode="transit",
                                     departure_time=MONDAY_9_AM,
                                     origins=origins,
                                     destinations=[destination["address"] for destination in destinations])
    if response["status"] != "OK":
        raise Exception("Failed to caclulate w/ status code: {}".format(response["status"]))

    matrix = [["Apartment"] + destinations_list]
    for i, row in enumerate(response["rows"]):
        minutes = [int(col["duration"]["value"] / 60) for col in row["elements"]]
        matrix.append([origins[i]] + minutes)
    return matrix


def generate_distance_matrix(origins, destinations, matrix):
    if is_dirty(origins, [destination["name"] for destination in destinations], matrix):
        matrix = fetch_distance_matrix(origins, destinations)

    # Extend the Google Distance matrix with our own calculated columns EXTRA_COLUMNS.
    # We handle calculated columns after so that it can be independent of the API call
    weights = [destination["weight"] for destination in destinations]

    # Add EXTRA_COLUMNS headers
    matrix[0].extend(EXTRA_COLUMNS)

    for row in matrix[1:]:
        # Ignore col 0 since that's the origin name
        minutes = list(map(int, row[1:]))
        row.extend([mean(minutes), weighted_mean(minutes, weights)])
    return matrix


if __name__ == "__main__":
    if not API_KEY:
        raise Exception('Source API_KEY.')
    origins, destinations, matrix = load_origins(), load_destinations(), load_matrix()
    matrix = generate_distance_matrix(origins, destinations, matrix)
    save_matrix(matrix)
    print_matrix(matrix, sort_by='wa')
