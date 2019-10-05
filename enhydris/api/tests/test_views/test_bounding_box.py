from django.contrib.gis.geos import Point
from django.test import override_settings
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models


class SimpleBoundingBoxTestCase(APITestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            models.Station,
            geom=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        response = self.client.get("/api/stations/")
        self.bounding_box = response.json()["bounding_box"]

    def test_x1(self):
        self.assertAlmostEqual(self.bounding_box[0], 21.06071)

    def test_y1(self):
        self.assertAlmostEqual(self.bounding_box[1], 39.09518)

    def test_x2(self):
        self.assertAlmostEqual(self.bounding_box[2], 21.60121)

    def test_y2(self):
        self.assertAlmostEqual(self.bounding_box[3], 39.22440)


@override_settings(ENHYDRIS_MAP_DEFAULT_VIEWPORT=(1.0, 2.0, 3.0, 4.0))
class DefaultBoundingBoxTestCase(APITestCase):
    def setUp(self):
        response = self.client.get("/api/stations/")
        self.bounding_box = response.json()["bounding_box"]

    def test_x1(self):
        self.assertAlmostEqual(self.bounding_box[0], 1.0)

    def test_y1(self):
        self.assertAlmostEqual(self.bounding_box[1], 2.0)

    def test_x2(self):
        self.assertAlmostEqual(self.bounding_box[2], 3.0)

    def test_y2(self):
        self.assertAlmostEqual(self.bounding_box[3], 4.0)


@override_settings(ENHYDRIS_MAP_MIN_VIEWPORT_SIZE=1.0)
class TooSmallBoundingBoxTestCase(APITestCase):
    def setUp(self):
        mommy.make(
            models.Station,
            geom=Point(x=21.06071, y=39.09518, srid=4326),
            original_srid=4326,
        )
        mommy.make(
            models.Station,
            geom=Point(x=21.60121, y=39.22440, srid=4326),
            original_srid=4326,
        )
        response = self.client.get("/api/stations/")
        self.bounding_box = response.json()["bounding_box"]

    def test_x1(self):
        self.assertAlmostEqual(self.bounding_box[0], 20.83096)

    def test_y1(self):
        self.assertAlmostEqual(self.bounding_box[1], 38.65979)

    def test_x2(self):
        self.assertAlmostEqual(self.bounding_box[2], 21.83096)

    def test_y2(self):
        self.assertAlmostEqual(self.bounding_box[3], 39.65979)
