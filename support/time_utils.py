import datetime

from pytz import timezone

#from enum import Enum

from astral import Astral

CITY_NAME = 'San Francisco'  # For Sunrise / Sunset detection. Supported cities: http://pythonhosted.org/astral/

LOCAL_TIMEZONE = timezone('US/Pacific')  # For logging datetimes

astral = Astral()
astral.solar_depression = 'civil'
astral_city = astral[CITY_NAME]

# Enums aren't a thing until python 3.5. RPi repository only has 3.4
# class CircadianEvent(Enum):
#     sunrise = 'sunrise'
#     sunset = 'sunset'

SUNRISE = "sunrise"
SUNSET = "sunset"


def get_local_time() -> datetime:
    return datetime.datetime.now(LOCAL_TIMEZONE)


def get_local_sunset(date=None) -> datetime:

    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['sunset']


def get_local_sunrise(date=None) -> datetime:

    if date is None:
        date = datetime.datetime.now(LOCAL_TIMEZONE)

    return astral_city.sun(date=date, local=True)['sunrise']


def get_next_circadian_event() -> (str, datetime):
    sunset = get_local_sunset()
    sunrise = get_local_sunrise()
    now = get_local_time()

    if now < sunrise:
        return SUNRISE, sunrise
    elif now < sunset:
        return SUNSET, sunset
    else:
        # sunrise tomorrow
        return SUNRISE, get_local_sunrise(now + datetime.timedelta(days=1))
