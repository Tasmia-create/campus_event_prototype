from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
DATABASE = "database.db"

# -------------------------
# Initialize the database
# -------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Colleges table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Colleges (
                        college_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    )''')

    # Students table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Students (
                        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        college_id INTEGER,
                        FOREIGN KEY (college_id) REFERENCES Colleges(college_id)
                    )''')

    # Events table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        type TEXT NOT NULL,
                        date TEXT NOT NULL,
                        college_id INTEGER,
                        FOREIGN KEY (college_id) REFERENCES Colleges(college_id)
                    )''')

    # Registrations table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Registrations (
                        registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        event_id INTEGER,
                        FOREIGN KEY (student_id) REFERENCES Students(student_id),
                        FOREIGN KEY (event_id) REFERENCES Events(event_id)
                    )''')

    # Attendance table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Attendance (
                        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        event_id INTEGER,
                        status TEXT CHECK(status IN ('Present', 'Absent')),
                        FOREIGN KEY (student_id) REFERENCES Students(student_id),
                        FOREIGN KEY (event_id) REFERENCES Events(event_id)
                    )''')

    # Feedback table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Feedback (
                        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        event_id INTEGER,
                        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                        FOREIGN KEY (student_id) REFERENCES Students(student_id),
                        FOREIGN KEY (event_id) REFERENCES Events(event_id)
                    )''')

    # Seed dummy events
    cursor.execute("SELECT COUNT(*) FROM Events")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Events (title, type, date) VALUES (?, ?, ?)",
                       ("Tech Fest", "Workshop", "2025-09-15"))
        cursor.execute("INSERT INTO Events (title, type, date) VALUES (?, ?, ?)",
                       ("Cultural Night", "Cultural", "2025-09-20"))

    conn.commit()
    conn.close()

# -------------------------
# Home Page
# -------------------------
@app.route("/")
def home():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, title, type, date FROM Events")
    events = cursor.fetchall()
    conn.close()
    return render_template("home.html", events=events)

# -------------------------
# Add Event
# -------------------------
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        title = request.form["title"]
        event_type = request.form["type"]
        date = request.form["date"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Events (title, type, date) VALUES (?, ?, ?)",
                       (title, event_type, date))
        conn.commit()
        conn.close()

        flash("Event added successfully!", "success")
        return redirect(url_for("home"))

    return render_template("add_event.html")

