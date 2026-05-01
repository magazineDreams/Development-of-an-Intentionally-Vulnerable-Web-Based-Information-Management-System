"""
Information Management System - Secured Version
Security fixes applied:
1. SQL Injection mitigated with parameterised queries
2. Exposed file-serving route removed
3. Cross-Site Scripting (XSS) mitigated with input escaping
4. Insecure Direct Object Reference (IDOR) mitigated with access control
5. Password hashing improved (werkzeug PBKDF2 + MD5 fallback for legacy accounts)
6. Session security hardened (HTTPONLY, SAMESITE; SECURE requires HTTPS)
7. Debug mode disabled, host restricted to localhost
8. Weak secret key replaced with environment-variable-driven secret
"""

from flask import (Flask, render_template, request, redirect,
                   session, flash, url_for)
import sqlite3
import hashlib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SECURE: Strong secret key from environment; dev fallback only
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-production")

# SECURE: Cookie hardening
app.config['SESSION_COOKIE_HTTPONLY'] = True
# Set SESSION_COOKIE_SECURE to True in production (requires HTTPS)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DB_PATH = os.path.join(BASE_DIR, "database.db")


# ── Database helpers ─────────────────────────────────────────────────────────

def ensure_extra_tables():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER REFERENCES users(id),
            recipient TEXT NOT NULL,
            subject   TEXT NOT NULL,
            message   TEXT NOT NULL,
            sent_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS event_signups (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id),
            event_name   TEXT NOT NULL,
            full_name    TEXT NOT NULL,
            email        TEXT NOT NULL,
            signed_up_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS schedule (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER REFERENCES subjects(id),
            day        TEXT NOT NULL,
            time_slot  TEXT NOT NULL,
            label      TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def seed_schedule_if_empty():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM schedule")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, code FROM subjects")
        subjects = {row[1]: row[0] for row in cursor.fetchall()}
        entries = []
        if "CS101-S1" in subjects:
            entries += [(subjects["CS101-S1"], "Mon", "09:00", "Intro Programming"),
                        (subjects["CS101-S1"], "Wed", "09:00", "Intro Programming")]
        if "CS101-S2" in subjects:
            entries += [(subjects["CS101-S2"], "Tue", "10:00", "Data Structures"),
                        (subjects["CS101-S2"], "Thu", "11:00", "Data Structures")]
        if "CS101-S3" in subjects:
            entries += [(subjects["CS101-S3"], "Mon", "14:00", "Web Development"),
                        (subjects["CS101-S3"], "Wed", "14:00", "Web Development")]
        if "BM101-S1" in subjects:
            entries += [(subjects["BM101-S1"], "Tue", "09:00", "Marketing"),
                        (subjects["BM101-S1"], "Thu", "09:00", "Marketing")]
        if "BM101-S2" in subjects:
            entries += [(subjects["BM101-S2"], "Mon", "10:00", "Financial Acct"),
                        (subjects["BM101-S2"], "Wed", "10:00", "Financial Acct")]
        if "BM101-S3" in subjects:
            entries += [(subjects["BM101-S3"], "Tue", "13:00", "Org. Behaviour"),
                        (subjects["BM101-S3"], "Fri", "13:00", "Org. Behaviour")]
        for subject_id, day, time_slot, label in entries:
            conn.execute(
                "INSERT INTO schedule (subject_id, day, time_slot, label) VALUES (?, ?, ?, ?)",
                (subject_id, day, time_slot, label)
            )
        conn.commit()
    conn.close()


ensure_extra_tables()
seed_schedule_if_empty()


# ── Access-control helpers ────────────────────────────────────────────────────

def admin_required():
    """Returns a redirect if the current user is not an admin, else None."""
    if "user_id" not in session:
        return redirect("/login")
    if session.get("user_role") != "admin":
        flash("Access denied – admins only.", "danger")
        return redirect("/dashboard")
    return None


# ── Public routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


