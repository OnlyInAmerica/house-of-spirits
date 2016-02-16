class Room:

    def __init__(self, name: str, lights: [int]):
        """
        :param name: the human-readable room name
        :param lights: the Hue API Ids of contained lights
        """
        self.name = name
        self.lights = lights


ROOMS = {
    "Living Room": Room("Living Room", [1, 2, 3]),
    "Kitchen": Room("Kitchen", [16, 17, 19]),
    "Bedroom": Room("Bedroom", [4, 7, 15, 18]),
    "Stairway": Room("Stairway", [13]),
    "Hallway": Room("Hallway", [14])
}
