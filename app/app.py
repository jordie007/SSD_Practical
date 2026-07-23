from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import psycopg2.extras
import re
import hashlib
import os
from datetime import datetime
import subprocess

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
DB_CONFIG = {
    'host': 'db',
    'database': 'webapp_db',
    'user': 'admin',
    'password': '2402242@sit.singaporetech.edu.sg'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def is_password_common(password):
    """Check if password is in common passwords list"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM common_passwords WHERE password = %s', (password,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error checking common password: {e}")
        return False

def validate_password_frontend(password):
    """
    Frontend validation based on OWASP Top 10 Proactive Controls C7
    Level 1: Passwords - Password Requirements
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if len(password) > 64:
        return False, "Password must not exceed 64 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    if is_password_common(password):
        return False, "Password is too common and easily guessable"
    return True, "Password is valid"

def validate_password_backend(password):
    """
    Backend validation based on OWASP Top 10 Proactive Controls C7
    Level 1: Passwords - Password Requirements
    """
    # Hash password for secure storage
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    # Same validation as frontend (defense in depth)
    if len(password) < 8:
        return False, "Password must be at least 8 characters long", hashed
    if len(password) > 64:
        return False, "Password must not exceed 64 characters", hashed
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter", hashed
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter", hashed
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number", hashed
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character", hashed
    if is_password_common(password):
        return False, "Password is too common and easily guessable", hashed
    return True, "Password is valid", hashed

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return render_template('index.html', error="Username and password are required")
    
    # Validate password
    is_valid, message = validate_password_frontend(password)
    
    if not is_valid:
        return render_template('index.html', error=message)
    
    # Backend validation
    is_valid_backend, message_backend, hashed_pw = validate_password_backend(password)
    
    if not is_valid_backend:
        return render_template('index.html', error=message_backend)
    
    # Store user in database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO "2402242" (username, created_at) VALUES (%s, %s)',
            (username, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.IntegrityError:
        return render_template('index.html', error="Username already exists. Please choose another.")
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('index.html', error="An error occurred. Please try again.")
    
    return render_template('welcome.html', username=username, password=password)

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'GET':
        return render_template('create_account.html')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if not username or not password:
        return render_template('create_account.html', error="All fields are required")
    
    # Validate password
    is_valid, message = validate_password_frontend(password)
    
    if not is_valid:
        return render_template('create_account.html', error=message)
    
    # Backend validation
    is_valid_backend, message_backend, hashed_pw = validate_password_backend(password)
    
    if not is_valid_backend:
        return render_template('create_account.html', error=message_backend)
    
    # Store user in database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO "2402242" (username, created_at) VALUES (%s, %s)',
            (username, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
    except psycopg2.IntegrityError:
        return render_template('create_account.html', error="Username already exists. Please choose another.")
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('create_account.html', error="An error occurred. Please try again.")
    
    return render_template('welcome.html', username=username, password=password)

@app.route('/logout')
def logout():
    return redirect(url_for('home'))

@app.route('/git/commit')
def git_commit():
    """Helper endpoint to commit code to git"""
    try:
        # Change to git directory
        os.chdir('/git-data')
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        
        # Commit with message
        commit_msg = f"Auto-commit {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
        
        return jsonify({'status': 'success', 'message': 'Code committed to git'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Check if certificates exist
    cert_file = '/certs/server.crt'
    key_file = '/certs/server.key'
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Using SSL certificates for HTTPS")
        context = (cert_file, key_file)
        app.run(host='0.0.0.0', port=443, debug=False, ssl_context=context)
    else:
        print("WARNING: SSL certificates not found, running on HTTP")
        print(f"Cert file: {cert_file}, exists: {os.path.exists(cert_file)}")
        print(f"Key file: {key_file}, exists: {os.path.exists(key_file)}")
        app.run(host='0.0.0.0', port=80, debug=False)