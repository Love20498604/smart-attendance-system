from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Registered_User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    image_file = db.Column(db.String(255))
    encoded_file = db.Column(db.String(255))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))


class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)      
    name = db.Column(db.String(100))                  
    date = db.Column(db.String(20))                  
    time = db.Column(db.String(20))                    
