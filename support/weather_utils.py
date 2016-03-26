import json

from weather import FORECAST_FILENAME


def is_cloudy(threshold: float = .5) -> bool:
    return get_cloud_cover() > threshold


def get_cloud_cover() -> float:
    """
    Get cloud cover from the local forecast file. See weather.py for forecast details
    :return: the day-wide cloud cover percentage between 0 and 1
    """
    try:
        forecast_file = open(FORECAST_FILENAME, 'r')
        forecast = json.loads(forecast_file.read())
        forecast_file.close()
        cloud_cover = forecast["cloud_cover"]
    except FileNotFoundError:
        cloud_cover = 0

    return cloud_cover
