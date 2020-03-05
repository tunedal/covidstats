import sys
from collections import defaultdict

import ecdc_reader, popreader


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


def main():
    countries = set(s.lower() for s in sys.argv[1:])
    pop_by_country = {p.country_name: p.population
                      for p in popreader.latest_population_count()}
    for country, cases, deaths in sum_days(ecdc_reader.daily_stats()):
        if country.lower() in countries:
            cases_per_million = 1_000_000 * cases / pop_by_country[country]
            print(country, cases, cases_per_million)


if __name__ == "__main__":
    main()
