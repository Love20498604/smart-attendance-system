from flask import Flask, request, render_template_string, url_for, jsonify
import csv
import os
import base64
import cv2
import numpy as np
import face_recognition
import numpy as np



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

registration_form = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Register</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='register_style.css') }}">
</head>
<body>
    <header>
        <h1>Register for SMART ATTENDANCE</h1>
    </header>

    <main>
        <div class="register-container">

            <form id="register-form" method="POST" action="/register" enctype="multipart/form-data">

                <div class="form-fields">
                    <input type="text" name="first_name" placeholder="First Name" required />
                    <input type="text" name="last_name" placeholder="Last Name" required />
                    <input type="email" name="email" placeholder="Email" required />
                    
                </div>

                <div class="photo-capture">
                    <video id="video" width="320" height="240" autoplay></video>
                    <button type="button" id="snap">Capture Face Image</button>
                    <canvas id="canvas" width="320" height="240" style="display:none;"></canvas>
                    <img id="captured-image" alt="Captured Image" style="display:none; margin-top:10px;"/>
                    <input type="hidden" name="captured_image" id="captured_image_input" />
                </div>

                <button class="register-button" type="submit">Register</button>
            </form>

        </div>
    </main>

    <footer>
        <p>Already have an account? <a href="login.html">Login here</a></p>
    </footer>

<script>
    // Access webcam and stream video to video element
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const snapBtn = document.getElementById('snap');
    const capturedImage = document.getElementById('captured-image');
    const capturedImageInput = document.getElementById('captured_image_input');

    // Prompt user for webcam access
    navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
        video.srcObject = stream;
    })
    .catch((err) => {
        alert('Error accessing webcam: ' + err);
    });

    // Capture image from video stream on button click
    snapBtn.addEventListener('click', () => {
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataURL = canvas.toDataURL('image/png');

        // Show captured image preview
        capturedImage.src = imageDataURL;
        capturedImage.style.display = 'block';

        // Put base64 image string into hidden form input for submission
        capturedImageInput.value = imageDataURL;
    });
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(registration_form, url_for=url_for)

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    image_data = request.form.get('captured_image')

    # Save image if present
    image_filename = ""
    
    if image_data:
        # image_data looks like 'data:image/png;base64,iVBORw0KGgoAAAANS...'
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = face_cascade.detectMultiScale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(50,50))

        face_location = face_recognition.face_locations(rgb)
        if face_location:

            encoding=face_recognition.face_encodings(rgb , face_location)
            os.makedirs('encodings', exist_ok=True)
            encoding_path=f"encodings/{first_name}_{last_name}.npy"
            np.save(encoding_path, encoding)

        elif len(faces)==0:
            return "NO face detected , PLease capture your photo again."      

        elif len(faces)>1:
            return "NO more than 1 face at a time. Try again."        
                              
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

if __name__ == '__main__':
    app.run(debug=True)
