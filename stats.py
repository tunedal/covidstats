import sys
from collections import defaultdict

import readers.popreader


# Maps the World Bank's country names to ECDC's names.
country_name_map = {
    "Egypt, Arab Rep.": "Egypt",
    "Iran, Islamic Rep.": "Iran",
    "Russian Federation": "Russia",
    "Korea, Rep.": "South Korea",
    "United States": "United States of America",
}


def latest_population_count():
    for r in readers.popreader.latest_population_count():
        canonical_name = country_name_map.get(r.country_name)
        if canonical_name:
            yield r._replace(country_name=canonical_name)
        else:
            yield r


def sum_days(data):
    cases_by_country = defaultdict(int)
    deaths_by_country = defaultdict(int)
    for r in data:
        cases_by_country[r.CountryExp] += r.NewConfCases
        deaths_by_country[r.CountryExp] += r.NewDeaths
    for country in cases_by_country.keys() | deaths_by_country.keys():
        cases = cases_by_country[country]
        deaths = deaths_by_country[country]
        yield country, cases, deaths


def case_density(data_source, countries=[]):
    stats = list(data_source())
    popcount = list(latest_population_count())
    pop_by_country = {p.country_name: p.population
                      for p in popcount}
    country_codes = iso_alpha3_codes(popcount)
    if countries:
        countries_set = set(s.lower() for s in countries)
    else:
        reported_countries = set(r.CountryExp for r in stats)
        countries_set = set(s.lower() for s in
                            pop_by_country.keys() & reported_countries)
    for country, cases, deaths in sum_days(stats):
        if country.lower() in countries_set:
            cases_per_million = 1_000_000 * cases / pop_by_country[country]
            yield country, country_codes[country], cases, cases_per_million


def iso_alpha3_codes(popcount):
    return {p.country_name: p.country_code for p in popcount}


def main():
    countries = set(s.lower() for s in sys.argv[1:])
    pop_by_country = {p.country_name: p.population
                      for p in latest_population_count()}
    data_source = readers.ecdc_source
    for country, cases, deaths in sum_days(data_source()):
        if country.lower() in countries:
            cases_per_million = 1_000_000 * cases / pop_by_country[country]
            print(country, cases, cases_per_million)


if __name__ == "__main__":
    main()
