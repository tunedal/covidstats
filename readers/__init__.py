from collections import namedtuple


CaseDayData = namedtuple(
    "CaseDayData",
    "DateRep CountryExp NewConfCases NewDeaths GeoId EU")


def __getattr__(name):
    if name == "ecdc_source":
        from .ecdc_reader import EcdcDataSource
        return EcdcDataSource
    elif name == "jhucsse_source":
        from .jhucsse_reader import JhuCsseDataSource
        return JhuCsseDataSource
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
