# House of Spirits

A collection of light management programs designed for Raspberry Pi and Hue.

## Top-Level routines

The following are always-running:

+ `circadian.py` : Adjusts the hue of lights on each sunset and sunrise
+ `motion.py` : Switches lights on in response to motion events, and off after a period of no motion.

The following are one-shot:

+ `wakeup.py` : Fades bedroom lights on over 30m.
+ 'weather.py' : Fetches the day's cloud cover and writes it to `weather.FORECAST_FILENAME` in this directory

## SECRETS.py

```
FORECAST_IO_KEY = "your_key"

# Key used to credential clients over HTTPS API
HTTPS_API_KEY = "your_key"
SSL_CERT_PEM = "/path/to/your/cert.pem"
SSL_KEY_PEM = "/paty/to/your/privkey.pem"
```

## Crontab configuration

Note the system timezone is America/LosAngeles.

```
@reboot sh /home/pi/python/motion.sh
@reboot sh /home/pi/python/circadian.sh
@reboot sh /home/pi/python/web_server.sh

# Wakeup weekdays 7:30a, weekends 9:30a
30 7 * * mon-fri /usr/bin/python3 /home/pi/python/wakeup.py
30 9 * * sat,sun /usr/bin/python3 /home/pi/python/wakeup.py

# Fetch forecast daily 5:00a
* 5 * * * sh /home/pi/python/weather.sh
```

## Sending to Raspberry Pi

    rsync -a --exclude-from 'rsync-excludes.txt' ./ pi@lights.home:/home/pi/python/

## Testing webserver

    The webserver has a single API for notifying of your arrival

    curl -H "Content-Type: application/json" -X POST -d '{"token":"TOKEN"}' https://home.dbro.pro/arrive