# ── Authentication ────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # SECURE: strip whitespace; do NOT embed into SQL string
        email    = request.form["email"].strip()
        password = request.form["password"]

        try:
            conn   = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # SECURE: parameterised query — no SQL injection possible
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user is None:
                flash("Email not found.", "warning")
                return render_template("login.html")

            # user columns: id(0) first_name(1) last_name(2) email(3) password(4) role(5)
            stored_password = user[4]
            password_ok     = False

            # SECURE: support both new strong hashes and legacy MD5 demo accounts
            if stored_password and stored_password.startswith(("pbkdf2:", "scrypt:")):
                password_ok = check_password_hash(stored_password, password)
            else:
                password_ok = (stored_password ==
                               hashlib.md5(password.encode()).hexdigest())

            if password_ok:
                session["user_id"]        = user[0]
                session["user_name"]      = user[1]
                session["user_last_name"] = user[2]
                session["user_email"]     = user[3]
                session["user_role"]      = user[5]
                # SECURE: password hash is NOT stored in session
                return redirect("/dashboard")
            else:
                flash("Incorrect password.", "warning")

        except sqlite3.Error as e:
            flash("A database error occurred. Please try again.", "danger")

    return render_template("login.html")


@app.route('/registration', methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        firstname        = request.form["firstname"]
        lastname         = request.form["lastname"]
        email            = request.form["email"]
        password         = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("registration"))

        try:
            conn   = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # SECURE: parameterised check for duplicate email
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                flash("Email already registered.", "warning")
                return redirect(url_for("registration"))

            # SECURE: strong salted hash instead of MD5
            hashed_password = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                (firstname, lastname, email, hashed_password)
            )
            conn.commit()
            conn.close()

            flash("Registered successfully! Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.Error:
            flash("A database error occurred.", "danger")
            return redirect(url_for("registration"))

    return render_template("registration.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    # Admins go straight to the admin panel
    if session.get("user_role") == "admin":
        return redirect(url_for("admin_dashboard"))

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Tutor dashboard ──
    if session.get("user_role") == "tutor":
        uid = session["user_id"]

        cursor.execute("SELECT COUNT(*) FROM subjects WHERE tutor_id = ?", (uid,))
        subjects_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT e.user_id)
            FROM enrollments e
            JOIN subjects s ON s.course_id = e.course_id
            WHERE s.tutor_id = ?
        """, (uid,))
        students_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM announcements WHERE user_id = ?", (uid,))
        announcements_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM comments
            WHERE subject_id IN (SELECT id FROM subjects WHERE tutor_id = ?)
        """, (uid,))
        comments_count = cursor.fetchone()[0]

        stats = {
            "subjects":      subjects_count,
            "students":      students_count,
            "announcements": announcements_count,
            "comments":      comments_count,
        }

        cursor.execute("""
            SELECT DISTINCT u.first_name, u.last_name, u.email, c.name, c.code
            FROM users u
            JOIN enrollments e ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            JOIN subjects s ON s.course_id = c.id
            WHERE s.tutor_id = ? AND u.role = 'student'
            ORDER BY u.last_name, u.first_name
        """, (uid,))
        students = [
            {"first_name": r[0], "last_name": r[1], "email": r[2],
             "course_name": r[3], "course_code": r[4]}
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT s.id, s.name, s.code, c.name
            FROM subjects s
            JOIN courses c ON s.course_id = c.id
            WHERE s.tutor_id = ?
            ORDER BY s.name
        """, (uid,))
        tutor_subjects = [
            {"id": r[0], "name": r[1], "code": r[2], "course_name": r[3]}
            for r in cursor.fetchall()
        ]

        cursor.execute(
            "SELECT office_number, office_hours FROM users WHERE id = ?", (uid,)
        )
        row          = cursor.fetchone()
        tutor_office = {"office_number": row[0] or "", "office_hours": row[1] or ""}

        conn.close()
        return render_template("dashboard.html", stats=stats, students=students,
                               tutor_office=tutor_office, tutor_subjects=tutor_subjects)

    # ── Student dashboard ──
    cursor.execute("""
        SELECT c.id, c.name, c.code, s.id, s.name, s.code,
               u.id, u.first_name, u.last_name, u.email, u.office_number, u.office_hours
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN subjects s ON s.course_id = c.id
        LEFT JOIN users u ON s.tutor_id = u.id
        WHERE e.user_id = ?
        ORDER BY c.id, s.id
    """, (session["user_id"],))
    rows = cursor.fetchall()

    cursor.execute("""
        SELECT sc.day, sc.time_slot, sc.label
        FROM schedule sc
        JOIN subjects s ON sc.subject_id = s.id
        JOIN courses c ON s.course_id = c.id
        JOIN enrollments e ON e.course_id = c.id
        WHERE e.user_id = ?
    """, (session["user_id"],))
    schedule = {(r[0], r[1]): r[2] for r in cursor.fetchall()}
    conn.close()

    courses      = {}
    tutors_seen  = set()
    tutors       = []
    for (c_id, c_name, c_code, s_id, s_name, s_code,
         t_id, t_first, t_last, t_email, t_office, t_hours) in rows:
        if c_id not in courses:
            courses[c_id] = {"id": c_id, "name": c_name, "code": c_code, "subjects": []}
        courses[c_id]["subjects"].append({"id": s_id, "name": s_name, "code": s_code})
        if t_id and t_id not in tutors_seen:
            tutors_seen.add(t_id)
            tutors.append({
                "name":    f"{t_first} {t_last}",
                "email":   t_email,
                "office":  t_office or "—",
                "hours":   t_hours  or "—",
                "subject": s_name,
            })

    return render_template("dashboard.html",
                           courses=list(courses.values()),
                           tutors=tutors,
                           schedule=schedule)


# ── Admin dashboard ───────────────────────────────────────────────────────────

@app.route("/admin_dashboard")
def admin_dashboard():
    guard = admin_required()
    if guard:
        return guard

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'tutor'")
    total_tutors = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM courses")
    total_courses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM comments")
    total_comments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM announcements")
    total_announcements = cursor.fetchone()[0]

    cursor.execute(
        "SELECT id, first_name, last_name, email, role FROM users ORDER BY role, last_name"
    )
    all_users = [
        {"id": r[0], "first_name": r[1], "last_name": r[2],
         "name": f"{r[1]} {r[2]}", "email": r[3], "role": r[4]}
        for r in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT c.id, c.name, c.code, c.description,
               COALESCE(u.first_name || ' ' || u.last_name, '—') AS tutor_name,
               COUNT(DISTINCT e.user_id) AS enrolled
        FROM courses c
        LEFT JOIN users u ON c.tutor_id = u.id
        LEFT JOIN enrollments e ON e.course_id = c.id
        GROUP BY c.id ORDER BY c.name
    """)
    all_courses = [
        {"id": r[0], "name": r[1], "code": r[2], "description": r[3],
         "tutor_name": r[4], "enrolled": r[5]}
        for r in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT cm.id, cm.content, cm.posted_at,
               u.first_name || ' ' || u.last_name AS author,
               s.name AS subject_name
        FROM comments cm
        JOIN users u ON cm.user_id = u.id
        JOIN subjects s ON cm.subject_id = s.id
        ORDER BY cm.posted_at DESC
    """)
    all_comments = [
        {"id": r[0], "content": r[1], "posted_at": r[2],
         "author": r[3], "subject_name": r[4]}
        for r in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT a.id, a.title, a.content, a.posted_at,
               u.first_name || ' ' || u.last_name AS author,
               s.name AS subject_name
        FROM announcements a
        JOIN users u ON a.user_id = u.id
        JOIN subjects s ON a.subject_id = s.id
        ORDER BY a.posted_at DESC
    """)
    all_announcements = [
        {"id": r[0], "title": r[1], "content": r[2], "posted_at": r[3],
         "author": r[4], "subject_name": r[5]}
        for r in cursor.fetchall()
    ]

    conn.close()

    stats = {
        "students":      total_students,
        "tutors":        total_tutors,
        "courses":       total_courses,
        "comments":      total_comments,
        "announcements": total_announcements,
    }

    return render_template("admin_dashboard.html",
                           stats=stats,
                           all_users=all_users,
                           all_courses=all_courses,
                           all_comments=all_comments,
                           all_announcements=all_announcements)


