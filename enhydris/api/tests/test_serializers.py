from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from model_mommy import mommy

from enhydris import models
from enhydris.api.serializers import StationSerializer


class StationSerializerTestCase(APITestCase):
    def setUp(self):
        station = mommy.make(
            models.Station,
            name="hello",
            overseer="Bilbo Baggins",
            maintainers=[mommy.make(User, username="Bilbo")],
        )
        self.serializer = StationSerializer(station)

    def test_name(self):
        self.assertEqual(self.serializer.data["name"], "hello")

    def test_overseer(self):
        self.assertEqual(self.serializer.data["overseer"], "Bilbo Baggins")

    def test_no_maintainers(self):
        # There shouldn't be information about maintainers, this is security information
        self.assertTrue("maintainers" not in self.serializer.data)
