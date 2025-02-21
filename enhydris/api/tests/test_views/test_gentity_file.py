from unittest.mock import MagicMock, mock_open, patch

from django.db.models.fields.files import FieldFile
from django.test import override_settings
from rest_framework.test import APITestCase

from model_bakery import baker

from enhydris import models


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class GentityFileTestCase(APITestCase):
    def setUp(self):
        self.station = baker.make(models.Station)
        self.gentity_file = baker.make(
            models.GentityFile, gentity=self.station, descr="hello"
        )
        self.station2 = baker.make(models.Station)
        self.gentity_file2 = baker.make(models.GentityFile, gentity=self.station2)

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


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
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

        self.station = baker.make(models.Station)
        self.gentity_file = baker.make(models.GentityFile, gentity=self.station)
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


@override_settings(ENHYDRIS_AUTHENTICATION_REQUIRED=False)
class GentityFileContentWithoutFileTestCase(APITestCase):
    def setUp(self):
        # Mommy creates a GentityFile without an associated file, so the
        # result should be 404
        self.station = baker.make(models.Station)
        self.gentity_file = baker.make(models.GentityFile, gentity=self.station)

        self.response = self.client.get(
            "/api/stations/{}/files/{}/content/".format(
                self.station.id, self.gentity_file.id
            )
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 404)
