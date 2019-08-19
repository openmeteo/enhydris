from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models

from .test_search import SearchTestCaseBase


class SearchBy2ndLevelPoliticalDivisionTest(SearchTestCaseBase, APITestCase):
    search_term = "political_division:cardolan"
    search_result = "Tharbad"

    def _create_models(self):
        mommy.make(
            models.Station,
            name="Verquières",
            political_division__name="Châteaurenard",
            political_division__parent__name="Bouches-du-Rhône",
            political_division__parent__parent__name="France extrême",
        )
        mommy.make(
            models.Station,
            name="Tharbad",
            political_division__name="Cardolan",
            political_division__parent__name="Eriador",
            political_division__parent__parent__name="Middle Earth",
        )


class SearchBy3rdLevelPolDivTest(SearchBy2ndLevelPoliticalDivisionTest):
    search_term = "political_division:earth"
    search_result = "Tharbad"


class SearchBy2ndLevelPolDivWithAccentsTest(SearchBy2ndLevelPoliticalDivisionTest):
    search_term = "political_division:rhone"
    search_result = "Verquières"


class SearchBy3rdLevelPolDivWithAccentsTest(SearchBy2ndLevelPoliticalDivisionTest):
    search_term = "political_division:extreme"
    search_result = "Verquières"


# The tests above have tested search specifically for "political_division:X". The ones
# below are for searching for a mere "X". However, this works only for the first level.


class SearchGeneralPolDivTest(SearchBy2ndLevelPoliticalDivisionTest):
    search_term = "cardolan"
    search_result = "Tharbad"


class SearchGeneralPolDivWithAccentsTest(SearchBy2ndLevelPoliticalDivisionTest):
    search_term = "chateaurenard"
    search_result = "Verquières"
