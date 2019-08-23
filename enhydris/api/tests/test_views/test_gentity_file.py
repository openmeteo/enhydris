from unittest.mock import MagicMock, mock_open, patch

from django.contrib.auth.models import User
from django.db.models.fields.files import FieldFile
from django.test.utils import override_settings
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class GentityFileTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(
            models.GentityFile, gentity=self.station, descr="hello"
        )
        self.station2 = mommy.make(models.Station)
        self.gentity_file2 = mommy.make(models.GentityFile, gentity=self.station2)

    def test_list_status_code(self):
        r = self.client.get("/api/stations/{}/files/".format(self.station.id))
        self.assertEqual(r.status_code, 200)

    def test_list_length(self):
        r = self.client.get("/api/stations/{}/files/".format(self.station.id))
        self.assertEqual(len(r.json()["results"]), 1)

    def test_list_content(self):
        r = self.client.get("/api/stations/{}/files/".format(self.station.id))
        self.assertEqual(r.json()["results"][0]["descr"], "hello")

    def test_detail_status_code(self):
        r = self.client.get(
            "/api/stations/{}/files/{}/".format(self.station.id, self.gentity_file.id)
        )
        self.assertEqual(r.status_code, 200)

    def test_detail_content(self):
        r = self.client.get(
            "/api/stations/{}/files/{}/".format(self.station.id, self.gentity_file.id)
        )
        self.assertEqual(r.json()["descr"], "hello")

    def test_detail_returns_nothing_if_wrong_station(self):
        r = self.client.get(
            "/api/stations/{}/files/{}/".format(self.station2.id, self.gentity_file.id)
        )
        self.assertEqual(r.status_code, 404)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class GentityFileContentTestCase(APITestCase):
    def setUp(self):
        # Mocking. We mock several things in Django and Python so that:
        #   1) The name of the file appears to be some_image.jpg
        #   2) Its data appears to be ABCDEF
        #   3) Its size appears to be 6
        self.saved_fieldfile_file = FieldFile.file
        self.filemock = MagicMock(**{"return_value.name": "some_image.jpg"})
        FieldFile.file = property(self.filemock, MagicMock(), MagicMock())
        patch1 = patch("enhydris.api.views.open", mock_open(read_data="ABCDEF"))
        patch2 = patch("os.path.getsize", return_value=6)

        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)
        with patch1, patch2:
            self.response = self.client.get(
                "/api/stations/{}/files/{}/content/".format(
                    self.station.id, self.gentity_file.id
                )
            )

    def tearDown(self):
        FieldFile.file = self.saved_fieldfile_file

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content(self):
        self.assertEqual(self.response.content, b"ABCDEF")

    def test_content_type(self):
        self.assertEqual(self.response["Content-Type"], "image/jpeg")


@override_settings(ENHYDRIS_OPEN_CONTENT=False)
@patch("enhydris.api.views.open", mock_open(read_data="ABCDEF"))
@patch("os.path.getsize", return_value=6)
class GentityFileContentPermissionsTestCase(APITestCase):
    def setUp(self):
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)
        self.url = "/api/stations/{}/files/{}/content/".format(
            self.station.id, self.gentity_file.id
        )
        self.saved_fieldfile_file = FieldFile.file
        self.filemock = MagicMock(**{"return_value.name": "some_image.jpg"})
        FieldFile.file = property(self.filemock, MagicMock(), MagicMock())

    def tearDown(self):
        FieldFile.file = self.saved_fieldfile_file

    def test_anonymous_user_is_denied(self, m):
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 401)

    def test_logged_on_user_is_ok(self, m):
        self.user1 = mommy.make(User, is_active=True, is_superuser=False)
        self.client.force_authenticate(user=self.user1)
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)


@override_settings(ENHYDRIS_OPEN_CONTENT=True)
class GentityFileContentWithoutFileTestCase(APITestCase):
    def setUp(self):
        # Mommy creates a GentityFile without an associated file, so the
        # result should be 404
        self.station = mommy.make(models.Station)
        self.gentity_file = mommy.make(models.GentityFile, gentity=self.station)

        self.response = self.client.get(
            "/api/stations/{}/files/{}/content/".format(
                self.station.id, self.gentity_file.id
            )
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 404)
