from __future__ import division, print_function
import sys
import os
import csv
import numpy as np
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
from flask import Flask, redirect, url_for, request, render_template, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'naeem123'
MODEL_PATH = 'models/model.h5'

# Load your trained model
model = load_model(MODEL_PATH)

print('Model loaded. Start serving...')

def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(64, 64))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    preds = model.predict(img)
    return preds

# Load patient data from CSV
def load_patient_data():
    data = []
    with open("static/patient_data.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

# Predict status based on symptoms entered by user
def predict_status(symptoms):
    # Load patient data
    patient_data = load_patient_data()

    # Compare user-entered symptoms with patient data
    for patient in patient_data:
        if all(symptoms[symptom] == int(patient[symptom]) for symptom in symptoms):
            return patient['Status']

    return "Uncertain"

@app.route('/')
def symptoms():
    return render_template('symptoms.html')

@app.route('/index')
def index():
    # Main page
    return render_template('index.html')

@app.route('/symptoms', methods=['POST'])
def symptoms_form():
    message = None
    if request.method == 'POST':
        # Get symptoms from form submission
        symptoms = {
            'Cough': request.form.get('Cough', ''),
            'Fever': request.form.get('Fever', ''),
            'Shortness of breath': request.form.get('Shortness of breath', ''),
            'Chest pain': request.form.get('Chest pain', '')
        }

        # Convert symptoms to integers if they are not empty strings
        symptoms = {key: int(value) if value.strip() else 0 for key, value in symptoms.items()}

        # Store symptoms data in session
        session['symptoms'] = symptoms

        # Predict status based on symptoms
        status = predict_status(symptoms)
        print("Status after form submission:", status)

        # Store symptoms status in session
        session['symptoms_status'] = status  # Update session with symptoms status

        # Set message for successful form submission
        message = "Status:  " + status

    return render_template('symptoms.html', message=message)

@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'static/uploads', secure_filename(f.filename))
        f.save(file_path)

        # Make prediction
        preds = model_predict(file_path, model)

        # Retrieve status from session
        status = session.get('symptoms_status')

        # Define result strings based on status and prediction
        str1 = 'Person has Pneumonia'
        str2 = 'Person is Normal'
        str3 = 'Uncertainty found, Please Upload another Image'
        print(preds)
        # Apply conditions
        if status == "Pneumonia" and preds == 1:
            return str1
        elif status in "Mostly Pneumonia" and preds == 0:
            return str3
        elif status in "Mostly Pneumonia" and preds == 1:
            return str1
        elif status in "Normal" and preds == 0:
            return str2
        elif status in "Normal" and preds == 1:
            return str3
        elif status == "Uncertain" and preds == 1:
            return str3
        elif status == "Uncertain" and preds == 0:
            return str3
        elif status == "Pneumonia" and preds == 0:
            return str3
        else:
            return str3

    return None


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
