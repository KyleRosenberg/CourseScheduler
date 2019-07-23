import pandas as pd


class BuildingGrabber:

    def __init__(self):
        self.reloadDataframe()

    def reloadDataframe(self):
        self.building_map = pd.read_excel("https://www.colorado.edu/fm/content/master-building-list-xls-version")

    def getAddressFromCode(self, code):
        if self.building_map is None:
            raise Exception("Building map not initialized, something went wrong!")
        dfBuilding = self.building_map.loc[self.building_map['Bldg \nCode'] == code]
        if len(dfBuilding) != 1:
            raise Exception("Building code returned multiple results, something went wrong!")
        dfB = dfBuilding.iloc[0]
        return dfB["Address"] + " " + dfB["City"] + " " + dfB["State"] + " " + str(dfB["Zip"])
