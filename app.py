from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session, Markup, after_this_request
from cucourses import CourseGrabber
from users import FirebaseAuth
from io import BytesIO as IO
import gzip
import functools

import os

app = Flask(__name__)
app.config['TESTING'] = True
app.config['HTML_FOLDER'] = 'templates/'
app.config['JS_FOLDER'] = 'js/'
app.config['CSS_FOLDER'] = 'css/'
app.config['IMAGE_FOLDER'] = 'images/'
app.secret_key = os.environ.get('flask_key')

fa = FirebaseAuth()
cg = CourseGrabber()

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
    with open('templates/navbar.html', 'r') as f:
        navbar = f.read()
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if navbar=="" or headers=="":
        return "Something went wrong"
    return render_template('classsearch.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

@app.route('/search', methods=['POST'])
def search():
    res = default()
    try:
        t = request.form['type']
    except:
        return default()
    if t == 'keyword':
        res = cg.doSearch(request.form, request.form['srcdb'])
    if t == 'view_sections':
        res = cg.getSections(request.form)
    return res

@app.route('/culogin', methods=['POST'])
def culogin():
    if fa.verifyToken(request.form['token'], request.form['uid']):
        print('Checking existing tokens...')
        t = fa.checkCUTokenExpire(request.form['uid'])
        dic = {}
        if t:
            print('Current token still valid.')
            info = cg.getUserId(t)
            if 'error' in info:
                t = cg.getAuthToken(request.form['username'], request.form['password'])
                info = cg.getUserId(t)
                id = info['pers']['id']
                fa.addTokenToDatabase(t, request.form['uid'], id)
            id = info['pers']['id']
            dic = info
        else:
            print('Token expired or doesnt exist, fetching new one...')
            try:
                t = cg.getAuthToken(request.form['username'], request.form['password'])
            except:
                return 'Invalid credentials'
            info = cg.getUserId(t)
            id = info['pers']['id']
            fa.addTokenToDatabase(t, request.form['uid'], id)
            dic = info
        return str([t, dic])
    else:
        return 'Auth Fail'

@app.route('/getcrns', methods=['POST'])
def getcrns():
    return cg.doSearch({'crn':request.form['crns']}, request.form['srcdb'])

@app.route('/getcart', methods=['POST'])
def getcart():
    if fa.checkToken(request.form['cutoken'], request.form['uid']) and fa.verifyToken(request.form['token'], request.form['uid']):
        cartinfo = cg.getCart(request.form['cutoken'], fa.getCIDToken(request.form['cutoken']))
        cart = cartinfo['cart']
        return str(cart)
    return 'Unauthorized'

@app.route('/addcart', methods=['POST'])
def addcart():
    if fa.checkToken(request.form['cutoken'], request.form['uid']) and fa.verifyToken(request.form['token'], request.form['uid']):
        cu = fa.getCUInfo(request.form['uid'])
        return cg.addToCart(request.form, cu[3])
    return "Unauthorized"

@app.route('/removecart', methods=['POST'])
def removecart():
    if fa.checkToken(request.form['cutoken'], request.form['uid']) and fa.verifyToken(request.form['token'], request.form['uid']):
        cu = fa.getCUInfo(request.form['uid'])
        return cg.removeFromCart(request.form, cu[3])
    return "Unauthorized"

@app.route('/savesect', methods=['POST'])
def savesect():
    if fa.verifyToken(request.form['token'], request.form['uid']):
        try:
            fa.saveSectList(request.form['uid'], request.form['saved'])
            return "Success"
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/loadsect', methods=['POST'])
def loadsect():
    if fa.verifyToken(request.form['token'], request.form['uid']):
        try:
            return jsonify(fa.loadSectList(request.form['uid']))
        except Exception as e:
            print(e)
            return "Something went wrong"
    return "Unauthorized"

@app.route('/favicon.ico')
@gzipped
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/contact')
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

@app.route('/')
@gzipped
def default():
    navbar = ""
    headers = ""
    with open('templates/navbar.html', 'r') as f:
        navbar = f.read()
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if navbar=="" or headers=="":
        return "Something went wrong"
    return render_template('index.html',
        navbar=Markup(navbar),
        headers=Markup(headers)
    )

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
