import os
import shutil
from io import StringIO
from tempfile import mkdtemp
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase

from model_mommy import mommy
from osgeo import ogr, osr

from enhydris import models
from enhydris.admin.garea import GareaAdmin, MissingAttribute


class GareaChangeListTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        self.client.force_login(user=self.alice)
        self.response = self.client.get("/admin/enhydris/garea/")

    def test_has_no_add_button(self):
        self.assertNotContains(self.response, "Add garea")

    def test_has_upload_shapefile_button(self):
        self.assertContains(self.response, "Upload shapefile")


class GareaBulkAddGetTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        self.client.force_login(user=self.alice)
        self.response = self.client.get("/admin/enhydris/garea/bulk_add/")

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_content(self):
        self.assertContains(self.response, "The shapefile.")


class GareaBulkAddPostSuccessfulTestCase(TestCase):
    patch1 = patch(
        "enhydris.admin.garea.ZipFile",
        **{"return_value.namelist.return_value": [".shp", ".shx", ".dbf"]},
    )
    patch2 = patch(
        "enhydris.admin.garea.GareaAdmin._process_uploaded_shapefile",
        return_value=(18, 5),
    )

    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        self.water_basins = mommy.make(models.GareaCategory, descr="Water basins")
        self.client.force_login(user=self.alice)
        with self.patch1, self.patch2:
            self.response = self.client.post(
                "/admin/enhydris/garea/bulk_add/",
                {"category": [self.water_basins.id], "file": StringIO("hello")},
            )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 302)

    def test_message(self):
        messages = list(get_messages(self.response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            "Replaced 5 existing objects in category Water basins with 18 new objects",
        )


class GareaBulkAddPostBadZipFileTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username="alice", password="topsecret", is_staff=True, is_superuser=True
        )
        self.water_basins = mommy.make(models.GareaCategory, descr="Water basins")
        self.client.force_login(user=self.alice)
        self.response = self.client.post(
            "/admin/enhydris/garea/bulk_add/",
            {"categories": [self.water_basins.id], "file": StringIO("hello")},
        )

    def test_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_message(self):
        self.assertContains(
            self.response,
            "This is not a zip file, or it doesn&#39;t contain exactly one .shp, .shx "
            "and .dbf file.",
            html=True,
        )


class ProcessUploadedShapefileTestCaseBase(TestCase):
    def setUp(self):
        self.tempdir = mkdtemp()
        self._get_filenames()
        self._create_data_in_database()
        self._create_test_shapefile()

    def _get_filenames(self):
        self.shp_filename = os.path.join(self.tempdir, "myshapefile.shp")
        self.shx_filename = os.path.join(self.tempdir, "myshapefile.shx")
        self.dbf_filename = os.path.join(self.tempdir, "myshapefile.dbf")
        self.zip_filename = os.path.join(self.tempdir, "myshapefile.zip")

    def _create_data_in_database(self):
        self.water_basins = mommy.make(models.GareaCategory, descr="Water basins")
        self.countries = mommy.make(models.GareaCategory, descr="Countries")

    def _create_test_shapefile(self):
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(self.shp_filename)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        layer = data_source.CreateLayer("Water basins", srs, ogr.wkbMultiPolygon)
        self._create_layer_fields(layer)
        self._add_entities(layer)
        data_source = None
        with ZipFile(self.zip_filename, "w") as myzip:
            myzip.write(self.shp_filename)
            myzip.write(self.shx_filename)
            myzip.write(self.dbf_filename)

    def _create_layer_fields(self, layer):
        self._create_string_field(layer, "Name")
        self._create_string_field(layer, "Code")

    def _create_string_field(self, layer, fieldname, width=24):
        field = ogr.FieldDefn(fieldname, ogr.OFTString)
        field.SetWidth(width)
        layer.CreateField(field)

    def _add_entities(self, layer):
        for item in self.entities:
            feature = ogr.Feature(layer.GetLayerDefn())
            for attrname in item:
                feature.SetField(attrname, item[attrname])
            entity = ogr.CreateGeometryFromWkt(item["wkt"])
            feature.SetGeometry(entity)
            layer.CreateFeature(feature)
            feature = None

    def _process_shapefile(self):
        self.result = GareaAdmin(MagicMock(), MagicMock())._process_uploaded_shapefile(
            self.water_basins, self.zip_filename
        )

    def tearDown(self):
        shutil.rmtree(self.tempdir)


class ProcessUploadedShapefileTestCase(ProcessUploadedShapefileTestCaseBase):
    entities = [
        {
            "Name": "Esgalduin",
            "wkt": (
                "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), "
                "((15 5, 40 10, 10 20, 5 10, 15 5)))"
            ),
        },
        {
            "Name": "Celduin",
            "Code": "ME05",
            "wkt": (
                "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), "
                "((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), "
                "(30 20, 20 15, 20 25, 30 20)))"
            ),
        },
    ]

    def setUp(self):
        super().setUp()
        self._process_shapefile()

    def test_return_value(self):
        self.assertEqual(self.result, (2, 0))

    def test_esgalduin_area(self):
        esgalduin = models.Garea.objects.get(name="Esgalduin").geom
        self.assertAlmostEqual(esgalduin.area, 612.5)

    def test_esgalduin_code(self):
        self.assertEqual(models.Garea.objects.get(name="Esgalduin").code, "")

    def test_celduin_code(self):
        self.assertEqual(models.Garea.objects.get(name="Celduin").code, "ME05")


class WithMissingNameTestCase(ProcessUploadedShapefileTestCaseBase):
    entities = [
        {
            "Name": "Esgalduin",
            "wkt": (
                "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), "
                "((15 5, 40 10, 10 20, 5 10, 15 5)))"
            ),
        },
        {
            "wkt": (
                "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), "
                "((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), "
                "(30 20, 20 15, 20 25, 30 20)))"
            )
        },
    ]

    def test_raises_correct_error(self):
        msg = 'Feature with fid=1 does not have a "Name" attribute'
        with self.assertRaisesRegex(MissingAttribute, msg):
            self._process_shapefile()
