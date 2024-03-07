from flask import Flask, request, redirect, url_for, render_template, flash
from markupsafe import escape
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create a new Flask instance
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000


# build a URL for the static file
# url_for('static', filename='style.css')

def valid_login(username, password):
    if username == 'admin' and password == '8888':
        return True
    else:
        return False
    
def log_the_user_in(username):
    return f'Logged in as: {username}'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Define a route(indicates what URL will trigger the function below)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select a file, the browser submits an empty part without a filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        # if the file is one of the allowed types and it has a filename
        if file and allowed_file(file.filename): 
            # make the filename safe, remove unsupported characters   
            filename = secure_filename(file.filename)
            # save the file to the uploads folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error)


@app.route('/user/')
@app.route('/user/<username>')
# show the user profile
def show_user_profile(username=None):
    return render_template('profile.html', username=username)

# show the event with the given id
@app.route('/event/<int:event_id>')
def show_event(event_id=None):
    return render_template('event.html', event_id=event_id)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

