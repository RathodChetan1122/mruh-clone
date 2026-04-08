from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 

db = SQLAlchemy()  
   
class User(db.Model):  
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)  
    role = db.Column(db.String(20), nullable=False)  # "student" or "faculty"
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Student-specific fields (nullable for faculty)
    roll_no = db.Column(db.String(50), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)

    def is_student(self):
        return self.role == "student"
    def is_faculty(self):
        return self.role == "faculty"


class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, default=100.0)
    term = db.Column(db.String(50), default="Semester 1")

    student = db.relationship("User", backref="results")


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    present = db.Column(db.Boolean, default=True)

    student = db.relationship("User", foreign_keys=[student_id])
    faculty = db.relationship("User", foreign_keys=[faculty_id])
