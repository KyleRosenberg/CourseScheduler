from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session
from cucourses import CourseGrabber
from users import FirebaseAuth

import os

app = Flask(__name__)
app.config['TESTING'] = True
app.config['HTML_FOLDER'] = 'templates/'
app.config['JS_FOLDER'] = 'js/'
app.config['CSS_FOLDER'] = 'css/'
app.secret_key = os.environ.get('flask_key')

fa = FirebaseAuth()
cg = CourseGrabber()

@app.route('/search_classes', methods=['POST'])
def search_classes():
    res = cg.doSearch(request.form)
    return res

@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory(app.config['CSS_FOLDER'], filename)

@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory(app.config['JS_FOLDER'], filename)

@app.route('/search', methods=['GET'])
def display_search():
    return send_from_directory(app.config['HTML_FOLDER'], 'classsearch.html')

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
            t = cg.getAuthToken(request.form['username'], request.form['password'])
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
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/contact')
def contact():
    return send_from_directory(app.config['HTML_FOLDER'], 'contact.html')

@app.route('/')
def default():
    return send_from_directory(app.config['HTML_FOLDER'], 'index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
