from django.utils.translation import ugettext as _


def check_latitude(latitude):
    if latitude > 90 or latitude < -90:
        raise Exception(_("%f is not a valid latitude") % (latitude,))


def check_longitude(longitude):
    if longitude > 180 or longitude < -180:
        raise Exception(_("%f is not a valid longitude") % (longitude,))


def check_altitude(altitude):
    if altitude > 8850 or altitude < -422:
        raise Exception(_("%f is not a valid altitude") % (altitude,))
