import csv
import sys
from streets_ahead import StreetsAheadService, Location
from utils import print_matrix


def load_origins():
    return [Location(line.strip()) for line in open("origins.txt")]


def load_destinations():
    destinations = []
    with open("destinations.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            destinations.append(Location(name=row[0], address=row[1], comment=row[2], weight=float(row[3]), mode=row[4]))
    return destinations


if __name__ == "__main__":
    force = len(sys.argv) == 2 and sys.argv[1] in {"--force", "-f"}
    streets_ahead = StreetsAheadService()
    origins, destinations = load_origins(), load_destinations()
    matrix = streets_ahead.summary(origins, destinations, force=force)
    print_matrix(matrix, sort_by='wa')
