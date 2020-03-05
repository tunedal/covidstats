# https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases

import sys
from pathlib import Path
from collections import namedtuple

import xlrd


CaseDayData = namedtuple(
    "CaseDayData", "DateRep CountryExp NewConfCases NewDeaths GeoId EU")


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
    filename = (Path("~/Downloads/").expanduser() /
                "COVID-19-geographic-disbtribution-worldwide-5-march-2020.xls")
    return read_file(filename)


if __name__ == "__main__":
    # for data in read_file(sys.argv[1]):
    #     print(data)
    data = read_file(sys.argv[2])
    print(sum_country(data, sys.argv[1]))
