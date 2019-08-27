import matplotlib
matplotlib.use('Agg')

from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session, Markup, after_this_request
from cucourses import CourseGrabber
from users import FirebaseAuth
from cubuildings import BuildingGrabber
from cufcq import FCQAnalyzer
from io import BytesIO as IO
import gzip
import functools

import os
import threading
import json

app = Flask(__name__)
app.config['TESTING'] = True
app.config['HTML_FOLDER'] = 'templates/'
app.config['JS_FOLDER'] = 'js/'
app.config['CSS_FOLDER'] = 'css/'
app.config['IMAGE_FOLDER'] = 'images/'
app.secret_key = os.environ.get('flask_key')

class HelperHandler:

    def __init__(self):
        self.fa = None
        self.cg = None
        self.bg = None
        self.fcq = None
        t = threading.Thread(target = self.initHelpers)
        t.start()

    def initHelpers(self):
        self.fa = FirebaseAuth()
        self.cg = CourseGrabber()
        self.bg = BuildingGrabber()
        #self.fcq = FCQAnalyzer()

hh = HelperHandler()

def open_template(file):
    try:
        with open(file, 'r') as f:
            return Markup(f.read())
    except:
        return "Error loading template %s" % file

def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func

@app.route('/css/<path:filename>')
@gzipped
def css(filename):
    return send_from_directory(app.config['CSS_FOLDER'], filename)

@app.route('/images/<path:filename>')
@gzipped
def images(filename):
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

@app.route('/js/<path:filename>')
@gzipped
def js(filename):
    return send_from_directory(app.config['JS_FOLDER'], filename)

@app.route('/search', methods=['GET'])
@gzipped
def display_search():
    navbar = ""
    headers = ""
    courses = "{}"
    if 'cal' in request.args:
        cal_classes = hh.fa.getShareFromUrl(request.url)
        courses = json.dumps(cal_classes)
    print(courses)
    with open('templates/navbar.html', 'r') as f:
        navbar = f.read()
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if navbar=="" or headers=="":
        return "Something went wrong"
    return render_template('classsearch.html',
        navbar=Markup(navbar),
        headers=Markup(headers),
        cal_param=courses
    )

@app.route('/search', methods=['POST'])
def search():
    res = default()
    try:
        t = request.form['type']
    except:
        return default()
    if t == 'keyword':
        res = hh.cg.doSearch(request.form, request.form['srcdb'])
    if t == 'view_sections':
        res = hh.cg.getSections(request.form)
    return res

@app.route('/culogin', methods=['POST'])
def culogin():
    if hh.fa.verifyToken(request.form['token'], request.form['uid']):
        print('Checking existing tokens...')
        t = hh.fa.checkCUTokenExpire(request.form['uid'])
        dic = {}
        if t:
            print('Current token still valid.')
            info = hh.cg.getUserId(t)
            if 'error' in info:
                t = hh.cg.getAuthToken(request.form['username'], request.form['password'])
                info = hh.cg.getUserId(t)
                id = info['pers']['id']
                hh.fa.addTokenToDatabase(t, request.form['uid'], id)
            id = info['pers']['id']
            dic = info
        else:
            print('Token expired or doesnt exist, fetching new one...')
            try:
                t = hh.cg.getAuthToken(request.form['username'], request.form['password'])
            except:
                return 'Invalid credentials'
            info = hh.cg.getUserId(t)
            id = info['pers']['id']
            hh.fa.addTokenToDatabase(t, request.form['uid'], id)
            dic = info
        return str([t, dic])
    else:
        return 'Auth Fail'

@app.route('/getcrns', methods=['POST'])
def getcrns():
    return hh.cg.doSearch({'crn':request.form['crns']}, request.form['srcdb'])

@app.route('/getcart', methods=['POST'])
def getcart():
    if hh.fa.checkToken(request.form['cutoken'], request.form['uid']) and hh.fa.verifyToken(request.form['token'], request.form['uid']):
        cartinfo = hh.cg.getCart(request.form['cutoken'], hh.fa.getCIDToken(request.form['cutoken']))
        cart = cartinfo['cart']
        return str(cart)
    return 'Unauthorized'

