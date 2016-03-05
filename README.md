# House of Spirits

A collection of light management programs designed for Raspberry Pi and Hue.

## Top-Level routines

The following always-running scripts are run on boot on the Raspberry Pi.

+ `circadian.py` : Adjusts the hue of lights on each sunset and sunrise
+ `motion.py` : Switches lights on in response to motion events, and off after a period of no motion.

The following one-shot scripts are run on a schedule managed with cron:

+ `wakeup.py` : Fades bedroom lights on over 30m.