# ── Admin: User CRUD ──────────────────────────────────────────────────────────

@app.route("/admin/user/<int:user_id>/edit", methods=["POST"])
def admin_edit_user(user_id):
    guard = admin_required()
    if guard:
        return guard
    first_name = request.form.get("first_name", "").strip()
    last_name  = request.form.get("last_name",  "").strip()
    email      = request.form.get("email",      "").strip()
    role       = request.form.get("role",       "").strip()
    if first_name and last_name and email and role in ("student", "tutor", "admin"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE users SET first_name=?, last_name=?, email=?, role=? WHERE id=?",
            (first_name, last_name, email, role, user_id)
        )
        conn.commit()
        conn.close()
        flash("User updated.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-users")


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    guard = admin_required()
    if guard:
        return guard
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] != "admin":
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        flash("User deleted.", "success")
    else:
        flash("Cannot delete an admin account.", "danger")
    conn.close()
    return redirect(url_for("admin_dashboard") + "#tab-users")


# ── Admin: Course CRUD ────────────────────────────────────────────────────────

@app.route("/admin/course/<int:course_id>/edit", methods=["POST"])
def admin_edit_course(course_id):
    guard = admin_required()
    if guard:
        return guard
    name        = request.form.get("name",        "").strip()
    code        = request.form.get("code",        "").strip()
    description = request.form.get("description", "").strip()
    if name and code:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE courses SET name=?, code=?, description=? WHERE id=?",
            (name, code, description, course_id)
        )
        conn.commit()
        conn.close()
        flash("Course updated.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-courses")


