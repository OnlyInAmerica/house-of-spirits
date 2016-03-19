import json

import forecastio

from SECRETS import FORECAST_IO_KEY
from support.time_utils import get_local_time

FORECAST_FILENAME = 'forecast.json'
LAT = 37.877881
LON = -122.269312

forecast_file = open(FORECAST_FILENAME, 'w')
current_time = get_local_time()
forecast = forecastio.load_forecast(FORECAST_IO_KEY, LAT, LON, time=current_time, lazy=True)

cloud_cover = forecast.daily().data[0].d['cloudCover']

forecast_data = {
    'date': current_time.isoformat(),
    'cloud_cover': cloud_cover
}

forecast_file.write(json.dumps(forecast_data))
forecast_file.close()
