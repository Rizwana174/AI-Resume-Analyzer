from flask import Flask, render_template, request, redirect, session
import pdfplumber
import os
import sqlite3

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================

app.secret_key = "resume_analyzer_secret"

# =========================
# FOLDERS
# =========================

UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# =========================
# DATABASE PATH
# =========================

DATABASE_PATH = r'C:\Users\habee\Documents\database.db'

# =========================
# CREATE DATABASE TABLES
# =========================

def create_table():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    # Resume Table

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS resumes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT,

            score INTEGER,

            ats_score INTEGER,

            predicted_role TEXT
        )
        '''
    )

    # Users Table

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE,

            password TEXT
        )
        '''
    )

    conn.commit()

    conn.close()


create_table()

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    return render_template('index.html')

# =========================
# SIGNUP
# =========================

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        conn = sqlite3.connect(DATABASE_PATH)

        cursor = conn.cursor()

        try:

            cursor.execute(
                '''
                INSERT INTO users (username, password)
                VALUES (?, ?)
                ''',

                (username, password)
            )

            conn.commit()

        except:

            return "Username already exists"

        conn.close()

        return redirect('/login')

    return render_template('signup.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        conn = sqlite3.connect(DATABASE_PATH)

        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT * FROM users
            WHERE username=? AND password=?
            ''',

            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['user'] = username

            return redirect('/history')

        else:

            return "Invalid Username or Password"

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# =========================
# ANALYZE RESUME
# =========================

@app.route('/analyze', methods=['POST'])
def analyze():

    if 'resume' not in request.files:

        return "No file uploaded"

    file = request.files['resume']

    if file.filename == '':

        return "No selected file"

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file.filename
    )

    file.save(filepath)

    text = ""

    try:

        with pdfplumber.open(filepath) as pdf:

            for page in pdf.pages:

                extracted = page.extract_text()

                if extracted:

                    text += extracted

    except Exception as e:

        return f"Error reading PDF: {e}"

    skills = [

        "python",
        "java",
        "c",
        "html",
        "css",
        "javascript",
        "sql",
        "machine learning",
        "data science",
        "flask",
        "pandas",
        "numpy",
        "git",
        "github",
        "api",
        "communication",
        "problem solving"
    ]

    detected_skills = []

    lower_text = text.lower()

    for skill in skills:

        if skill in lower_text:

            detected_skills.append(skill)

    score = len(detected_skills) * 10

    if score > 100:

        score = 100

    ats_score = int(
        (
            len(detected_skills)
            /
            len(skills)
        ) * 100
    )

    suggestions = []

    if "sql" not in detected_skills:

        suggestions.append(
            "Add SQL skill"
        )

    if "flask" not in detected_skills:

        suggestions.append(
            "Add Flask project"
        )

    if "api" not in detected_skills:

        suggestions.append(
            "Add API integration experience"
        )

    missing_skills = []

    for skill in skills:

        if skill not in detected_skills:

            missing_skills.append(skill)

    predicted_role = "General Software Role"

    if (
        "machine learning" in detected_skills
        and
        "python" in detected_skills
    ):

        predicted_role = (
            "Machine Learning Engineer"
        )

    elif (
        "python" in detected_skills
        and
        "flask" in detected_skills
    ):

        predicted_role = (
            "Python Backend Developer"
        )

    elif (
        "html" in detected_skills
        and
        "css" in detected_skills
        and
        "javascript" in detected_skills
    ):

        predicted_role = "Web Developer"

    elif (
        "sql" in detected_skills
        and
        "pandas" in detected_skills
    ):

        predicted_role = "Data Analyst"

    if score >= 80:

        performance = "Excellent Resume"

    elif score >= 50:

        performance = "Good Resume"

    else:

        performance = "Needs Improvement"

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute(
        '''
        INSERT INTO resumes
        (
            filename,
            score,
            ats_score,
            predicted_role
        )

        VALUES (?, ?, ?, ?)
        ''',

        (
            file.filename,
            score,
            ats_score,
            predicted_role
        )
    )

    conn.commit()

    conn.close()

    return render_template(

        'index.html',

        extracted_text=text,

        skills=detected_skills,

        score=score,

        performance=performance,

        suggestions=suggestions,

        ats_score=ats_score,

        missing_skills=missing_skills,

        predicted_role=predicted_role
    )

# =========================
# HISTORY DASHBOARD
# =========================

@app.route('/history')
def history():

    if 'user' not in session:

        return redirect('/login')

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT
            filename,
            score,
            ats_score,
            predicted_role
        FROM resumes
        '''
    )

    data = cursor.fetchall()

    conn.close()

    return render_template(
        'history.html',
        data=data
    )

# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(debug=True)