@app.route("/admin/course/<int:course_id>/delete", methods=["POST"])
def admin_delete_course(course_id):
    guard = admin_required()
    if guard:
        return guard
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course deleted.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-courses")


# ── Admin: Comment CRUD ───────────────────────────────────────────────────────

@app.route("/admin/comment/<int:comment_id>/edit", methods=["POST"])
def admin_edit_comment(comment_id):
    guard = admin_required()
    if guard:
        return guard
    # SECURE: escape admin-supplied content too
    content = str(escape(request.form.get("content", "").strip()))
    if content:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE comments SET content=? WHERE id=?", (content, comment_id))
        conn.commit()
        conn.close()
        flash("Comment updated.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-comments")


@app.route("/admin/comment/<int:comment_id>/delete", methods=["POST"])
def admin_delete_comment(comment_id):
    guard = admin_required()
    if guard:
        return guard
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    conn.close()
    flash("Comment deleted.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-comments")


# ── Admin: Announcement CRUD ──────────────────────────────────────────────────

@app.route("/admin/announcement/<int:ann_id>/edit", methods=["POST"])
def admin_edit_announcement(ann_id):
    guard = admin_required()
    if guard:
        return guard
    title   = str(escape(request.form.get("title",   "").strip()))
    content = str(escape(request.form.get("content", "").strip()))
    if title and content:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE announcements SET title=?, content=? WHERE id=?",
            (title, content, ann_id)
        )
        conn.commit()
        conn.close()
        flash("Announcement updated.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-announcements")


@app.route("/admin/announcement/<int:ann_id>/delete", methods=["POST"])
def admin_delete_announcement(ann_id):
    guard = admin_required()
    if guard:
        return guard
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM announcements WHERE id=?", (ann_id,))
    conn.commit()
    conn.close()
    flash("Announcement deleted.", "success")
    return redirect(url_for("admin_dashboard") + "#tab-announcements")


# ── Contact ───────────────────────────────────────────────────────────────────

@app.route('/contact')
def contact():
    if 'user_id' not in session:
        return redirect('/login')

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if session.get('user_role') == 'tutor':
        cursor.execute("""
            SELECT DISTINCT u.first_name, u.last_name, u.email, c.name, c.code
            FROM users u
            JOIN enrollments e ON e.user_id = u.id
            JOIN courses c ON e.course_id = c.id
            JOIN subjects s ON s.course_id = c.id
            WHERE s.tutor_id = ? AND u.role = 'student'
            ORDER BY u.last_name, u.first_name
        """, (session['user_id'],))
        students = [
            {'first_name': r[0], 'last_name': r[1], 'email': r[2],
             'course_name': r[3], 'course_code': r[4]}
            for r in cursor.fetchall()
        ]
        conn.close()
        return render_template('contact.html', students=students)
    else:
        cursor.execute("""
            SELECT u.first_name, u.last_name, u.email,
                   u.office_number, u.office_hours,
                   GROUP_CONCAT(s.name, ', ') AS subjects
            FROM users u
            JOIN subjects s ON s.tutor_id = u.id
            WHERE u.role = 'tutor'
            GROUP BY u.id
            ORDER BY u.last_name
        """)
        tutors = [
            {'name': f"{r[0]} {r[1]}", 'email': r[2] or '',
             'office_number': r[3] or '—', 'office_hours': r[4] or '—',
             'subjects': r[5] or '—'}
            for r in cursor.fetchall()
        ]
        conn.close()
        return render_template('contact.html', tutors=tutors)


