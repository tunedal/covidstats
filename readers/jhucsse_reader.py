import csv, datetime
from contextlib import contextmanager
from collections import namedtuple, defaultdict
from itertools import groupby
from operator import itemgetter

from readers import CaseDayData


ENDPOINT = ("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/"
            "master/csse_covid_19_data/csse_covid_19_time_series/"
            "time_series_covid19_confirmed_global.csv")

Record = namedtuple("Record", "province country lat long cumulative_cases")

# Treat ECDC's country names as canonical.
country_name_map = {
    "US": "United States of America",
    "Korea, South": "South Korea",
}


class JhuCsseDataSource:
    name = ("Johns Hopkins University"
            " Center for Systems Science and Engineering")
    info_url = ("https://data.humdata.org/dataset/"
                "novel-coronavirus-2019-ncov-cases")

    def __iter__(self):
        return daily_stats()


@contextmanager
def fetch_data():
    import requests             # a bit slow to import
    response = requests.get(ENDPOINT, stream=True)
    with response:
        response.raise_for_status()
        yield response.iter_lines(decode_unicode=True)


def parse_stream(stream):
    for data in csv.DictReader(stream):
        yield parse_record(data)


def parse_record(data):
    case_counts = [(parse_american_date(k), int(v)) for k, v in data.items()
                   if k[0].isnumeric() and v]
    return Record(province=data["Province/State"] or None,
                  country=data["Country/Region"] or None,
                  lat=float(data["Lat"]),
                  long=float(data["Long"]),
                  cumulative_cases=case_counts)


def parse_american_date(datestr):
    return datetime.datetime.strptime(datestr, "%m/%d/%y").date()


def daily_stats():
    with fetch_data() as stream:
        yield from casedaydata_from_records(parse_stream(stream))


def casedaydata_from_records(records):
    cases_by_country_and_date = defaultdict(int)
    for r in records:
        for d, cumulative_count in r.cumulative_cases:
            cases_by_country_and_date[(r.country, d)] += cumulative_count

    sorted_data = sorted((country, d, cases) for (country, d), cases
                         in cases_by_country_and_date.items())
    for country, g in groupby(sorted_data, key=itemgetter(0)):
        if country in country_name_map.values():
            raise ValueError(f"Ambiguous name {country!r}")
        canonical_country_name = country_name_map.get(country, country)
        preexisting_cases = 0
        for _, d, cases in g:
            new_cases = cases - preexisting_cases
            preexisting_cases = cases
            yield CaseDayData(
                DateRep=d,
                CountryExp=canonical_country_name,
                NewConfCases=new_cases,
                NewDeaths=0,
                GeoId=None,
                EU=None)
