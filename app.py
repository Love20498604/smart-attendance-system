from flask import Flask, render_template, request,  url_for, jsonify , flash
import csv
import os
import base64
import cv2
from flask import session
import face_recognition
import numpy as np
from flask import redirect
from datetime import datetime



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024



app.secret_key = 'key_123'

@app.route('/')
@app.route('/home')
def home_page():
    teacher_name=session.get("teacher_name")
    return render_template('index.html' , teacher_name=teacher_name)

@app.route('/Sign Out')
def new_home_page():
    session.clear()
    return redirect(url_for('home_page'))

@app.route('/Get Started')
@app.route('/teacher_dashboard')
def teacher_login():
    teacher_name=session.get("teacher_name")
    if 'teacher_name' not in session:
        flash("Please sign in as a teacher to begin registering your students and taking attendance.")
        return render_template('teacher_dashboard.html')
    return f"you are already signed as {teacher_name}"



@app.route('/teacher_dashboard' , methods= ['POST'])
def teacher_login_page():
    admin_name=request.form.get("Name")
    admin_password=request.form.get("Password")
    if admin_name=='123' and admin_password=='123' :
        session['teacher_name']=admin_name
        return redirect(url_for("home_page") )
    else:
        flash("Wrong Teacher id or password")
        return render_template('teacher_dashboard.html')

@app.route('/Attendance')
@app.route('/Take Attendance')
def login_page():
    teacher_name=session['teacher_name']
    login_logs=[]
    if os.path.exists('login_logs.csv'):
        read_file=open('login_logs.csv' , 'r')
        reader=csv.DictReader(read_file)
        login_logs=list(reader)
    return render_template('login.html' , login_logs=login_logs , teacher_name=session['teacher_name'] )
    
    
 


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
                    
        now=datetime.now()
        date=now.strftime("%Y-%m-%d")
        time=now.strftime("%H-%M-%S")
        fieldnames=['name' , "date",  "time"]
        if matched_user:
            with open("login_logs.csv", "a", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                # write header if file is new
                if file.tell() == 0:
                    writer.writeheader()
                writer.writerow({
                    "name": matched_user,
                    "date": date,
                    "time": time
                })

            flash("No matching face found. Please try again or register first.") 
            return redirect(url_for('login_page'))
        
    


@app.route('/register', methods=['GET'])
def register_page():
    users=[]
    
    if 'teacher_name' in session:

        if os.path.exists("users.csv"):
            csv_file=open("users.csv" , "r")
            reader=csv.DictReader(csv_file)
            users=list(reader)        
        return render_template('register.html' , users=users , teacher_name=session['teacher_name'])

    flash("Please , Let a teacher sign in first to register new students and take attendance.")
    return redirect(url_for('teacher_login'))


@app.route('/register', methods=['POST'])
def register():
    now=datetime.now()
    current_date=now.strftime('%Y-%m-%d')
    current_time=now.strftime('%H-%M-%S')

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
            fieldnames = ['first_name', 'last_name', 'email', 'image_file' , "encoded_file", 'Date' , "Time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'image_file': image_filename,
                "encoded_file": encoding_path,
                "Date": current_date,
                'Time' : current_time
            })

        return redirect(url_for("register_page"))
    
    
    except Exception as e:
        return f"Registration failed: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
