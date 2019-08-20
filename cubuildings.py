import pandas as pd
import json


class BuildingGrabber:

    def __init__(self):
        self.reloadDataframe()

    def reloadDataframe(self):
        self.building_map = {}
        self.address_map = {}
        with open("BuildingMap.json", "r") as f:
            data = json.loads(f.read())
            self.building_map = data[0]
            self.address_map = data[1]

    def getCoordsFromCode(self, code):
        if self.building_map is None:
            raise Exception("Building map not initialized, something went wrong!")
        if code in self.building_map:
            return self.building_map[code]
