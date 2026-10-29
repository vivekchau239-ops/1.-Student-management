import json
import hmac
import os
import secrets
from functools import wraps

from flask import (
    Flask,
    make_response,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

FILE = os.path.join(app.root_path, "students.json")
USERS_FILE = os.path.join(app.root_path, "users.json")
ADMINS_FILE = os.path.join(app.root_path, "admins.json")
ADMIN_REQUESTS_FILE = os.path.join(app.root_path, "admin_requests.json")
STUDENT_REQUESTS_FILE = os.path.join(app.root_path, "student_requests.json")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_dashboard"))
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def load_students():
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_admin_requests():
    if os.path.exists(ADMIN_REQUESTS_FILE):
        with open(ADMIN_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_student_requests():
    if os.path.exists(STUDENT_REQUESTS_FILE):
        with open(STUDENT_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def save_admins(admins):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=4)


def save_admin_requests(admin_requests):
    with open(ADMIN_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(admin_requests, f, indent=4)


def save_student_requests(student_requests):
    with open(STUDENT_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(student_requests, f, indent=4)


def save_students(students):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, indent=4)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if session.get("logged_in"):
        return redirect(url_for("home"))

    message = (
        "Registration successful. You can now sign in."
        if request.args.get("registered") == "1"
        else ""
    )
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = load_users().get(username)

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["logged_in"] = username
            return redirect(url_for("home"))

        message = "Incorrect username or password."

    return render_template("login.html", message=message)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    message = (
        "Admin account created. You can now sign in."
        if request.args.get("registered") == "1"
        else ""
    )
    if request.method == "POST":
        configured_username = os.environ.get("ADMIN_USERNAME", "").strip()
        configured_password = os.environ.get("ADMIN_PASSWORD", "")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = load_admins().get(username.lower())

        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        if (
            configured_username
            and configured_password
            and hmac.compare_digest(
                username.lower(), configured_username.lower()
            )
            and hmac.compare_digest(password, configured_password)
        ):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            message = "Incorrect admin username or password."

    return render_template(
        "admin_login.html",
        message=message,
    )


@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            message = "Please fill all fields."
        elif len(username) < 3 or len(username) > 32:
            message = "Username must be between 3 and 32 characters."
        elif len(password) < 8:
            message = "Password must be at least 8 characters."
        elif password != confirm_password:
            message = "Passwords do not match."
        else:
            username_key = username.lower()
            admin_requests = load_admin_requests()
            if (
                username_key in load_admins()
                or username_key in load_users()
                or username_key in admin_requests
            ):
                message = "That username already exists or has a pending request."
            else:
                admin_requests[username_key] = {
                    "username": username,
                    "password_hash": generate_password_hash(password),
                }
                save_admin_requests(admin_requests)
                return redirect(url_for("admin_register", submitted="1"))

    response = make_response(
        render_template(
            "admin_register.html",
            message=message,
            submitted=request.args.get("submitted") == "1",
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    students = load_students()
    admin_requests = load_admin_requests()
    student_requests = load_student_requests()
    message = ""

    if request.method == "POST":
        roll = request.form.get("roll", "").strip()
        name = request.form.get("name", "").strip()
        marks_text = request.form.get("marks", "").strip()

        if not roll or not name or not marks_text:
            message = "Please fill all fields."
        elif roll in students:
            message = "Roll number already exists."
        else:
            try:
                marks = float(marks_text)
                if not 0 <= marks <= 100:
                    message = "Marks must be between 0 and 100."
                else:
                    students[roll] = {"name": name, "marks": marks}
                    save_students(students)
                    return redirect(url_for("admin_dashboard"))
            except ValueError:
                message = "Enter valid marks."

    records = [{"roll": roll, **info} for roll, info in students.items()]
    response = make_response(
        render_template(
            "admin.html",
            students=records,
            message=message,
            admin_requests=list(admin_requests.values()),
            student_requests=list(student_requests.values()),
            student_request_error=(
                request.args.get("student_request_error") == "duplicate"
            ),
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/admin/requests/<username>/approve", methods=["POST"])
@admin_required
def approve_admin_request(username):
    username_key = username.lower()
    admin_requests = load_admin_requests()
    admin_request = admin_requests.get(username_key)

    if admin_request:
        admins = load_admins()
        users = load_users()
        if username_key not in admins and username_key not in users:
            admins[username_key] = admin_request
            save_admins(admins)
        del admin_requests[username_key]
        save_admin_requests(admin_requests)

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/requests/<username>/reject", methods=["POST"])
@admin_required
def reject_admin_request(username):
    admin_requests = load_admin_requests()
    if username.lower() in admin_requests:
        del admin_requests[username.lower()]
        save_admin_requests(admin_requests)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/student-requests/<roll>/approve", methods=["POST"])
@admin_required
def approve_student_request(roll):
    student_requests = load_student_requests()
    student_request = student_requests.get(roll)

    if student_request:
        students = load_students()
        if roll in students:
            return redirect(
                url_for(
                    "admin_dashboard",
                    student_request_error="duplicate",
                )
            )
        students[roll] = {
            "name": student_request["name"],
            "marks": student_request["marks"],
        }
        save_students(students)
        del student_requests[roll]
        save_student_requests(student_requests)

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/student-requests/<roll>/reject", methods=["POST"])
@admin_required
def reject_student_request(roll):
    student_requests = load_student_requests()
    if roll in student_requests:
        del student_requests[roll]
        save_student_requests(student_requests)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<roll>", methods=["POST"])
@admin_required
def admin_delete_student(roll):
    students = load_students()
    if roll in students:
        del students[roll]
        save_students(students)
    return redirect(url_for("admin_dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in") or session.get("admin_logged_in"):
        return redirect(url_for("home"))

    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            message = "Please fill all fields."
        elif len(username) < 3 or len(username) > 32:
            message = "Username must be between 3 and 32 characters."
        elif len(password) < 8:
            message = "Password must be at least 8 characters."
        elif password != confirm_password:
            message = "Passwords do not match."
        else:
            users = load_users()
            username_key = username.lower()
            if username_key in users:
                message = "That username is already registered."
            else:
                users[username_key] = {
                    "username": username,
                    "password_hash": generate_password_hash(password),
                }
                save_users(users)
                return redirect(url_for("login", registered="1"))

    return render_template("register.html", message=message)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    message = ""
    visible_students = []
    query = ""
    searched = False

    if request.method == "POST":
        query = request.form.get("q", "").strip().lower()
        password = request.form.get("password", "")
        username = session["logged_in"]
        user = load_users().get(username)

        if not user or not check_password_hash(user["password_hash"], password):
            message = "Incorrect password. Student records are still hidden."
        elif not query:
            message = "Enter a name or roll number to search."
        else:
            students = load_students()
            visible_students = [
                {"roll": roll, **info}
                for roll, info in students.items()
                if query in roll.lower()
                or query in info["name"].lower()
            ]
            searched = True

    response = make_response(
        render_template(
            "index.html",
            students=visible_students,
            message=message,
            query=query,
            searched=searched,
            request_submitted=request.args.get("request_submitted") == "1",
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/student/request", methods=["POST"])
@login_required
def request_student_record():
    roll = request.form.get("roll", "").strip()
    name = request.form.get("name", "").strip()
    marks_text = request.form.get("marks", "").strip()
    students = load_students()
    student_requests = load_student_requests()
    message = ""

    if not roll or not name or not marks_text:
        message = "Please fill all fields before sending the request."
    elif roll in students or roll in student_requests:
        message = "That roll number already exists or has a pending request."
    else:
        try:
            marks = float(marks_text)
            if not 0 <= marks <= 100:
                message = "Marks must be between 0 and 100."
            else:
                student_requests[roll] = {
                    "roll": roll,
                    "name": name,
                    "marks": marks,
                    "requested_by": session["logged_in"],
                }
                save_student_requests(student_requests)
                return redirect(url_for("home", request_submitted="1"))
        except ValueError:
            message = "Enter valid marks."

    response = make_response(
        render_template(
            "index.html",
            students=[],
            message=message,
            query="",
            searched=False,
            request_submitted=False,
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(debug=True)