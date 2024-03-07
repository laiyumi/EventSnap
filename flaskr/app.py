from flask import Flask, request, redirect, url_for, render_template, flash
from markupsafe import escape
import os, glob
from werkzeug.utils import secure_filename
import cv2 as cv
import utlis

# remove all files in the output folder before starting the app
files = glob.glob('static/output/*')
for f in files:
    os.remove(f)

UPLOAD_FOLDER = '/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create a new Flask instance
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# read the img file
filename = 'static/test.001.jpeg'
if not os.path.isfile(filename):
    print(f"File '{filename}' does not exist")
    exit(1)
img = cv.imread(filename)
if img is None:
    print(f"Failed to load image '{filename}]")
    exit(1)


# convert img to grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
gray = cv.bilateralFilter(gray, 11, 17, 17)
# detect edges in the image
edges = cv.Canny(gray, 100, 200)

# apply a closing operation to close gaps in between object edges
kernel = cv.getStructuringElement(cv.MORPH_RECT, (7, 7))
closed = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)

i = 0
# find all contours
imgOrigin = img.copy() # copy of the original image for display purposes
cnts, heir = cv.findContours(closed.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)[-2:]
for c in cnts:
    peri = cv.arcLength(c, True)
    approx = cv.approxPolyDP(c, 0.02 * peri, True)
    # draw the contours
    cv.drawContours(img, [approx], -1, (0, 255, 0), 2)
    x, y, w, h = cv.boundingRect(c)
    if h > 0 and w > 0:
        # check if height and width are greater than 0
        newImage = img[max(0, y): min(img.shape[0], y + h), max(0, x): min(img.shape[1], x + w)].copy()
        cv.imwrite('static/output/segment_' + str(i) + '.jpg', newImage)
        print(f'Image saved as /static/segment_{i}.jpg')
        i += 1

# img array for display
imgArray = ([imgOrigin, gray], [edges, img])
# img labels for display
labels = [["Original", "Gray"], ["Edges", "Contours"]]

stackedImages = utlis.stackImages(imgArray,0.6,labels)
cv.imshow('result', stackedImages)
cv.waitKey(0)
cv.destroyAllWindows()




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

