# https://data.worldbank.org/indicator/SP.POP.TOTL

import time
from pathlib import Path
from collections import namedtuple

import xlrd, requests


ENDPOINT = ("https://api.worldbank.org/v2/en/indicator/" +
            "SP.POP.TOTL?downloadformat=excel")

CACHE_DIR = Path(__file__).parent


PopData = namedtuple(
    "PopData", "country_name country_code year population")



def fetch_data(filename):
    r = requests.get(ENDPOINT, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=128):
            f.write(chunk)


def update_data(filename, max_age_days=7):
    filename = Path(filename)
    deadline = filename.stat().st_mtime + max_age_days * 24 * 3600
    now = time.time()
    if deadline <= now:
        fetch_data(filename)


def read_data_rows(filename):
    book = xlrd.open_workbook(filename)
    sheet = book.sheet_by_name("Data")
    rows_iter = sheet.get_rows()

    def is_header(values):
        header = ("Country Name", "Country Code", "Indicator Name",
                  "Indicator Code")
        if values[0:len(header)] != header:
            return False
        if not all(0 < int(year) < 10000 for year in values[len(header):]):
            return False
        return True

    for row in rows_iter:
        values = tuple(cell.value for cell in row)
        if is_header(values):
            yield values
            break
    else:
        raise Exception("Failed to find column header")


    for row in rows_iter:
        yield tuple(cell.value for cell in row)


def parse_data(rows):
    rows_iter = iter(rows)
    header = next(rows_iter)
    for row in rows:
        for i in range(len(row) - 1, 3, -1):
            if row[i]:
                latest_index = i
                break
        else:
            continue            # no data for this country
        pop = row[latest_index]
        year = int(header[latest_index])
        yield PopData(country_name=row[0],
                      country_code=row[1],
                      year=year,
                      population=int(pop))


def latest_population_count():
    datafile = CACHE_DIR / "pop.xls"
    update_data(datafile)
    data = read_data_rows(datafile)
    return parse_data(data)


if __name__ == "__main__":
    for r in sorted(latest_population_count(), key=lambda r: r.country_name):
        print(f"{r.country_name}: {r.population} people (as of {r.year})")
