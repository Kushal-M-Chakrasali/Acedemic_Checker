
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PyPDF2 import PdfReader
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

app = Flask(__name__)
app.secret_key = "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"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Gemini API Key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# =====================================================
# DATABASE
# =====================================================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            analysis TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# UTILITIES
# =====================================================

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_pdf_text(pdf_path):
    text = ""

    try:
        reader = PdfReader(pdf_path)

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

    except Exception as e:
        print("PDF Error:", e)

    return text


def analyze_syllabus(text):
    prompt = f"""
You are an expert placement mentor.

Analyze the following college syllabus.

Provide:

1. Key Topics Found
2. Industry-Relevant Skills Missing
3. Gap Score (0-100%)
4. Placement Readiness
5. Recommended Technologies
6. Certifications
7. Project Ideas
8. Personalized Learning Roadmap

SYLLABUS:
{text[:15000]}
"""

    response = model.generate_content(prompt)

    return response.text

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users(name,email,password)
                VALUES(?,?,?)
            """, (name, email, password))

            conn.commit()

            flash("Registration Successful", "success")

            return redirect(url_for("login"))

        except:
            flash("Email already exists", "danger")

        finally:
            conn.close()

    return render_template("register.html")


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE email=? AND password=?
        """, (email, password))

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            flash("Login Successful", "success")

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM reports
        WHERE user_id=?
        ORDER BY id DESC
    """, (session["user_id"],))

    reports = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        reports=reports,
        username=session["user_name"]
    )


# =====================================================
# UPLOAD
# =====================================================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        if "pdf" not in request.files:
            flash("No file selected", "danger")
            return redirect(request.url)

        file = request.files["pdf"]

        if file.filename == "":
            flash("No file selected", "danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            flash("PDF Uploaded Successfully", "success")

            # Extract text
            syllabus_text = extract_pdf_text(filepath)

            # AI Analysis
            analysis = analyze_syllabus(syllabus_text)

            # Save report
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO reports
                (user_id, filename, analysis, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                session["user_id"],
                filename,
                analysis,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()

            report_id = cursor.lastrowid

            conn.close()

            return redirect(
                url_for("view_report", report_id=report_id)
            )

    return render_template("upload.html")


# =====================================================
# REPORT VIEW
# =====================================================

@app.route("/report/<int:report_id>")
def view_report(report_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM reports
        WHERE id=?
    """, (report_id,))

    report = cursor.fetchone()

    conn.close()

    if report is None:
        flash("Report Not Found", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "report.html",
        report=report
    )


# =====================================================
# DELETE REPORT
# =====================================================

@app.route("/delete/<int:report_id>")
def delete_report(report_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM reports
        WHERE id=?
    """, (report_id,))

    conn.commit()
    conn.close()

    flash("Report Deleted", "success")

    return redirect(url_for("dashboard"))


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully", "success")

    return redirect(url_for("login"))


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    if not os.path.exists("static/uploads"):
        os.makedirs("static/uploads")

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