@app.route('/addcart', methods=['POST'])
def addcart():
    if hh.fa.checkToken(request.form['cutoken'], request.form['uid']) and hh.fa.verifyToken(request.form['token'], request.form['uid']):
        cu = hh.fa.getCUInfo(request.form['uid'])
        return hh.cg.addToCart(request.form, cu[3])
    return "Unauthorized"

@app.route('/removecart', methods=['POST'])
def removecart():
    if hh.fa.checkToken(request.form['cutoken'], request.form['uid']) and hh.fa.verifyToken(request.form['token'], request.form['uid']):
        cu = hh.fa.getCUInfo(request.form['uid'])
        return hh.cg.removeFromCart(request.form, cu[3])
    return "Unauthorized"

@app.route('/savesect', methods=['POST'])
def savesect():
    if hh.fa.verifyToken(request.form['token'], request.form['uid']):
        try:
            hh.fa.saveSectList(request.form['uid'], request.form['saved'])
            return "Success"
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/loadsect', methods=['POST'])
def loadsect():
    if hh.fa.verifyToken(request.form['token'], request.form['uid']):
        try:
            return jsonify(hh.fa.loadSectList(request.form['uid']))
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/building', methods=['POST'])
def building():
    coords = hh.bg.getCoordsFromCode(request.form['name'])
    return jsonify(coords)

@app.route('/favicon.ico')
@gzipped
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/help')
@gzipped
def contact():
    navbar = ""
    headers = ""
    with open('templates/navbar.html', 'r') as f:
        navbar = f.read()
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if navbar=="" or headers=="":
        return "Something went wrong"
    return render_template('contact.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

@app.route('/grades', methods=['GET'])
@gzipped
def display_grades():
    navbar = ""
    headers = ""
    with open('templates/navbar.html', 'r') as f:
        navbar = f.read()
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if navbar=="" or headers=="":
        return "Something went wrong"
    return render_template('grades.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

@app.route('/grades', methods=['POST'])
@gzipped
def activate_grades():
    return "Coming soon"

@app.route('/predict', methods=['GET'])
@gzipped
def display_predict():
    return "Temporarily Unavailable"
    headers = open_template('templates/headers.html')
    navbar = open_template('templates/navbar.html')
    return render_template('predict.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

@app.route('/predict', methods=['POST'])
def analyze_predict():
    return "Temporarily Unavailable"
    if hh.fcq:
        if hh.fa.verifyToken(request.form['token'], request.form['uid']):
            oldList = hh.fa.loadOldList(request.form['uid'])
            newList = hh.fa.loadSectList(request.form['uid'])
            return hh.fcq.predictMultipleGrades(oldList, newList)
        return "Unauthorized"
    else:
        return json.dumps({'failure': 'Server is still initializing FCQs, please try again in a minute.'})

@app.route('/predictsearch', methods=['POST'])
@gzipped
def search_predict():
    return "Temporarily Unavailable"
    if hh.fcq:
        return hh.fcq.getRows(request.form['subject'], request.form['course'], request.form['term'], request.form['year'])
    else:
        return json.dumps({'failure': 'Server is still initializing FCQs, please try again in a minute.'})

@app.route('/predictsave', methods=['POST'])
@gzipped
def save_predict():
    return "Temporarily Unavailable"
    if hh.fa.verifyToken(request.form['token'], request.form['uid']):
        try:
            hh.fa.saveOldList(request.form['uid'], request.form['saved'])
            return "Success"
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/predictload', methods=['POST'])
@gzipped
def load_predict():
    return "Temporarily Unavailable"
    if (hh.fa.verifyToken(request.form['token'], request.form['uid'])):
        try:
            return jsonify(hh.fa.loadOldList(request.form['uid']))
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/generatelink', methods=['POST'])
@gzipped
def generate_link():
    try:
        calendar_classes = json.loads(request.form['calendar_classes'])
        print(calendar_classes)
        url = hh.fa.makeShareUrl(calendar_classes)
        print(url)
        return json.dumps({'success': request.url_root + "search?cal=" + url})
    except Exception as e:
        print(e)
        return json.dumps({'failure': 'Something went wrong.'})

@app.route('/')
@gzipped
def default():
    headers = open_template('templates/headers.html')
    navbar = open_template('templates/navbar.html')
    return render_template('index.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
