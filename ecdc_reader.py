# https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases

import sys, re
from pathlib import Path
from collections import namedtuple

import xlrd, requests


ENDPOINT = "https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases"

CaseDayData = namedtuple(
    "CaseDayData", "DateRep CountryExp NewConfCases NewDeaths GeoId EU")


def scrape_for_data_url(url):
    # I know, I know, but this is more extracting than parsing.
    # https://stackoverflow.com/a/1732454
    r = requests.get(url)
    pat = r'<a href="([^"]+\.xls)"[^<]*Download[^<]*</a>'
    m = re.search(pat, r.text)
    return m.group(1)


def fetch_data(filename):
    url = scrape_for_data_url(ENDPOINT)
    r = requests.get(url, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=128):
            f.write(chunk)


def read_file(filename):
    book = xlrd.open_workbook(filename)
    sheet = book.sheet_by_name("CSV_4_COMS")
    rows_iter = sheet.get_rows()

    header = tuple(cell.value for cell in next(rows_iter))
    if header != CaseDayData._fields:
        raise ValueError(f"Unexpected header: {header!r}")

    for row in rows_iter:
        yield CaseDayData._make(cell.value for cell in row)


def sum_country(data, country_name):
    return sum(row.NewConfCases for row in data
               if row.CountryExp == country_name)


def daily_stats():
    # filename = (Path("~/Downloads/").expanduser() /
    #             "COVID-19-geographic-disbtribution"
    #             "-worldwide-5-march-2020.xls")
    filename = Path(__file__).parent / "cases.xls"
    fetch_data(filename)
    return read_file(filename)


if __name__ == "__main__":
    # for data in read_file(sys.argv[1]):
    #     print(data)
    data = read_file(sys.argv[2])
    print(sum_country(data, sys.argv[1]))
