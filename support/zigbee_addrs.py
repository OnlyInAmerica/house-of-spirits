# This must be a python 2 compatible file, because
# the Zigbee packet parsing library used has no python 3 support
# and this file is intended for sharing between that library
# and the python3 light control components

SENSOR_ADDR_TO_NAME = {
    6623462419764822: "Living Room Sensor",
    6623462419746382: "Kitchen Sensor",
    6623462419764631: "Kitchen Hall Sensor"
}

SENSOR_NAME_TO_ADDR = {
    "Living Room Sensor": 6623462419746382,
    "Kitchen Sensor": 6623462419746382,
    "Kitchen Hall Sensor": 6623462419764631
}