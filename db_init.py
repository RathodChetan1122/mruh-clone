from app import app
from models import db, User, Result, Attendance
from werkzeug.security import generate_password_hash
from datetime import date

with app.app_context():
    db.drop_all()
    db.create_all()

    # create sample faculty
    f1 = User(role="faculty", name="Dr. S. Rao", email="rao@demo.edu", password_hash=generate_password_hash("faculty123"))
    db.session.add(f1)
    db.session.commit()

    # create sample students
    s1 = User(role="student", name="Ravi Kumar", email="ravi@demo.edu", password_hash=generate_password_hash("student123"),
              roll_no="R001", course="B.Tech CSE", year="2nd Year")
    s2 = User(role="student", name="Priya Sharma", email="priya@demo.edu", password_hash=generate_password_hash("student123"),
              roll_no="R002", course="B.Tech ECE", year="1st Year")
    db.session.add_all([s1, s2])
    db.session.commit()

    # add sample results
    r1 = Result(student_id=s1.id, subject="Mathematics", marks=78)
    r2 = Result(student_id=s1.id, subject="Physics", marks=85)
    r3 = Result(student_id=s2.id, subject="Mathematics", marks=92)
    db.session.add_all([r1, r2, r3])
    db.session.commit()

    # add sample attendance
    a1 = Attendance(student_id=s1.id, faculty_id=f1.id, date=date(2025,3,1), present=True)
    a2 = Attendance(student_id=s1.id, faculty_id=f1.id, date=date(2025,3,2), present=False)
    db.session.add_all([a1, a2])
    db.session.commit()

    print("DB initialized with sample data.")
