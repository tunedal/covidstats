from collections import namedtuple


CaseDayData = namedtuple(
    "CaseDayData",
    "DateRep CountryExp NewConfCases NewDeaths GeoId EU")


from .ecdc_reader import daily_stats as ecdc_source
from .jhucsse_reader import daily_stats as jhucsse_source
