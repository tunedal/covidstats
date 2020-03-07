# Data source:
# Johns Hopkins University Center for Systems Science and Engineering
# https://data.humdata.org/dataset/novel-coronavirus-2019-ncov-cases

import csv, datetime
from contextlib import contextmanager
from collections import namedtuple


ENDPOINT = ("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/"
            "master/csse_covid_19_data/csse_covid_19_time_series/"
            "time_series_19-covid-Confirmed.csv")

Record = namedtuple("Record", "province country lat long cumulative_cases")


@contextmanager
def fetch_data():
    import requests             # a bit slow to import
    response = requests.get(ENDPOINT, stream=True)
    with response:
        yield response.iter_lines(decode_unicode=True)


def parse_stream(stream):
    for data in csv.DictReader(stream):
        yield parse_record(data)


def parse_record(data):
    case_counts = [(parse_american_date(k), int(v)) for k, v in data.items()
                   if k[0].isnumeric()]
    return Record(province=data["Province/State"] or None,
                  country=data["Country/Region"] or None,
                  lat=float(data["Lat"]),
                  long=float(data["Long"]),
                  cumulative_cases=case_counts)


def parse_american_date(datestr):
    return datetime.datetime.strptime(datestr, "%m/%d/%y").date()
