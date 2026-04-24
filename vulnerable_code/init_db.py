"""
init_db.py — One-time database initialisation script.
Creates all tables and seeds sample data for the student portal.

Usage:
    python init_db.py
"""

import sqlite3
import hashlib

DB_PATH = "database.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def drop_tables(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS event_signups;
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS schedule;
        DROP TABLE IF EXISTS announcements;
        DROP TABLE IF EXISTS comments;
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS users;
    """)


def create_tables(conn):
    conn.executescript("""
        CREATE TABLE users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name     TEXT    NOT NULL,
            last_name      TEXT    NOT NULL,
            email          TEXT    UNIQUE NOT NULL,
            password       TEXT    NOT NULL,
            role           TEXT    NOT NULL DEFAULT 'student'
                           CHECK(role IN ('student', 'tutor', 'admin')),
            office_number  TEXT,
            office_hours   TEXT
        );

        CREATE TABLE courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            code        TEXT    UNIQUE NOT NULL,
            description TEXT,
            tutor_id    INTEGER REFERENCES users(id)
        );

        CREATE TABLE subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            code        TEXT    UNIQUE NOT NULL,
            description TEXT,
            course_id   INTEGER REFERENCES courses(id),
            tutor_id    INTEGER REFERENCES users(id)
        );

        CREATE TABLE enrollments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER REFERENCES users(id),
            course_id   INTEGER REFERENCES courses(id),
            enrolled_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_id)
        );

        CREATE TABLE comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            subject_id INTEGER REFERENCES subjects(id),
            content    TEXT    NOT NULL,
            posted_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER REFERENCES users(id),
            recipient TEXT NOT NULL,
            subject   TEXT NOT NULL,
            message   TEXT NOT NULL,
            sent_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE event_signups (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id),
            event_name   TEXT NOT NULL,
            full_name    TEXT NOT NULL,
            email        TEXT NOT NULL,
            signed_up_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE schedule (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER REFERENCES subjects(id),
            day        TEXT NOT NULL,
            time_slot  TEXT NOT NULL,
            label      TEXT NOT NULL
        );

        CREATE TABLE announcements (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id),
            user_id    INTEGER NOT NULL REFERENCES users(id),
            title      TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            posted_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        );
    """)


def seed_data(conn):
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    users = [
        # (first_name, last_name, email, password, role, office_number, office_hours)
        ("Alice",   "Admin",    "admin@portal.com",       "Admin@1234",   "admin",   None,     None),
        ("Tom",     "Harris",   "tom.harris@portal.com",  "Tutor@1234",   "tutor",   "B2-104", "Mon & Wed 10:00–12:00"),
        ("Sara",    "Malik",    "sara.malik@portal.com",  "Tutor@1234",   "tutor",   "A3-207", "Tue & Thu 14:00–16:00"),
        ("Ben",     "Clarke",   "ben.clarke@portal.com",  "Tutor@1234",   "tutor",   "B3-201", "Tue & Thu 09:00–11:00"),
        ("Priya",   "Patel",    "priya.patel@portal.com", "Tutor@1234",   "tutor",   "C1-305", "Mon & Fri 13:00–15:00"),
        ("David",   "Kim",      "david.kim@portal.com",   "Tutor@1234",   "tutor",   "A2-112", "Wed & Fri 10:00–12:00"),
        ("Laura",   "Hughes",   "laura.hughes@portal.com","Tutor@1234",   "tutor",   "B1-408", "Mon & Thu 15:00–17:00"),
        ("James",   "Carter",   "james@portal.com",       "Student@1234", "student", None,     None),
        ("Emily",   "Brown",    "emily@portal.com",       "Student@1234", "student", None,     None),
        ("Liam",    "Wong",     "liam@portal.com",        "Student@1234", "student", None,     None),
        ("Sophia",  "Nguyen",   "sophia@portal.com",      "Student@1234", "student", None,     None),
    ]

    user_ids = []
    for first_name, last_name, email, password, role, office_number, office_hours in users:
        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password, role, office_number, office_hours) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, hashlib.md5(password.encode()).hexdigest(), role, office_number, office_hours),
        )
        user_ids.append(cur.lastrowid)

    # Convenience aliases
    admin_id  = user_ids[0]
    tutor1_id = user_ids[1]   # Tom Harris      — CS101-S1
    tutor2_id = user_ids[2]   # Sara Malik      — BM101-S1
    tutor3_id = user_ids[3]   # Ben Clarke      — CS101-S2
    tutor4_id = user_ids[4]   # Priya Patel     — CS101-S3
    tutor5_id = user_ids[5]   # David Kim       — BM101-S2
    tutor6_id = user_ids[6]   # Laura Hughes    — BM101-S3
    student_ids = user_ids[7:]  # James, Emily, Liam, Sophia

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    cur.execute(
        "INSERT INTO courses (name, code, description, tutor_id) VALUES (?, ?, ?, ?)",
        (
            "Computer Science",
            "CS101",
            "Foundations of computing, algorithms, and software development.",
            tutor1_id,
        ),
    )
    cs_course_id = cur.lastrowid

    cur.execute(
        "INSERT INTO courses (name, code, description, tutor_id) VALUES (?, ?, ?, ?)",
        (
            "Business Management",
            "BM101",
            "Principles of business strategy, marketing, and operations.",
            tutor2_id,
        ),
    )
    bm_course_id = cur.lastrowid

    # ------------------------------------------------------------------
    # Subjects
    # ------------------------------------------------------------------
    cs_subjects = [
        ("Introduction to Programming", "CS101-S1", "Variables, loops, and functions in Python.", cs_course_id, tutor1_id),
        ("Data Structures",             "CS101-S2", "Arrays, linked lists, trees, and graphs.",   cs_course_id, tutor3_id),
        ("Web Development",             "CS101-S3", "HTML, CSS, JavaScript, and Flask basics.",   cs_course_id, tutor4_id),
    ]

    bm_subjects = [
        ("Marketing Fundamentals",   "BM101-S1", "Consumer behaviour and marketing mix.",       bm_course_id, tutor2_id),
        ("Financial Accounting",     "BM101-S2", "Balance sheets, P&L, and cash flow basics.",  bm_course_id, tutor5_id),
        ("Organisational Behaviour", "BM101-S3", "Leadership, culture, and team dynamics.",      bm_course_id, tutor6_id),
    ]

    subject_ids = {}
    for name, code, desc, course_id, tutor_id in cs_subjects + bm_subjects:
        cur.execute(
            "INSERT INTO subjects (name, code, description, course_id, tutor_id) VALUES (?, ?, ?, ?, ?)",
            (name, code, desc, course_id, tutor_id),
        )
        subject_ids[code] = cur.lastrowid

    # ------------------------------------------------------------------
    # Enrollments
    # ------------------------------------------------------------------
    enrollments = [
        (student_ids[0], cs_course_id),   # James → CS
        (student_ids[1], cs_course_id),   # Emily → CS
        (student_ids[2], bm_course_id),   # Liam  → BM
        (student_ids[3], bm_course_id),   # Sophia→ BM
        (student_ids[1], bm_course_id),   # Emily also in BM
    ]
    for user_id, course_id in enrollments:
        cur.execute(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id),
        )

    # ------------------------------------------------------------------
    # Comments  (content stored raw — intentional for XSS demo)
    # ------------------------------------------------------------------
    comments = [
        (student_ids[0], subject_ids["CS101-S1"], "Great intro! Really enjoyed the Python exercises."),
        (student_ids[1], subject_ids["CS101-S1"], "The loops section was a bit fast, could use more examples."),
        (student_ids[0], subject_ids["CS101-S2"], "Binary trees finally make sense after this lecture."),
        (student_ids[2], subject_ids["BM101-S1"], "The case study on Nike was really insightful!"),
        (student_ids[3], subject_ids["BM101-S2"], "Accounting is tough but the examples help a lot."),
        (student_ids[3], subject_ids["BM101-S3"], "Loved the group discussion on leadership styles."),
    ]
    for user_id, subject_id, content in comments:
        cur.execute(
            "INSERT INTO comments (user_id, subject_id, content) VALUES (?, ?, ?)",
            (user_id, subject_id, content),
        )

    announcements_seed = [
        (subject_ids["CS101-S1"], tutor1_id, "Welcome to Intro Programming", "Please complete the Week 1 reading before Thursday's session."),
        (subject_ids["CS101-S2"], tutor3_id, "Assignment 1 Released", "Assignment 1 on linked lists is now live. Due in two weeks."),
        (subject_ids["BM101-S1"], tutor2_id, "Case Study This Week", "We will be analysing the Unilever sustainability report. Skim it beforehand."),
        (subject_ids["BM101-S2"], tutor5_id, "Mid-term Date Confirmed", "Mid-term assessment is scheduled for Week 8. Review chapters 3-6."),
    ]
    for subject_id, user_id, title, content in announcements_seed:
        cur.execute(
            "INSERT INTO announcements (subject_id, user_id, title, content) VALUES (?, ?, ?, ?)",
            (subject_id, user_id, title, content),
        )

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    schedule_seed = [
        (subject_ids["CS101-S1"], "Mon", "09:00", "Intro Programming"),
        (subject_ids["CS101-S1"], "Wed", "09:00", "Intro Programming"),
        (subject_ids["CS101-S2"], "Tue", "10:00", "Data Structures"),
        (subject_ids["CS101-S2"], "Thu", "11:00", "Data Structures"),
        (subject_ids["CS101-S3"], "Mon", "14:00", "Web Development"),
        (subject_ids["CS101-S3"], "Wed", "14:00", "Web Development"),
        (subject_ids["BM101-S1"], "Tue", "09:00", "Marketing"),
        (subject_ids["BM101-S1"], "Thu", "09:00", "Marketing"),
        (subject_ids["BM101-S2"], "Mon", "10:00", "Financial Acct"),
        (subject_ids["BM101-S2"], "Wed", "10:00", "Financial Acct"),
        (subject_ids["BM101-S3"], "Tue", "13:00", "Org. Behaviour"),
        (subject_ids["BM101-S3"], "Fri", "13:00", "Org. Behaviour"),
    ]
    for subject_id, day, time_slot, label in schedule_seed:
        cur.execute(
            "INSERT INTO schedule (subject_id, day, time_slot, label) VALUES (?, ?, ?, ?)",
            (subject_id, day, time_slot, label),
        )

    conn.commit()


def main():
    print(f"Connecting to {DB_PATH} ...")
    conn = get_connection()

    print("Dropping existing tables ...")
    drop_tables(conn)

    print("Creating tables ...")
    create_tables(conn)

    print("Seeding data ...")
    seed_data(conn)

    conn.close()
    print("Done. Database initialised successfully.")
    print()
    print("Seeded accounts:")
    print("  admin@portal.com         / Admin@1234    (admin)")
    print("  tom.harris@portal.com    / Tutor@1234    (tutor — CS101-S1)")
    print("  sara.malik@portal.com    / Tutor@1234    (tutor — BM101-S1)")
    print("  ben.clarke@portal.com    / Tutor@1234    (tutor — CS101-S2)")
    print("  priya.patel@portal.com   / Tutor@1234    (tutor — CS101-S3)")
    print("  david.kim@portal.com     / Tutor@1234    (tutor — BM101-S2)")
    print("  laura.hughes@portal.com  / Tutor@1234    (tutor — BM101-S3)")
    print("  james@portal.com         / Student@1234  (student)")
    print("  emily@portal.com         / Student@1234  (student)")
    print("  liam@portal.com          / Student@1234  (student)")
    print("  sophia@portal.com        / Student@1234  (student)")


if __name__ == "__main__":
    main()
