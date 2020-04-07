from datetime import date
from itertools import zip_longest
from contextlib import contextmanager
from unittest import TestCase, skip
from unittest.mock import patch

import readers.jhucsse_reader
from readers import CaseDayData


sample_data = [
    "Province/State,Country/Region,Lat,Long,1/22/20,1/23/20,1/24/20",
    "Beijing,Mainland China,40.1824,116.4142,14,22,36",
    "Hainan,Mainland China,19.1959,109.7453,4,5,8",
    ",Germany,51,9,0,0,0",
]


def make_rec(country, cumulative_cases_list):
    R = readers.jhucsse_reader.Record
    return R("SomeProvince", country, 0, 0, cumulative_cases_list)


def make_caseday(country, report_date, case_count):
    return CaseDayData(report_date, country, case_count, 0, None, None)


class StreamParserTest(TestCase):
    def parse_stream(self, data=sample_data):
        return readers.jhucsse_reader.parse_stream(iter(data))

    def test_processes_all_records(self):
        result = self.parse_stream()
        self.assertEqual(len(sample_data) - 1, len(list(result)))

    def test_yields_record_tuples(self):
        result = self.parse_stream()
        expected_fields = ("province", "country",
                           "lat", "long",
                           "cumulative_cases")
        self.assertTrue(all(r._fields == expected_fields for r in result))

    def test_copies_basic_values(self):
        result = self.parse_stream()
        expected = [
            ("Beijing", "Mainland China", 40.1824, 116.4142),
            ("Hainan", "Mainland China", 19.1959, 109.7453),
            (None, "Germany", 51, 9),
        ]
        for r, expected in zip_longest(result, expected):
            self.assertEqual(expected, (r.province, r.country, r.lat, r.long))

    def test_copies_cumulative_cases_and_dates(self):
        result = self.parse_stream()
        expected = [
            [(date(2020, 1, 22), 14),
             (date(2020, 1, 23), 22),
             (date(2020, 1, 24), 36)],
            [(date(2020, 1, 22), 4),
             (date(2020, 1, 23), 5),
             (date(2020, 1, 24), 8)],
            [(date(2020, 1, 22), 0),
             (date(2020, 1, 23), 0),
             (date(2020, 1, 24), 0)],
        ]
        for r, expected in zip_longest(result, expected):
            self.assertEqual(expected, r.cumulative_cases)

    def test_discards_empty_reports(self):
        data = [
            "Province/State,Country/Region,Lat,Long,1/1/20,1/2/20",
            "City,Country,0,0,42,",
            "City,Country,0,0,,1",
        ]
        result = self.parse_stream(data)
        self.assertEqual([[(date(2020, 1, 1), 42)], [(date(2020, 1, 2), 1)]],
                         [r.cumulative_cases for r in result])


class CaseDayDataConversionTest(TestCase):
    def casedaydata_from_records(self, data):
        result = readers.jhucsse_reader.casedaydata_from_records(iter(data))
        return list(result)

    def test_merges_countries(self):
        data = [
            make_rec("A", [(None, 10)]),
            make_rec("A", [(None, 20)]),
            make_rec("B", [(None, 30)]),
            make_rec("A", [(None, 40)]),
            make_rec("B", [(None, 50)]),
        ]
        result = self.casedaydata_from_records(data)
        self.assertEqual(["A", "B"], [r.CountryExp for r in result])
        self.assertEqual([70, 80], [r.NewConfCases for r in result])

    def test_yields_caseday_per_country_and_day(self):
        date1 = date(1970, 1, 1)
        date2 = date(1970, 2, 2)
        data = [
            make_rec("Country A", [(date1, 0), (date2, 0)]),
            make_rec("Country B", [(date1, 0), (date2, 0)])
        ]
        result = self.casedaydata_from_records(data)
        expected = {
            make_caseday("Country A", date1, 0),
            make_caseday("Country A", date2, 0),
            make_caseday("Country B", date1, 0),
            make_caseday("Country B", date2, 0),
        }
        self.assertEqual(4, len(result))
        self.assertEqual(expected, set(result))

    def test_converts_cumulative_count_to_per_day_count(self):
        date1 = date(1970, 1, 1)
        date2 = date(1970, 2, 2)
        date3 = date(1970, 3, 3)
        data = [
            make_rec("A", [(date1, 10), (date2, 20)]),
            make_rec("B", [(date1, 100), (date2, 1000)]),
            make_rec("C", [(date1, 0), (date2, 123), (date3, 123)])
        ]
        result = self.casedaydata_from_records(data)
        self.assertEqual(7, len(result))
        self.assertEqual([("A", 10), ("A", 10), ("B", 100), ("B", 900),
                          ("C", 0), ("C", 123), ("C", 0)],
                         [(r.CountryExp, r.NewConfCases) for r in result])

    def test_canonicalizes_country_names(self):
        date1 = date(1970, 1, 1)
        data = [
            make_rec("US", [(date1, 10)]),
            make_rec("Germany", [(date1, 10)]),
        ]
        result = self.casedaydata_from_records(data)
        expected = {
            make_caseday("United States of America", date1, 10),
            make_caseday("Germany", date1, 10),
        }
        self.assertEqual(expected, set(result))

    def test_rejects_conflicting_canonicalization(self):
        date1 = date(1970, 1, 1)
        data = [
            make_rec("United States of America", [(date1, 10)]),
        ]
        with self.assertRaises(ValueError):
            self.casedaydata_from_records(data)


class DailyStatsTest(TestCase):
    def setUp(self):
        self._fetch_patcher = patch("readers.jhucsse_reader.fetch_data")
        self._fetch_mock = self._fetch_patcher.start()

    def tearDown(self):
        self._fetch_patcher.stop()

    def daily_stats(self, data=sample_data):
        def fake_fetch():
            yield iter(data)
        self._fetch_mock.side_effect = contextmanager(fake_fetch)
        return readers.jhucsse_reader.daily_stats()

    def test_yields_casedaydata_with_country_and_cases(self):
        result = self.daily_stats()
        expected = {
            make_caseday("Mainland China", date(2020, 1, 22), 14 + 4),
            make_caseday("Mainland China", date(2020, 1, 23), 8 + 1),
            make_caseday("Mainland China", date(2020, 1, 24), 14 + 3),
            make_caseday("Germany", date(2020, 1, 22), 0),
            make_caseday("Germany", date(2020, 1, 23), 0),
            make_caseday("Germany", date(2020, 1, 24), 0),
        }
        self.assertEqual(expected, set(result))