# -------------------------
# Event Detail
# -------------------------
@app.route("/event/<int:event_id>")
def event_detail(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, title, type, date FROM Events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if event:
        return render_template("event_detail.html", event=event)
    else:
        flash("Event not found.", "danger")
        return redirect(url_for("home"))

# -------------------------
# Register Student
# -------------------------
@app.route("/register/<int:event_id>", methods=["GET", "POST"])
def register(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT event_id, title FROM Events")
    events = cursor.fetchall()

    if request.method == "POST":
        student_name = request.form["name"]
        selected_event_id = request.form.get("event_id", event_id)

        cursor.execute("INSERT INTO Students (name) VALUES (?)", (student_name,))
        student_id = cursor.lastrowid
        cursor.execute("INSERT INTO Registrations (student_id, event_id) VALUES (?, ?)",
                       (student_id, selected_event_id))
        conn.commit()
        conn.close()
        flash("Registered successfully!", "success")
        return redirect(url_for("home"))

    conn.close()
    return render_template("register.html", events=events, selected_event_id=event_id)

# -------------------------
# Attendance
# -------------------------
@app.route("/attendance/<int:event_id>", methods=["GET", "POST"])
def attendance(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Students.student_id, Students.name 
        FROM Students 
        JOIN Registrations ON Students.student_id = Registrations.student_id
        WHERE Registrations.event_id = ?
    """, (event_id,))
    students = cursor.fetchall()

    if request.method == "POST":
        for student in students:
            status = request.form.get(f"attendance_{student[0]}")
            if not status:
                continue

            cursor.execute("SELECT attendance_id FROM Attendance WHERE student_id = ? AND event_id = ?",
                           (student[0], event_id))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("UPDATE Attendance SET status = ? WHERE attendance_id = ?",
                               (status, existing[0]))
            else:
                cursor.execute("INSERT INTO Attendance (student_id, event_id, status) VALUES (?, ?, ?)",
                               (student[0], event_id, status))

        conn.commit()
        conn.close()
        flash("Attendance saved!", "success")
        return redirect(url_for("view_attendance", event_id=event_id))

    conn.close()
    return render_template("attendance.html", students=students, event_id=event_id)

# -------------------------
# Feedback
# -------------------------
@app.route("/feedback/<int:event_id>", methods=["GET", "POST"])
def feedback(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, name FROM Students")
    students = cursor.fetchall()

    if request.method == "POST":
        student_id = request.form["student_id"]
        rating = request.form["rating"]
        cursor.execute("INSERT INTO Feedback (student_id, event_id, rating) VALUES (?, ?, ?)",
                       (student_id, event_id, rating))
        conn.commit()
        conn.close()
        flash("Feedback submitted!", "success")
        return redirect(url_for("home"))

    conn.close()
    return render_template("feedback.html", students=students, event_id=event_id)

# -------------------------
# View Attendance / Feedback
# -------------------------
@app.route("/view_attendance/<int:event_id>")
def view_attendance(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Students.name, Attendance.status
        FROM Attendance 
        JOIN Students ON Attendance.student_id = Students.student_id
        WHERE Attendance.event_id = ?
    """, (event_id,))
    attendance_list = cursor.fetchall()
    conn.close()
    return render_template("view_attendance.html", attendance_list=attendance_list)

@app.route("/view_feedback/<int:event_id>")
def view_feedback(event_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Students.name, Feedback.rating
        FROM Feedback 
        JOIN Students ON Feedback.student_id = Students.student_id
        WHERE Feedback.event_id = ?
    """, (event_id,))
    feedbacks = cursor.fetchall()
    conn.close()
    return render_template("view_feedback.html", feedbacks=feedbacks)

# -------------------------
# Reports
# -------------------------
@app.route("/reports/registrations")
def report_registrations():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Events.title, COUNT(Registrations.registration_id) 
        FROM Events
        LEFT JOIN Registrations ON Events.event_id = Registrations.event_id
        GROUP BY Events.event_id
    """)
    data = cursor.fetchall()
    conn.close()
    return render_template("report_registrations.html", data=data)

@app.route("/reports/attendance")
def report_attendance():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.title,
               COALESCE(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END)*100.0/COUNT(r.registration_id), 0) AS attendance_percentage
        FROM Events e
        LEFT JOIN Registrations r ON e.event_id = r.event_id
        LEFT JOIN Attendance a ON r.student_id = a.student_id AND r.event_id = a.event_id
        GROUP BY e.event_id
    """)
    data = cursor.fetchall()
    conn.close()
    return render_template("report_attendance.html", data=data)

@app.route("/reports/feedback")
def report_feedback():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.title, COALESCE(AVG(f.rating), 0)
        FROM Events e
        LEFT JOIN Feedback f ON e.event_id = f.event_id
        GROUP BY e.event_id
    """)
    data = cursor.fetchall()
    conn.close()
    return render_template("report_feedback.html", data=data)

@app.route("/reports/top_students")
def report_top_students():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name, COUNT(a.attendance_id) AS total_attendance
        FROM Students s
        JOIN Attendance a ON s.student_id = a.student_id
        GROUP BY s.student_id
        ORDER BY total_attendance DESC
        LIMIT 3
    """)
    data = cursor.fetchall()
    conn.close()
    return render_template("report_top_students.html", data=data)

# -------------------------
# Reset Database
# -------------------------
@app.route("/reset_db")
def reset_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()
    flash("Database has been reset!", "success")
    return redirect(url_for("home"))

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()
    else:
        init_db()
    app.run(debug=True)
