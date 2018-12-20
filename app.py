from flask import Flask, jsonify, request, render_template, send_file, send_from_directory
from cucourses import CourseGrabber

app = Flask(__name__)
app.config['TESTING'] = True
app.config['HTML_FOLDER'] = 'templates/'
app.config['JS_FOLDER'] = 'js/'
app.config['CSS_FOLDER'] = 'css/'


@app.route('/search_classes', methods=['POST'])
def search_classes():
    cg = CourseGrabber()
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
    print(request.form)
    res = default()
    try:
        t = request.form['type']
    except:
        return default()
    if t =='keyword':
        cg = CourseGrabber()
        res = cg.doSearch(request.form, request.form['srcdb'])
    return res

@app.route('/')
def default():
    return send_from_directory(app.config['HTML_FOLDER'], 'index.html')