@app.route("/contact/send", methods=["POST"])
def contact_send():
    if "user_id" not in session:
        return redirect("/login")
    # SECURE: escape all free-text fields
    recipient    = str(escape(request.form.get("recipient",    "").strip()))
    subject_line = str(escape(request.form.get("subject",      "").strip()))
    message      = str(escape(request.form.get("message",      "").strip()))
    if recipient and subject_line and message:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO messages (sender_id, recipient, subject, message) VALUES (?, ?, ?, ?)",
            (session["user_id"], recipient, subject_line, message)
        )
        conn.commit()
        conn.close()
        flash("Message sent successfully!", "success")
    else:
        flash("Please fill in all fields.", "warning")
    return redirect(url_for("contact"))


# ── Events ────────────────────────────────────────────────────────────────────

@app.route("/firstPage")
def firstPage():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("FirstPage.html")


@app.route("/events/signup", methods=["POST"])
def events_signup():
    if "user_id" not in session:
        return redirect("/login")
    event_name = str(escape(request.form.get("event_name", "").strip()))
    full_name  = str(escape(request.form.get("full_name",  "").strip()))
    email      = str(escape(request.form.get("email",      "").strip()))
    if event_name and full_name and email:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM event_signups WHERE user_id=? AND event_name=?",
            (session["user_id"], event_name)
        )
        if cursor.fetchone():
            conn.close()
            flash(f"You are already signed up for '{event_name}'.", "info")
        else:
            conn.execute(
                "INSERT INTO event_signups (user_id, event_name, full_name, email) "
                "VALUES (?, ?, ?, ?)",
                (session["user_id"], event_name, full_name, email)
            )
            conn.commit()
            conn.close()
            flash(f"Successfully registered for '{event_name}'!", "success")
    else:
        flash("Please fill in all fields.", "warning")
    return redirect(url_for("firstPage"))


# ── Profile ───────────────────────────────────────────────────────────────────

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    # SECURE: normal users can only view their own profile.
    # Admins may view any profile via ?user_id=.
    user_id           = session["user_id"]
    requested_user_id = request.args.get("user_id")

    if requested_user_id:
        if session.get("user_role") == "admin":
            user_id = requested_user_id
        elif str(requested_user_id) != str(session["user_id"]):
            # SECURE: block IDOR — redirect to own profile silently
            flash("Access denied.", "danger")
            return redirect("/profile")

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT first_name, last_name, email, role FROM users WHERE id = ?",
        (user_id,)
    )
    user_data = cursor.fetchone()

    cursor.execute("""
        SELECT c.name, c.code
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.user_id = ?
    """, (user_id,))
    courses = [{"name": r[0], "code": r[1]} for r in cursor.fetchall()]
    conn.close()

    # Build the dict that profile.html expects
    user = {
        "first_name": user_data[0],
        "last_name":  user_data[1],
        "email":      user_data[2],
        "role":       user_data[3],
    } if user_data else None

    return render_template("profile.html",
                           user=user,
                           courses=courses,
                           current_user_id=int(user_id),
                           logged_in_user_id=session["user_id"])


@app.route("/profile/edit", methods=["POST"])
def profile_edit():
    if "user_id" not in session:
        return redirect("/login")
    first_name = str(escape(request.form.get("first_name", "").strip()))
    last_name  = str(escape(request.form.get("last_name",  "").strip()))
    email      = str(escape(request.form.get("email",      "").strip()))
    if first_name and last_name and email:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE users SET first_name=?, last_name=?, email=? WHERE id=?",
            (first_name, last_name, email, session["user_id"])
        )
        conn.commit()
        conn.close()
        # Keep session in sync
        session["user_name"]      = first_name
        session["user_last_name"] = last_name
        session["user_email"]     = email
        flash("Profile updated successfully.", "success")
    else:
        flash("All fields are required.", "warning")
    return redirect(url_for("profile"))


