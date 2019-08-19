import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import re
import time

def main():
    print('Loading building list...')
    df = pd.read_excel("https://www.colorado.edu/fm/content/master-building-list-xls-version")
    coords = {}
    addrs = {}
    with open('BuildingMap.json', 'r') as f:
        try:
            data = json.loads(f.read())
            coords = data[0]
            addrs = data[1]
        except:
            pass
    for index, row in df.iterrows():
        try:
            addr = row["Address"] + " " + row["City"] + " " + row["State"] + " " + str(row["Zip"])
        except Exception as e:
            print("Error for " + row['Bldg \nCode'] + ". Skipping...")
            print(e)
        if row['Bldg \nCode'] in coords:
            print('Already have coordinates for ' + row['Bldg \nCode'])
            continue
        if addr in addrs:
            print('Already have coordinates for ' + addr)
            coords[row['Bldg \nCode']] = addrs[addr]
        else :
            error = True
            while error:
                try:
                    print('Fetching coordinates for ' + row['Bldg \nCode'] + ' - ' + addr)
                    driver = webdriver.Chrome('ignore/chromedriver')
                    driver.get("http://maps.google.com")
                    searchbar = driver.find_element_by_xpath("//input[@name='q']")
                    searchbar.send_keys(addr, Keys.ENTER)
                    time.sleep(4)
                    url = driver.current_url
                    ind = url.find('@')
                    first = url[ind+1:]
                    end = first.find("/")
                    second = first[:end]
                    latlon = second.split(',')
                    latitude = latlon[0]
                    longitude = latlon[1]
                    coords[row['Bldg \nCode']] = [latitude, longitude]
                    addrs[addr] = [latitude, longitude]
                    print(latitude, ',', longitude)
                    error = False
                    driver.close()
                except:
                    driver.close()
                    error = True
            time.sleep(10)
        with open('BuildingMap.json', 'w') as f:
            data = json.dumps([coords, addrs])
            f.write(data)

if __name__ == '__main__':
    main()
