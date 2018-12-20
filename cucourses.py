import requests
import json


class CourseGrabber:

    def __init__(self):
        pass

    def doSearch(self, fields, semester="2191"):
        url = "https://classes.colorado.edu/api/"
        querystring = {"page":"fose","route":"search"}
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "44ff740c-90b5-4cb0-ae59-c0a53a2bd4b3"
        }
        c = []
        ignore = ['srcdb', 'type']
        for f in fields:
            if f in ignore:
                continue
            c.append({"field":f, "value":fields[f]})
        payload = {
            "other": {"srcdb":str(semester)},
            "criteria": c
        }
        r = requests.post(url, headers=headers, params = querystring, data=json.dumps(payload))
        return r.text
