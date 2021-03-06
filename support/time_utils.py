import datetime

import astral
from pytz import timezone

# from enum import Enum

CITY_NAME = 'San Francisco'  # For Sunrise / Sunset detection. Supported cities: http://pythonhosted.org/astral/

LOCAL_TIMEZONE = timezone('US/Pacific')  # For logging datetimes

_astral = astral.Astral()
_astral.solar_depression = 'civil'
astral_city = _astral[CITY_NAME]

# Enums aren't a thing until python 3.5. RPi repository only has 3.4
# class CircadianEvent(Enum):
#     sunrise = 'sunrise'
#     sunset = 'sunset'

SUNRISE = "sunrise"
SUNSET = "sunset"
DUSK = "dusk"


def get_local_time() -> datetime:
    return datetime.datetime.now(LOCAL_TIMEZONE)


def get_local_sunset(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['sunset']


def get_local_dusk(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['dusk']


def get_local_dawn(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['dawn']


def get_local_sunrise(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['sunrise']


def get_local_noon(date: datetime = None) -> datetime:
    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['noon']


def get_time_at_first_lit_elevation(date: datetime = None):
    return astral_city.time_at_elevation(elevation=10, date=date)


def get_local_solar_elevation(date: datetime = None):
    return astral_city.solar_elevation(dateandtime=date)


def get_time_at_elevation(elevation_deg: float, date: datetime = None, direction=astral.SUN_SETTING):

    while True:
        try:
            return astral_city.time_at_elevation(elevation_deg, direction=direction, date=date, local=True)
        except astral.AstralError:
            print("Sun does not reach elevation %f, trying another" % elevation_deg)
            if elevation_deg >= 0:
                return get_time_at_elevation(elevation_deg-1, date, direction)
            else:
                return get_time_at_elevation(elevation_deg+1, date, direction)