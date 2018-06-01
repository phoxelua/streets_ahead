# STREETS AHEAD

View the transit times from a list of candidate apartments to a list of points of interests.

Aka literally use Google Distance Matrix API to create...a distance matrix.


## Setup

In virtualenv with python 3.6:

`pip install -r requirements.txt`

In an env file `.streets` put your Google API key like so `export GOOGLE_API_KEY=<your-secret-here>`. Then run `source .streets`.

## Run

1. Put apartment name or address on the new-line separated file `origins.txt`

2. Put your points of interest in `destinations.csv`. The columns are:
    
    1. Human-friendly display name
    2. Address or distinct enough name that you would type into Google Maps search
    3. Comment (not used yet but good for notes)
    4. Weight (i.e.- # of days out of 30 you would go to this hotspot/area)
    
    For example,

    ```Google,"111 8th Ave, New York, NY 10011",Work,22```

    See `destinations.csv` for more examples.

3. Run it

   `python main.py`

   This will save a the results of your run in `matrix.csv` to save repeat API calls.


## Refreshing

The following actions will cause the executable to refresh and recall the APIs:

- Add/delete/change a row in `origins.txt`
- Add/delete a row or change the any first column value in `destinations.csv`
- Add/delete/change a row in `matrix.csv`

Basically `matrix.csv` should be the cartesian product of `origins.txt` and `destinations.csv`- if there is a discrepancy it will do afull API refresh.
