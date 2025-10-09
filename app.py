from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Result, Attendance
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import os
from datetime import date

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mru_clone.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Wrap User model for Flask-Login by creating a tiny mixin
class AuthUser(UserMixin):
    def __init__(self, user: User):
        self.user = user
    def get_id(self):
        return str(self.user.id)

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    if not u:
        return None
    return AuthUser(u)

# ------------------------------------------------
# Public pages (you probably already have these)
# ------------------------------------------------
@app.route("/")
def index():
    schools = [
        {"name": "School of Engineering", "desc": "B.Tech, M.Tech, PhD programs"},
        {"name": "School of Management", "desc": "MBA, BBA programs"},
        {"name": "School of Sciences", "desc": "B.Sc, M.Sc, PhD programs"},
    ]
    events = [
        {"title": "Tech Fest 2025", "date": "March 15, 2025"},
        {"title": "Convocation Ceremony", "date": "July 10, 2025"},
    ]
    return render_template("index.html", title="Home", schools=schools, events=events)

@app.route("/about")
def about():
    return render_template("about.html", title="About Us")

@app.route("/academics")
def academics():
    schools = [
        {"name": "School of Engineering", "desc": "B.Tech, M.Tech, PhD programs"},
        {"name": "School of Management", "desc": "MBA, BBA programs"},
    ]
    return render_template("academics.html", title="Academics", schools=schools)

@app.route("/admissions")
def admissions():
    return render_template("admissions.html", title="Admissions")

@app.route("/campuslife")
def campuslife():
    return render_template("campuslife.html", title="Campus Life")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact Us")

# ------------------------------------------------
# Authentication
# ------------------------------------------------
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        roll_no = request.form.get("roll_no")
        course = request.form.get("course")
        year = request.form.get("year")
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register_student"))
        user = User(
            role="student",
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            roll_no=roll_no,
            course=course,
            year=year
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("auth/register_student.html", title="Student Registration")

@app.route("/register/faculty", methods=["GET", "POST"])
def register_faculty():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register_faculty"))
        user = User(
            role="faculty",
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash("Faculty registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("auth/register_faculty.html", title="Faculty Registration")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(AuthUser(user))
            flash("Logged in successfully.", "success")
            # redirect based on role
            if user.role == "student":
                return redirect(url_for("student_profile"))
            else:
                return redirect(url_for("faculty_profile"))
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html", title="Login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("index"))

# ------------------------------------------------
# Student dashboard & actions
# ------------------------------------------------
@app.route("/student/profile")
@login_required
def student_profile():
    # ensure current_user is a student
    user = current_user.user
    if not user.is_student():
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    # fetch results and attendance for this student
    results = Result.query.filter_by(student_id=user.id).all()
    attendance_records = Attendance.query.filter_by(student_id=user.id).all()

    # compute attendance percentage for display
    total = len(attendance_records)
    present_count = sum(1 for a in attendance_records if a.present)
    attendance_pct = (present_count / total * 100) if total > 0 else None

    return render_template("student_profile.html",
                            title="Student Dashboard",
                            user=user,
                            results=results,
                            attendance_pct=attendance_pct,
                            attendance_records=attendance_records)

# ------------------------------------------------
# Faculty dashboard & actions
# ------------------------------------------------
@app.route("/faculty/profile")
@login_required
def faculty_profile():
    user = current_user.user
    if not user.is_faculty():
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    # show basic faculty info and a list of students
    students = User.query.filter_by(role="student").all()
    return render_template("faculty_profile.html",
                            title="Faculty Dashboard",
                            user=user,
                            students=students)

# Faculty: Post attendance
@app.route("/faculty/attendance", methods=["POST"])
@login_required
def faculty_post_attendance():
    user = current_user.user
    if not user.is_faculty():
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    # expected form: student_id, date, present (on/off)
    student_id = request.form.get("student_id")
    date_str = request.form.get("date")
    present_val = request.form.get("present")  # "on" if checkbox checked

    try:
        att_date = date.fromisoformat(date_str)
    except Exception:
        flash("Invalid date format. Use YYYY-MM-DD", "danger")
        return redirect(url_for("faculty_profile"))

    present = True if present_val == "on" else False
    attendance = Attendance(student_id=int(student_id),
                            faculty_id=user.id,
                            date=att_date,
                            present=present)
    db.session.add(attendance)
    db.session.commit()
    flash("Attendance recorded", "success")
    return redirect(url_for("faculty_profile"))

# Faculty: Add or update marks for a student
@app.route("/faculty/marks", methods=["POST"])
@login_required
def faculty_update_marks():
    user = current_user.user
    if not user.is_faculty():
        flash("Access denied", "danger")
        return redirect(url_for("index"))

    student_id = int(request.form.get("student_id"))
    subject = request.form.get("subject")
    marks = float(request.form.get("marks"))
    term = request.form.get("term") or "Semester 1"

    # check if a result for subject+term exists for this student; update if so otherwise insert
    existing = Result.query.filter_by(student_id=student_id, subject=subject, term=term).first()
    if existing:
        existing.marks = marks
        flash("Marks updated", "success")
    else:
        r = Result(student_id=student_id, subject=subject, marks=marks, term=term)
        db.session.add(r)
        flash("Marks added", "success")
    db.session.commit()
    return redirect(url_for("faculty_profile"))


if __name__ == "__main__":
    # ensure DB exists
    with app.app_context():
        db.create_all()
    app.run(debug=True)
