from flask import Flask, request, jsonify, render_template, redirect, url_for
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import os
import stone
import threading
import subprocess
app = Flask(__name__, static_folder='public')

@app.route('/')
def first_page():
    return render_template('index.html')

@app.route('/save',methods=['POST','GET'])
def save_page():
    return render_template('save.html')

@app.route('/takeapic',methods=['POST','GET'])
def takeapic_page():
    return render_template('takeapic.html')

@app.route('/forgot',methods=['POST','GET'])
def forgot_page():
    return render_template('forgotPassword.html')

@app.route('/register',methods=['POST','GET'])
def register_page():
    return render_template('Register.html')

@app.route('/landingpage',methods=['POST','GET'])
def landing_page():
    return render_template('landingpage.html')

@app.route('/homepage',methods=['POST','GET'])
def home_page():
    return render_template('homepage.html')

@app.route('/uploadapic', methods=['POST', 'GET'])
def upload_pic():
    return render_template('uploadapic.html')

@app.route('/listalldat', methods=['POST'])
def list_all():
    # Get the classification result from the request
    classification_result = request.json
    return render_template('listalldat.html', result=classification_result)

# @app.route('/takeapic/start', methods=['POST'])
# def start_flask_server():
#     if 'WERKZEUG_RUN_MAIN' not in os.environ:
#         threading.Thread(target=start_flask).start()
#     return jsonify({'message': 'Flask server started successfully'})

def start_flask():
    subprocess.Popen(["python", "app.py"])

result = None

def process(temp_image_path):
    global result
    result = stone.process(temp_image_path, image_type="color", return_report_image=True)
    try:
        report_images = result.pop("report_images")
        face_id = 1
        # Uncomment the next line if you want to display the image locally
        # cv2.imshow("Report Image", report_images[face_id])
    except KeyError:
        print("Key 'report_images' not found in the result dictionary.")

def saving(uploaded):
    file_name = next(iter(uploaded))
    image = Image.open(BytesIO(uploaded[file_name]))
    temp_image_path = "/tmp/uploaded_image.jpg"
    image.save(temp_image_path)
    return temp_image_path

def extract_skin_tone(result):
    if "faces" in result and result["faces"]:
        return result["faces"][0].get("skin_tone", "Skin tone not found")
    else:
        return "No faces found in the result"

def determine_undertone(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    cool_boundary = ([0, 0, 100], [100, 100, 255])
    warm_boundary = ([100, 100, 0], [255, 255, 100])
    neutral_boundary = ([100, 100, 100], [200, 200, 200])

    cool_mask = cv2.inRange(image, np.array(cool_boundary[0]), np.array(cool_boundary[1]))
    warm_mask = cv2.inRange(image, np.array(warm_boundary[0]), np.array(warm_boundary[1]))
    neutral_mask = cv2.inRange(image, np.array(neutral_boundary[0]), np.array(neutral_boundary[1]))

    cool_count = cv2.countNonZero(cool_mask)
    warm_count = cv2.countNonZero(warm_mask)
    neutral_count = cv2.countNonZero(neutral_mask)

    if cool_count > warm_count and cool_count > neutral_count:
        return "Cool Undertone"
    elif warm_count > cool_count and warm_count > neutral_count:
        return "Warm Undertone"
    else:
        return "Neutral Undertone"

@app.route('/classify', methods=['POST', 'GET'])
def classify():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if file:
        file.save('/tmp/uploaded_image.jpg')
        temp_image_path = '/tmp/uploaded_image.jpg'
        
        process(temp_image_path)
        skin_tone = extract_skin_tone(result)
        tones = None
        if skin_tone in ['#373028', '#422811']:
            tones = 'Dark'
        elif skin_tone.lower() in ['#513b2e', '#6f503c', '#81654f']:
            tones = 'Mid-Dark'
        elif skin_tone.lower() in ['#9d7a54', '#bea07e', '#e5c8a6', '#e7c1b8']:
            tones = 'Mid-Light'
        else:
            tones = 'Light'

        if tones == 'Dark':
        # dark
            target_folder = "Mustard"
        elif tones == 'Mid-Dark':
        # olive
            target_folder = "Camel"
        elif tones == 'Mid-Light':
        # medium
            target_folder = "Olive"
        else:
        # fair
            target_folder = "Lavender"

        undertone = determine_undertone(temp_image_path)
        
        return jsonify({"skin_tone": tones, "undertone": undertone, "color": target_folder})

if __name__ == '__main__':
    app.run(debug=True)
