from flask import Flask, request, render_template_string, url_for
import csv
import os

app = Flask(__name__)

registration_form = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=initial-scale=1.0">
    <title>Register</title>
    <link rel="stylesheet" href="{{ url_for('static' , filename='register_style.css')}}">
</head>
<body>
    <header>
        <h1>Register for SMART ATTENDANCE</h1>
    </header>

    <main>
        <div class="register-container">

            <form id="register-form" method="POST" action="/register">

                <div class="form-fields">

                    <input type="text" name="first_name" placeholder="First Name" required/>
                    <input type="text" name="last_name" placeholder="Last Name" required/>
                    <input type="email" name="email" placeholder="Email" required/>
                    <input type="text" name="username" placeholder="Username" required/>
                    <input type="password" name="password" placeholder="Password" required/>
            
                </div>

                <div class="photo capture">

                    <button type="button" onclick="captureImage()">Capture face Image</button>
                    <p id="captureStatus"></p>   
                    
                </div>
                <button class="register-button" type="submit">Register</button>
            </form>

        </div>
    </main>

    <footer>
        <p>Already have an account? <a href="login.html">Login here</a></p>
    </footer>

    <script>
        function captureImage() {
            const captureStatus = document.getElementById("captureStatus");
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            captureStatus.textContent = `Image captured: face_${timestamp}.png`;
        }
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
    username = request.form.get('username')
    password = request.form.get('password')

    # Save to CSV
    file_exists = os.path.isfile('users.csv')
    with open('users.csv', 'a', newline='') as csvfile:
        fieldnames = ['first_name', 'last_name', 'email', 'username', 'password']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
            'password': password
        })

    return f"Thanks {first_name}, you have been registered successfully!"

if __name__ == '__main__':
    app.run(debug=True)
