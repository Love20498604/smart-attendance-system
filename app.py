from flask import Flask, render_template, request,  url_for, jsonify
import csv
import os
import base64
import cv2
import numpy as np
import face_recognition
import numpy as np



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template("login.html" )


@app.route('/login' , methods=["POST"])
def login():
    image_data=request.form.get("captured_image")
    if not image_data:
        return "No image recieved. Please try again."
    
    try:

        header , encoded=image_data.split(",", 1)
        image_byte=base64.b64decode(encoded)
    except Exception as e :
        return f"Error decoding image: {str(e)}"
    
    nparr = np.frombuffer(image_byte, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)   # decode numpy vector array into image matrix form

    if img is None:
        return "error decoding image."
    
    rgb_img = cv2.cvtColor(img , cv2.COLOR_BGR2RGB)

    face_locations=face_recognition.face_locations(rgb_img)

    if not face_locations:
        return "NO face detected."
    
    face_encodings=face_recognition.face_encodings(rgb_img , face_locations)
    
    if not face_encodings:
        return "could not extract face encoding."
    
    current_encoding=face_encodings[0]

    encoding_dir= "encodings"
    matched_user =None

    for file in os.listdir(encoding_dir):
        if file.endswith('.npy'):
            saved_encoding = np.load(os.path.join(encoding_dir, file))[0]
            match = face_recognition.compare_faces([saved_encoding], current_encoding, tolerance=0.5)
            if match[0]:
                matched_user = file.replace(".npy", "")
                break

    if matched_user:
        return f"Welcome, {matched_user}! Login successful."
    else:
        return "No matching face found. Please try again or register first."

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    image_data = request.form.get('image_data')

    if not image_data:
        return "No image recieved."
    
    try:
        encoding_path=""
        # Save image if present
        image_filename = ""
        
        # image_data looks like 'data:image/png;base64,iVBORw0KGgoAAAANS...'
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return "Failed to decode image"

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = face_cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(50,50))

        face_location = face_recognition.face_locations(rgb)

        if not face_location:
            return "NO face detected , PLease capture your photo again."   
        if len(faces) != 1:
            return "Please ensure only one face is visible during registration."
        

        encoding=face_recognition.face_encodings(rgb , face_location)
        if not encoding:
            return "could not generate face encoding"

        encoding=encoding[0]
        os.makedirs('encodings', exist_ok=True)
        
        for file in os.listdir('encodings'):
            if file.endswith('.npy'):
                existing_encoding=np.load(os.path.join("encodings" , file))[0]
                match=face_recognition.compare_faces([existing_encoding], encoding , tolerance=0.5)
                if match[0]:
                    return "This Face image already in the system."


        encoding_path=f"encodings/{first_name}_{last_name}.npy"
        np.save(encoding_path, [encoding])

                              
        # Create images folder if it doesn't exist
        os.makedirs('static/images', exist_ok=True)
        image_filename = f"static/images/{first_name}_{last_name}_face.png"
        with open(image_filename, 'wb') as f:
            f.write(image_bytes)

        # Save user data and image filename to CSV
        file_exists = os.path.isfile('users.csv')
        with open('users.csv', 'a', newline='') as csvfile:
            fieldnames = ['first_name', 'last_name', 'email', 'image_file' , "encoded_file"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'image_file': image_filename,
                "encoded_file": encoding_path
            })

        return f"Thanks {first_name}, you have been registered successfully! Image saved as {image_filename}"
    
    
    except Exception as e:
        return f"Registration failed: {str(e)}"





if __name__ == '__main__':
    app.run(debug=True)
