from flask import Flask, render_template, request,  url_for, jsonify , flash
import os
import base64
import cv2
from flask import session
import face_recognition
import numpy as np
from flask import redirect
from datetime import datetime


from database import db
from database import Registered_User
from database import LoginLog



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db.init_app(app)


app.secret_key = 'key_123'


def count_total_registered_students():
    return Registered_User.query.count()

def count_total_present_students():
    return LoginLog.query.count()

def load_recent_logs(limit=10):
    recent_entries = LoginLog.query.order_by(LoginLog.id.desc()).limit(limit).all()
    logs = [
        {
            'name': entry.name,
            'date': entry.date,
            'time': entry.time,
            'status': 'Present'
        }
        for entry in recent_entries
    ]
    return logs





@app.route('/')
@app.route('/home')
def home_page():
    teacher_name=session.get("teacher_name")
    return render_template('index.html' , teacher_name=teacher_name)


@app.route('/Sign Out')
def new_home_page():
    session.clear()
    return render_template('index.html')


@app.route('/Get Started')
@app.route('/teacher_dashboard')
def teacher_login():
    teacher_name=session.get("teacher_name")
    if 'teacher_name' not in session:
        flash("Please sign in as a teacher to begin registering your students and taking attendance.")
        return render_template('teacher_dashboard.html' )
    
    search_date = request.args.get('search_date', '').strip()

    query = LoginLog.query

    if search_date:
        query = query.filter(LoginLog.date == search_date)
    logs = query.order_by(LoginLog.id.desc()).limit(10).all()
    return render_template('teacher_stat.html',
                           teacher_name=teacher_name,
                           total_registered=Registered_User.query.count(),
                           total_present=LoginLog.query.count(),
                           logs=logs)




@app.route('/teacher_dashboard' , methods= ['POST'])
def teacher_login_page():
    admin_name=request.form.get("Name")
    admin_password=request.form.get("Password")
    if admin_name=='123' and admin_password=='123' :
        session['teacher_name']=admin_name
        return render_template("teacher_stat.html" ,
            total_registered=count_total_registered_students(),
            total_present=count_total_present_students(), 
            logs=load_recent_logs(limit=10) )
    else:
        flash("Wrong Teacher id or password")
        return render_template('teacher_dashboard.html')



@app.route('/Attendance')
@app.route('/Take Attendance')
def login_page():
    teacher_name=session['teacher_name']
    login_logs=LoginLog.query.order_by(LoginLog.id.desc()).limit(10).all()
    
    return render_template('login.html' , login_logs=login_logs , teacher_name=session['teacher_name'] )
     
    

@app.route('/login', methods=["POST"])
def login():
    login_logs = []
    
    image_data = request.form.get("captured_image")

    if not image_data:
        return render_template("login.html", error="No image received. Please try again.", login_logs=login_logs)

    try:
        header, encoded = image_data.split(",", 1)
        image_byte = base64.b64decode(encoded)
    except Exception as e:
        return render_template("login.html", error=f"Error decoding image: {str(e)}", login_logs=login_logs)

    nparr = np.frombuffer(image_byte, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return render_template("login.html", error="Error decoding image.", login_logs=login_logs)

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_img)

    if not face_locations:
        return render_template("login.html", error="No Face Detected. Please try again.", login_logs=login_logs)

    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

    if not face_encodings:
        return render_template("login.html", error="Could not extract face encoding.", login_logs=login_logs)

    current_encoding = face_encodings[0]

    encoding_dir = "encodings"
    matched_user = None

    for file in os.listdir(encoding_dir):
        if file.endswith('.npy'):
            saved_encoding = np.load(os.path.join(encoding_dir, file))[0]
            match = face_recognition.compare_faces([saved_encoding], current_encoding, tolerance=0.5)
            if match[0]:
                matched_user = file.replace(".npy", "")
                break

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")
    fieldnames = ['name', "date", "time"]

    if matched_user:
        log=LoginLog(name=matched_user , date=date , time=time)
        db.session.add(log)
        db.session.commit()
        return redirect(url_for("login_page") )
    else:
        return render_template("login.html", error="No matching face found. Please try again or register first.", login_logs=login_logs)


@app.route('/register', methods=['GET'])
def register_page():
    users=[]
    
    if 'teacher_name' not in session:

        flash("Please , Let a teacher sign in first to register new students and take attendance.")
        return redirect(url_for('teacher_login'))
    
    search_date=request.args.get('search_date')
    if search_date:
        users=Registered_User.query.filter_by(date=search_date).all()

    else:
        users=Registered_User.query.all()   
    return render_template('register.html' , users=users , teacher_name=session['teacher_name'])


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

        new_user=Registered_User(
            first_name=first_name,
            last_name=last_name,
            email = email , 
            image_file=image_filename , 
            encoded_file=encoding_path, 
            date=current_date, 
            time= current_time
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("register_page"))
    
    
    except Exception as e:
        return f"Registration failed: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
