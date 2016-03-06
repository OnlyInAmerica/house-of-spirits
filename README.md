# House of Spirits

A collection of light management programs designed for Raspberry Pi and Hue.

## Top-Level routines

The following are always-running:

+ `circadian.py` : Adjusts the hue of lights on each sunset and sunrise
+ `motion.py` : Switches lights on in response to motion events, and off after a period of no motion.

The following are one-shot:

+ `wakeup.py` : Fades bedroom lights on over 30m.
+ 'weather.py' : Fetches the day's cloud cover and writes it to `weather.FORECAST_FILENAME` in this directory

## Crontab configuration

```
# Begin monitoring motion and circadian cycles on boot
@reboot /usr/bin/python3 /home/pi/python/motion.py
@reboot /usr/bin/python3 /home/pi/python/circadian.py

# Wakeup weekdays 7:30a, weekends 9:30a
30 15 * * mon-fri /usr/bin/python3 /home/pi/python/wakeup.py
30 17 * * sat,sun /usr/bin/python3 /home/pi/python/wakeup.py

# Fetch forecast daily 5:00a
* 12 * * * /usr/bin/python3 /home/pi/python/weather.py
```

## Sending to Raspberry Pi

    rsync -a --exclude-from 'rsync-excludes.txt' ./ pi@lights.home:/home/pi/python/
