import requests
import json


class CourseGrabber:

    def __init__(self):
        self.MEETING_TYPES = {
            'LEC': ['lecture', 'lectures'],
            'REC': ['recitation', 'recitations'],
            'LAB': ['labratory', 'labratories'],
            'SEM': ['seminar', 'seminars'],
            'PRA': ['practicum', 'practicums'],
            'STU': ['studio', 'studios'],
            'WKS': ['workshop', 'workshops']
        }
        self.recs = {}
        with open('rec_final.json', 'r') as f:
            self.recs = json.loads(f.read())

    def doSearch(self, fields, semester="2201"):
        url = "https://classes.colorado.edu/api/"
        querystring = {"page":"fose","route":"search"}
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        sc = "asgened"
        c = []
        ignore = ['srcdb', 'type']
        for f in fields:
            if f in ignore:
                continue
            if f=="hours":
                c.append({"field":f, "value":">="+str(fields[f])})
                c.append({"field":"hours_min", "value":"<="+str(fields[f])})
            elif f[:len(sc)]==sc:
                c.append({"field":str(fields[f]), "value":"Y"})
            else:
                c.append({"field":f, "value":fields[f]})
        payload = {
            "other": {"srcdb":str(semester)},
            "criteria": c
        }
        r = requests.post(url, headers=headers, params = querystring, data=json.dumps(payload))
        return self.cleanSearch(r.text)

    def cleanSearch(self, results):
        big_dict = json.loads(results)
        small_ret = []
        if (big_dict['count']==0):
            return results
        i = 0
        while i < len(big_dict['results']):
            c = big_dict['results'][i]
            curr_code = c['code']
            newC = {
                'code': curr_code, #CSCI 1300
                'title': c['title'], #Computer Science 1: Intro to Computing
            }
            counts = {}
            j = i
            crns = ''
            while j<len(big_dict['results']) and big_dict['results'][j]['code']==curr_code:
                nc = big_dict['results'][j]
                crns += nc['crn'] + ','
                if nc['schd'] in counts:
                    counts[nc['schd']] += 1
                else:
                    counts[nc['schd']] = 1
                j+=1
            meeting_types_display = ''
            for k in self.MEETING_TYPES: #1 lecture, 2 recitations
                if k in counts:
                    poss = self.MEETING_TYPES[k]
                    if counts[k]==1:
                        meeting_types_display += '1 ' + poss[0]
                    else:
                        meeting_types_display += str(counts[k]) + ' ' + poss[1]
                    meeting_types_display += ', '
            meeting_types_display = meeting_types_display[0:-2]
            newC['meeting_types'] = meeting_types_display
            newC['crns'] = crns #12345, 12346, 12347,
            small_ret.append(newC)
            i = j
        return json.dumps(small_ret)

    def getSections(self, fields):
        url = "https://classes.colorado.edu/api/"
        querystring = {"page":"fose","route":"details"}
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }
        c = {}
        ignore = ['type']
        for f in fields:
            if f in ignore:
                continue
            c[f] = fields[f]
        payload = c
        r = requests.post(url, headers=headers, params = querystring, data=json.dumps(payload))
        d = json.loads(r.text)
        code = d['code']
        if code in self.recs and len(self.recs[code])>0:
            d['matches'] = self.recs[code]
        return json.dumps(d)

    def handleLoginPage(self, session, post_page_text, username, password, count=0):
        postURL = post_page_text.split('fm-login" name="login" action="')[1].split('"')[0]
        login_data = {
            "timezoneOffset": "0",
            "_eventId_proceed": "Log In",
            "j_username": username,
            "j_password": password,
            "MIME Type": "application/x-www-form-urlencoded"
        }

        # user login page
        login_request = session.post("https://fedauth.colorado.edu" + postURL, data=login_data)

        login_text = login_request.text
        if login_text.find('<form id="fm-login" name="login"')>-1:
            if count==3:
                print('FAILED')
                return 'BROKEN'
            return self.handleLoginPage(session, login_text, username, password, count+1)
        else:
            return login_text

    def getAuthToken(self, username, password, count=0):
        session = requests.Session()

        # get the inital page, found url by disecting js code from
        # mycuinfo.colorado.edu
        init_page = session.get("https://ping.prod.cu.edu/as/authorization.oauth2?client_id=CUBoulderClassSearch&response_type=token&IdpSelectorId=BoulderIDP&scope=AcademicRecords&redirect_uri=https://classes.colorado.edu/sam/oauth.html")
        init_text = init_page.text

        # set the post data for the next request
        samlValue = init_text.split('name="SAMLRequest" value="')[1].split('"')[0]
        relay = init_text.split('name="RelayState" value="')[1].split('"')[0]
        action = init_text.split('method="post" action="')[1].split('"')[0]
        ver1_data = {
            "SAMLRequest" : samlValue,
            "RelayState" : relay
        }

        # human verification page num. 1
        post_page = session.post(action, data=ver1_data)
        post_page_text = post_page.text

        login_text = self.handleLoginPage(session, post_page_text, username, password)

        RelayState = login_text.split('name="RelayState" value="')[1].split('"')[0]
        SAMLResponse = login_text.split(
            'name="SAMLResponse" value="')[1].split('"')[0]

        ver3_data = {
            "RelayState": RelayState,
            "SAMLResponse": SAMLResponse
        }

        # human verification page num. 3
        third_post_page = session.post(
            "https://ping.prod.cu.edu/sp/ACS.saml2",
            data=ver3_data)

        ind = third_post_page.url.find('access_token=')
        end = third_post_page.url.find('&', ind+1)
        return third_post_page.url[ind+13:end]

    def getUserId(self, token):
        r = requests.get('https://classes.colorado.edu/api/?page=sisproxy&oauth_token='+token)
        text = r.text
        text = text[text.find('(')+1: text.find(')')]
        return json.loads(text)

    def getCart(self, token, id):
        params = {
            'page': 'sisproxy',
            'p_action': 'cart_read',
            'oauth_token': token,
            'user_id': id
        }
        r = requests.get('https://classes.colorado.edu/api/', params=params)
        j = r.text[8:-3]
        return json.loads(j)

    def addToCart(self, form, id):
        params = {}
        for k in form:
            if k[0]=='p':
                params[k] = form[k]
        params['oauth_token'] = form['cutoken']
        params['p_action'] = 'cart_add'
        params['p_cart_name'] = 'default-UGRD'
        params['p_institution'] = 'CUBLD'
        params['user_id'] = id
        params['page'] = 'sisproxy';
        r = requests.get('https://classes.colorado.edu/api/', params=params)
        return r.text

    def removeFromCart(self, form, id):
        params = {}
        for k in form:
            if k[0]=='p':
                params[k] = form[k]
        params['oauth_token'] = form['cutoken']
        params['p_action'] = 'cart_remove'
        params['p_cart_name'] = 'default-UGRD'
        params['p_institution'] = 'CUBLD'
        params['user_id'] = id
        params['page'] = 'sisproxy';
        r = requests.get('https://classes.colorado.edu/api/', params=params)
        return r.text
