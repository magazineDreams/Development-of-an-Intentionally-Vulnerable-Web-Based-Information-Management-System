# Intentionally Vulnerable Information Management System

⚠️ **WARNING**: This application contains intentional security vulnerabilities for educational purposes only.

---

## Project Overview

This project demonstrates four critical web application vulnerabilities from the OWASP Top 10:

| # | Vulnerability | OWASP Category | CWE |
|---|---|---|---|
| 1 | SQL Injection | A03:2021 - Injection | CWE-89 |
| 2 | Insecure Direct Object Reference (IDOR) | A01:2021 - Broken Access Control | CWE-639 |
| 3 | Cross-Site Scripting (XSS) | A03:2021 - Injection | CWE-79 |
| 4 | Exposed Backup Files | A05:2021 - Security Misconfiguration | CWE-552 |

---

## Repository Structure

```
repo/
├── .gitignore
├── README.md
├── Comprehensive_Vulnerability_Report.md
│
├── vulnerable_code/               # Intentionally vulnerable version
│   ├── app.py                     # Main Flask application (VULNERABLE)
│   ├── init_db.py                 # Database initialisation script
│   ├── requirements.txt           # Python dependencies
│   ├── .env.backup                # Exposed backup file (intentional demo)
│   ├── .htaccess_bak              # Exposed backup file (intentional demo)
│   ├── templates/                 # HTML templates
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── registration.html
│   │   ├── Dashboard.html
│   │   ├── profile.html
│   │   ├── admin_dashboard.html
│   │   ├── subject.html
│   │   ├── about.html
│   │   ├── contact.html
│   │   └── FirstPage.html
│   └── static/
│       ├── assets/
│       │   ├── MMUMediaLogo.png
│       │   ├── button-drop-down.jpeg
│       │   └── favicon.ico
│       └── css/
│           └── style.css
│
└── secure_code/                   # Remediated secure version
    ├── app.py                     # Main Flask application (SECURE)
    ├── init_db.py                 # Database initialisation script
    ├── requirements.txt           # Python dependencies
    ├── templates/                 # HTML templates with XSS fix
    │   ├── index.html
    │   ├── login.html
    │   ├── registration.html
    │   ├── Dashboard.html
    │   ├── profile.html
    │   ├── admin_dashboard.html
    │   ├── subject.html
    │   ├── about.html
    │   ├── contact.html
    │   └── FirstPage.html
    └── static/
        ├── assets/
        │   ├── MMUMediaLogo.png
        │   ├── button-drop-down.jpeg
        │   └── favicon.ico
        └── css/
            └── style.css
```
---

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip
- Git

### Step 1 — Clone the Repository

```bash
git clone https://github.com/magazineDreams/Development-of-an-Intentionally-Vulnerable-Web-Based-Information-Management-System.git
cd Development-of-an-Intentionally-Vulnerable-Web-Based-Information-Management-System
```

### Step 2 — Running the Vulnerable Version

```bash
cd vulnerable_code
pip install -r requirements.txt
python init_db.py
python app.py
```
Access at: **http://localhost:5001**

### Step 3 — Running the Secure Version

Open a new terminal in the same repo folder:

```bash
cd secure_code
pip install -r requirements.txt
python init_db.py
python app.py
```
Access at: **http://localhost:5000**

---

## Test Accounts

| Role | Email | Password |
|---|---|---|
| Student | sophia@portal.com | Student@1234 |
| Tutor | tutor@portal.com | Tutor@1234 |
| Admin | admin@portal.com | Admin@1234 |

---

## Security Fixes Applied (secure_code)

| Vulnerability | Fix Applied |
|---|---|
| SQL Injection | Parameterised queries throughout |
| IDOR | Server-side session-based access control on profile route |
| XSS | Input escaped with `markupsafe.escape()`, `\| safe` removed from templates |
| Exposed Backup Files | Catch-all file-serving route removed entirely |
| Weak Password Hashing | MD5 replaced with PBKDF2 via Werkzeug |
| Session Misconfiguration | `HTTPONLY`, `SAMESITE` enabled; password hash removed from session |
| Debug Mode | `debug=False`, server bound to `127.0.0.1` |

---

## Important Notes

- All credentials and data are **fictional** — no real personal data is used
- The vulnerable version is for **demonstration purposes only**

---

## Documentation

For full technical analysis of each vulnerability including exploitation steps and remediation:
- `Comprehensive_Vulnerability_Report.md`

---

## References

- [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

*Manchester Metropolitan University — Department of Computing and Mathematics*  
*6G5Z0023 Thematic Project — Team OWASP*  
*Mohammed · Hira · Abdulla · Summar · Al Muhanad · Sabina · Jhanzaib*