@app.route("/profile/office", methods=["POST"])
def update_office():
    if "user_id" not in session:
        return redirect("/login")
    if session.get("user_role") not in ("tutor", "admin"):
        flash("Not authorised.", "danger")
        return redirect("/dashboard")
    office_number = request.form.get("office_number", "").strip()
    office_hours  = request.form.get("office_hours",  "").strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET office_number=?, office_hours=? WHERE id=?",
        (office_number, office_hours, session["user_id"])
    )
    conn.commit()
    conn.close()
    flash("Office info updated.", "success")
    return redirect("/dashboard")


# ── Subjects ──────────────────────────────────────────────────────────────────

@app.route("/subject/<int:subject_id>")
def subject(subject_id):
    if "user_id" not in session:
        return redirect("/login")

    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.name, s.code, s.description, c.name,
               u.first_name, u.last_name, u.email, u.office_number, u.office_hours
        FROM subjects s
        JOIN courses c ON s.course_id = c.id
        LEFT JOIN users u ON s.tutor_id = u.id
        WHERE s.id = ?
    """, (subject_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Subject not found", 404

    subject_data = {
        "id":                 row[0],
        "name":               row[1],
        "code":               row[2],
        "description":        row[3],
        "course_name":        row[4],
        "tutor_name":         f"{row[5]} {row[6]}" if row[5] else "Not assigned",
        "tutor_email":        row[7] or "",
        "tutor_office_number": row[8] or "—",
        "tutor_office_hours":  row[9] or "—",
    }

    cursor.execute("""
        SELECT cm.id, u.first_name, u.last_name, cm.content, cm.posted_at
        FROM comments cm
        JOIN users u ON cm.user_id = u.id
        WHERE cm.subject_id = ?
        ORDER BY cm.posted_at
    """, (subject_id,))
    comments = [
        {"id": r[0], "author": f"{r[1]} {r[2]}", "content": r[3], "posted_at": r[4]}
        for r in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT a.id, u.first_name, u.last_name, a.title, a.content, a.posted_at
        FROM announcements a
        JOIN users u ON a.user_id = u.id
        WHERE a.subject_id = ?
        ORDER BY a.posted_at DESC
    """, (subject_id,))
    announcements = [
        {"id": r[0], "author": f"{r[1]} {r[2]}", "title": r[3],
         "content": r[4], "posted_at": r[5]}
        for r in cursor.fetchall()
    ]
    conn.close()

    return render_template("subject.html",
                           subject=subject_data,
                           comments=comments,
                           announcements=announcements)


@app.route("/subject/<int:subject_id>/comment", methods=["POST"])
def add_comment(subject_id):
    if "user_id" not in session:
        return redirect("/login")

    # SECURE: escape user input to prevent XSS
    content = str(escape(request.form["content"].strip()))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (user_id, subject_id, content) VALUES (?, ?, ?)",
        (session["user_id"], subject_id, content)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("subject", subject_id=subject_id))


@app.route("/subject/<int:subject_id>/announcement", methods=["POST"])
def post_announcement(subject_id):
    if "user_id" not in session:
        return redirect("/login")
    if session.get("user_role") not in ("tutor", "admin"):
        flash("Only tutors and admins can post announcements.", "danger")
        return redirect(url_for("subject", subject_id=subject_id))

    # SECURE: escape both fields
    title   = str(escape(request.form.get("title",   "").strip()))
    content = str(escape(request.form.get("content", "").strip()))

    if not title or not content:
        flash("Title and content are required.", "warning")
        return redirect(url_for("subject", subject_id=subject_id))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO announcements (subject_id, user_id, title, content) VALUES (?, ?, ?, ?)",
        (subject_id, session["user_id"], title, content)
    )
    conn.commit()
    conn.close()
    flash("Announcement posted.", "success")
    return redirect(url_for("subject", subject_id=subject_id))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # SECURE: debug=False, bound to localhost only
    app.run(debug=False, host='127.0.0.1', port=5000)
