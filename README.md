# Intentionally Vulnerable Information Management System

⚠️ **WARNING**: This application contains intentional security vulnerabilities for educational purposes only.

## Project Overview

This project demonstrates four critical web application vulnerabilities from the OWASP Top 10:
1. **SQL Injection (A03:2021)** - Injection - CWE-89
2. **Insecure Direct Object Reference - IDOR (A01:2021)** - Broken Access Control - CWE-639
3. **Exposed Backup Files - A03:2021** - Broken Access Control - CWE-552
4. **Cross-Site Scripting (XSS) - A03:2021** - Injection - CWE-79
## Educational Use Only




## ⚡ Quick Start
 
### Prerequisites
- Python 3.8 or higher
- Flask web framework
 
### Installation
 
1. **Install dependencies:**
```bash
pip install -r requirements.txt
```
 
2. **Initialize the database:**
```bash
python init_db.py
```
 
3. **Run the application:**
```bash
python app.py
```
 
4. **Access the application:**
```
http://localhost:5000
```

---
 
## 📁 Project Structure
 
```
vulnerable_code/
├── app.py                    # Main Flask application (VULNERABLE)
├── init_db.py               # Database initialization script
├── database.db              # SQLite database
├── requirements.txt         # Python dependencies
├── README.md               # This file
│
├── templates/              # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── registration.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── admin_dashboard.html
│   ├── subject.html
│   ├── about.html
│   └── contact.html
│
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   └── assets/
│       ├── MMUMediaLogo.png
│       └── favicon.ico
│
└── backup_files/          # Exposed backup files (INTENTIONAL)
    ├── .env.backup
    ├── .htaccess.bak
```
This application is designed for:
- Learning about web security vulnerabilities
- Understanding exploitation techniques
- Practicing secure coding
- Security training and workshops

## 📚 Documentation
For detailed technical analysis of each vulnerability, see:
- `Comprehensive_Vulnerability_Report.md` - Full vulnerability analysis

## ⚠️ Important Notes
 
### Academic Use Only
- This project is for educational purposes only
- All credentials are fictional
 
### Localhost Only
- Application runs on localhost (127.0.0.1)
- Not accessible from external networks
- Database contains no real user data
 
### Compliance
- Complies with Computer Misuse Act 1990 (academic exception)
- No real personal data (GDPR compliant)
- Ethical disclosure principles followed
 
---

## References

- [OWASP Top 10 Web Application Security Risks](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)

## License

This project is for educational purposes only. Use at your own risk.
