from unittest import TestCase
from unittest.mock import patch


from readers.popreader import PopData, latest_population_count


class LatestPopulationCountTest(TestCase):
    def test_appends_supplemental_data(self):
        file_data = iter([])
        supplement = PopData(country_name="Country 1",
                             country_code="ONE",
                             year=1970,
                             population=1000)

        with patch("readers.popreader._get_file_data", lambda: file_data), \
             patch("readers.popreader.supplemental_data", [supplement]):
            data = list(latest_population_count())

        self.assertIn(supplement, data)
