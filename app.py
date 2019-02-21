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
        if t:
            return t
        else:
            print('Token expired or doesnt exist, fetching new one...')
            t = cg.getAuthToken(request.form['username'], request.form['password'])
            info = cg.getUserId(t)
            session['info'] = info
            id = info['pers']['id']
            fa.addTokenToDatabase(t, request.form['uid'], id)
        return t
    else:
        return 'Auth Fail'

@app.route('/getcart', methods=['POST'])
def getcart():
    if fa.checkToken(request.form['cutoken'], request.form['uid']) and fa.verifyToken(request.form['token'], request.form['uid']):
        cartinfo = cg.getCart(request.form['cutoken'], fa.getCIDToken(request.form['cutoken']))
        reginfo = cg.getUserId(request.form['cutoken'])
        cart = cartinfo['cart']
        reg = reginfo['reg'][request.form['srcdb']]
        cacrns = [c.split('|')[2] if c[:4]==request.form['srcdb'] else '' for c in cart]
        recrns = [c.split('|')[1] for c in reg]
        crns = cacrns + recrns
        for c in crns:
            if c=='':
                crns.remove(c)
        param = {
            'crn':','.join(crns)
        }
        return cg.doSearch(param, request.form['srcdb'])
    return 'Unauthorized'

@app.route('/addcart', methods=['POST'])
def addcart():
    if fa.checkToken(request.form['cutoken'], request.form['uid']) and fa.verifyToken(request.form['token'], request.form['uid']):
        cu = fa.getCUInfo(request.form['uid'])
        return cg.addToCart(request.form, cu[3])
    return ""

@app.route('/')
def default():
    return send_from_directory(app.config['HTML_FOLDER'], 'index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
