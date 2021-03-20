import datetime
from tabulate import tabulate


def print_matrix(matrix, sort_by=None):
    header, rows = matrix[0], matrix[1:]
    if sort_by == 'wa':
        rows = sorted(rows, key=lambda row: row[-1])
    elif sort_by == 'a':
        rows = sorted(rows, key=lambda row: row[-2])
    print(tabulate(rows, headers=header))


def mean(array):
    return sum(array) / len(array)


def weighted_mean(array, weights):
    assert len(array) == len(weights)
    return sum([num*wt for num, wt in zip(array, weights)]) / sum(weights)


def next_monday():
    # Get the next Monday 9 am
    now =  datetime.date.today()
    shift = (-now.weekday()) % 7
    next = now + datetime.timedelta(days=shift) 
    return datetime.datetime(next.year, next.month, next.day, 9)
