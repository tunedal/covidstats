from datetime import date
from unittest import TestCase
from itertools import zip_longest

import readers.jhucsse_reader


sample_data = [
    "Province/State,Country/Region,Lat,Long,1/22/20,1/23/20,1/24/20",
    "Beijing,Mainland China,40.1824,116.4142,14,22,36",
    "Hainan,Mainland China,19.1959,109.7453,4,5,8",
    ",Germany,51,9,0,0,0",
]


class StreamParserTest(TestCase):
    def parse_stream(self):
        return readers.jhucsse_reader.parse_stream(iter(sample_data))

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
