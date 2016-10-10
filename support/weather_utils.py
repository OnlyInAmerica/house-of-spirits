from support import env


def is_cloudy(threshold: float = .5) -> bool:
    return get_cloud_cover() > threshold


def get_cloud_cover() -> float:
    """
    Get cloud cover from the local forecast file. See weather.py for forecast details
    :return: the day-wide cloud cover percentage between 0 and 1
    """
    return env.get_cloud_cover()
