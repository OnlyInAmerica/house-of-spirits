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

'''
Forecastio daily data point has the following properties, 
some may be undefined if they do not apply to that day's weather:

{ 'd': { 'apparentTemperatureMax': 59.55,
         'apparentTemperatureMaxTime': 1457204400,
         'apparentTemperatureMin': 57.26,
         'apparentTemperatureMinTime': 1457186400,
         'cloudCover': 0.82,
         'dewPoint': 55.44,
         'humidity': 0.89,
         'icon': 'rain',
         'moonPhase': 0.88,
         'ozone': 338.58,
         'precipIntensity': 0.0647,
         'precipIntensityMax': 0.2725,
         'precipIntensityMaxTime': 1457226000,
         'precipProbability': 0.87,
         'precipType': 'rain',
         'pressure': 1008.4,
         'summary': 'Heavy rain throughout the day and breezy in the '
                    'evening.',
         'sunriseTime': 1457188535,
         'sunsetTime': 1457230089,
         'temperatureMax': 59.55,
         'temperatureMaxTime': 1457204400,
         'temperatureMin': 57.26,
         'temperatureMinTime': 1457186400,
         'time': 1457164800,
         'visibility': 8.12,
         'windBearing': 188,
         'windSpeed': 10.13},
  'sunriseTime': datetime.datetime(2016, 3, 5, 14, 35, 35),
  'sunsetTime': datetime.datetime(2016, 3, 6, 2, 8, 9),
  'time': datetime.datetime(2016, 3, 5, 8, 0),
  'utime': 1457164800}
'''
cloud_cover = forecast.daily().data[0].d['cloudCover']


forecast_data = {
    'date': current_time.isoformat(),
    'cloud_cover': cloud_cover
}

forecast_file.write(json.dumps(forecast_data))
forecast_file.close()
