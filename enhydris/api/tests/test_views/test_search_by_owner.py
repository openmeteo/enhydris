from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models

from .test_search import SearchTestCaseBase


class SearchByOwnerTestCase(SearchTestCaseBase, APITestCase):
    search_term = "owner:assassination"
    search_result = "Hobbiton"

    def _create_models(self):
        owner1 = mommy.make(models.Organization, name="The Assassination Bureau, Ltd")
        owner2 = mommy.make(models.Organization, name="Société d'assassins")
        owner3 = mommy.make(models.Person, first_name="Joe", last_name="User")
        owner4 = mommy.make(models.Person, first_name="André", last_name="Béart")
        mommy.make(models.Station, owner=owner1, name="Hobbiton")
        mommy.make(models.Station, owner=owner2, name="Rivendell")
        mommy.make(models.Station, owner=owner3, name="Bree")
        mommy.make(models.Station, owner=owner4, name="Fornost")


class SearchByOwnerFirstNameTestCase(SearchByOwnerTestCase):
    search_term = "owner:joe"
    search_result = "Bree"


class SearchByOwnerLastNameTestCase(SearchByOwnerTestCase):
    search_term = "owner:user"
    search_result = "Bree"


class SearchByOwnerOrganizationWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "owner:societe"
    search_result = "Rivendell"


class SearchByOwnerFirstNameWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "owner:andre"
    search_result = "Fornost"


class SearchByOwnerLastNameWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "owner:beart"
    search_result = "Fornost"


# The searches above have tested searching specifically for "owner:X". The ones below
# are the same but they search for a mere "X".


class SearchGeneralByOwnerTestCase(SearchByOwnerTestCase):
    search_term = "assassination"
    search_result = "Hobbiton"


class SearchGeneralByOwnerFirstNameTestCase(SearchByOwnerTestCase):
    search_term = "joe"
    search_result = "Bree"


class SearchGeneralByOwnerLastNameTestCase(SearchByOwnerTestCase):
    search_term = "user"
    search_result = "Bree"


class SearchGeneralByOwnerOrganizationWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "societe"
    search_result = "Rivendell"


class SearchGeneralByOwnerFirstNameWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "andre"
    search_result = "Fornost"


class SearchGeneralByOwnerLastNameWithAccentsTestCase(SearchByOwnerTestCase):
    search_term = "beart"
    search_result = "Fornost"
