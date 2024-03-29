from flask import Flask, request, redirect, url_for, render_template, flash, Response
from markupsafe import escape
import os, glob
from werkzeug.utils import secure_filename
import cv2 as cv
import utlis
from pyzbar.pyzbar import decode
import numpy as np
import json
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
import base64
import requests
import base64

#################### Housekeeping ####################
files = glob.glob('static/output/*')
for f in files:
    os.remove(f)

# Create a new Flask instance
app = Flask(__name__)
app.secret_key = os.urandom(24)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'


# Configure upload folder and allowed file extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load existing data
data = {}
# Check if file exists and is not empty
if os.path.isfile('data.json') and os.stat('data.json').st_size != 0:
    with open('data.json', 'r') as file:
        # If file exists and is not empty, load its contents into 'data'
        data = json.load(file)

#################### Set up OpenAI ####################
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def get_img_info(image_path):

    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": '''
                    Please read the text in this image and return the information in the following JSON format(note xxx is placeholder, if the information is not available in the image,put"N/A" instead). 
                    {"eventName":xxx,"Date":dd/mm/yyyy(if the year is not specific, put "2024" as defalut),"Time":xxx(hh:mm PM/AM timezone),
                    "Location":xxx,"Hosts":list all hosts,"Type":in person or virtual(if both, then put "virtual and in-person"),
                    "Website":xxx,"SignUpLink":if there is a QRcode, put "Yes"}
                    ''',
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            },
        ]
        }
    ],
    "max_tokens": 300
    }
    api_url = "https://api.openai.com/v1/chat/completions"
    print("API Endpoint URL:", api_url)

    response = requests.post(api_url, headers=headers, json=payload)
    response_json = response.json()

    # print(json.dumps(response_json, indent=2)) 

    content_value = response_json['choices'][0]['message']['content'] 
    # print({content_value})
    cleaned_content = content_value.replace("json", "").replace("```", "").replace("\n", "").strip()
    print("-----> gpt retrieve info: " + cleaned_content)
    return cleaned_content



#################### Extract Text ####################
        
# detecting characters and disply the result
# hImg, wImg, _ = img.shape
# boxes = pytesseract.image_to_boxes(img)
# for b in boxes.splitlines():
#     # convert b to a list
#     b = b.split(' ')
#     # print(b)
#     # identity the position of the characters
#     x, y, w, h = int(b[1]), int(b[2]), int(b[3]), int(b[4])
#     # draw a rectangle around the characters
#     cv.rectangle(img, (x, hImg - y), (w, hImg - h), (0, 0, 255), 2)
#     cv.putText(img, b[0], (x, hImg - y + 25), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

# cv.imshow('result', img)


# Take a photo from webcam
def take_photo():
    data = request.values['imageBase64']
    encoded_data = data.split(',')[1]
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)

    global num
    save_path = 'static/uploads/webcam_' + str(num) + '.jpg'
    cv.imwrite(save_path, img)
    num += 1
    print(f'----> Photo saved as {save_path} <----')
    return "Image saved!"


# read the img file
def read_img(image_path):
    if not os.path.isfile(image_path):
        print(f"File '{image_path}' does not exist")
        exit(1)
    img = cv.imread(image_path)
    if img is None:
        print(f"Failed to load image '{image_path}]")
        exit(1)
    print("-----> invoking read image ")

    return img

def extract_qr_code(image_path):
    
    print("-----> invoking extract qr code ")

    img = read_img(image_path)
    myData = None
    # decode the QR code
    for qrcode in decode(img):
        # read the data
        myData = qrcode.data.decode('utf-8')
        if myData:
            print(f'----> QR code data: {myData} <----')
        else:
            print(f'----> Cannot extract QR code / No QR code <----')

        # draw a bounding box around the QR code
        pts = np.array([qrcode.polygon], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv.polylines(img, [pts], True, (255, 0, 255), 3)

        # print out the message in the QR code
        pts2 = qrcode.rect
        cv.putText(img, myData, (pts2[0], pts2[1]), cv.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

    return myData

    
def save_data_to_json(image_path):

    print("-----> invoking save data to json")

    # write the event data to the json file
    data_dict = json.loads(get_img_info(image_path))
    qr_code_data = extract_qr_code(image_path)

    # Determine the next event key
    event_keys = [key for key in data.keys() if key.startswith('event_')]
    next_event_number = 1 if not event_keys else max([int(key.split('_')[1]) for key in event_keys]) + 1
    next_event_key = f'event_{next_event_number}'

    data[next_event_key] = {
            "name": data_dict["eventName"],
            "date": data_dict["Date"],
            "time": data_dict["Time"],
            "location": data_dict["Location"],
            "hosts": data_dict["Hosts"],
            "type": data_dict["Type"],
            "website": data_dict["Website"],
            "signUpLink": qr_code_data
    }

    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)  

################## Image Segmentation ####################
# convert img to grayscale
# gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
# gray = cv.bilateralFilter(gray, 11, 17, 17)
# # detect edges in the image
# edges = cv.Canny(gray, 100, 200)

# # apply a closing operation to close gaps in between object edges
# kernel = cv.getStructuringElement(cv.MORPH_RECT, (7, 7))
# closed = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)

# print(f'---- Start extracting text from gray img ---- \n' + pytesseract.image_to_string(gray) + f'\n---- End extracting text ----')
# print(f'---- Start extracting text from edges img ---- \n' + pytesseract.image_to_string(edges) + f'\n---- End extracting text ----')


# i = 0
# # find all contours
# imgOrigin = img.copy() # copy of the original image for display purposes
# cnts, heir = cv.findContours(closed.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)[-2:]
# for c in cnts:
#     peri = cv.arcLength(c, True)
#     approx = cv.approxPolyDP(c, 0.02 * peri, True)
#     # draw the contours
#     cv.drawContours(img, [approx], -1, (0, 255, 0), 2)

#     x, y, w, h = cv.boundingRect(c)
#     if h > 0 and w > 0:
#         # check if height and width are greater than 0
#         newImage = img[max(0, y): min(img.shape[0], y + h), max(0, x): min(img.shape[1], x + w)].copy()
#         cv.imwrite('static/output/segment_' + str(i) + '.jpg', newImage)
#         i += 1
# print(f'Completed image segmentation and saved in /static/')

################## Display the results ####################
# img array for display
# imgArray = ([imgOrigin, gray], [edges, img])
# # img labels for display
# labels = [["Original", "Gray"], ["Edges", "Contours"]]

# stackedImages = utlis.stackImages(imgArray,0.6,labels)
# cv.imshow('result', stackedImages)
# cv.waitKey(0)
# cv.destroyAllWindows()


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

def load_events():
    with open('data.json', 'r') as file:
        return json.load(file)


################## Create Routes ####################
@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        if 'take_photo' in request.form:
            take_photo()
            flash('Photo taken and saved successfully')
        else:
            # check if the post request has the file part
            if 'photo' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            # get the uploaded file
            file = request.files['photo']

            # check if a file was selected
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            # check file extensions
            if file and allowed_file(file.filename): 
                # make the filename safe, remove unsupported characters   
                filename = secure_filename(file.filename)
                # save the file to the uploads folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                flash('Image upload successfully')

                save_data_to_json(file_path)

                # redirect back to index after upload
                return redirect(url_for('index'))
    
    # pass the events to the template
    events = load_events()
    return render_template('index.html', events=events)


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

