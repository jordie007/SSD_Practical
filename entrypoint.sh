#!/bin/bash

# Configure Git
git config --global user.name "LIM WEI HAO"
git config --global user.email "2402242@sit.singaporetech.edu.sg"

# Initialize git repository if not exists
if [ ! -d "/git-data/.git" ]; then
    mkdir -p /git-data
    cd /git-data
    git init
    echo "Git repository initialized at /git-data"
fi

# Verify certificates exist
echo "Verifying SSL certificates..."
if [ -f "/certs/server.crt" ] && [ -f "/certs/server.key" ]; then
    echo "SSL certificates found:"
    ls -la /certs/
else
    echo "ERROR: SSL certificates not found! Generating new ones..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /certs/server.key \
        -out /certs/server.crt \
        -subj "/C=SG/ST=Singapore/L=Singapore/O=SIT/CN=127.0.0.1"
    echo "Certificates generated."
fi

# Wait for database to be ready using Python
echo "Waiting for database..."
python -c "
import time
import psycopg2
import sys

max_attempts = 30
attempt = 0
while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            host='db',
            database='postgres',
            user='admin',
            password='2402242@sit.singaporetech.edu.sg'
        )
        conn.close()
        print('Database is ready!')
        break
    except Exception:
        attempt += 1
        print(f'Waiting for database... (attempt {attempt}/{max_attempts})')
        time.sleep(2)
else:
    print('Could not connect to database after 30 attempts')
    sys.exit(1)
"

# Initialize database
python -c "
import psycopg2
import os
import csv
import time

try:
    # Wait a bit more for database to be fully ready
    time.sleep(2)
    
    conn = psycopg2.connect(
        host='db',
        database='webapp_db',
        user='admin',
        password='2402242@sit.singaporetech.edu.sg'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create table for student ID
    cur.execute('''
        CREATE TABLE IF NOT EXISTS \"2402242\" (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create table for common passwords if not exists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS common_passwords (
            id SERIAL PRIMARY KEY,
            password VARCHAR(255) UNIQUE NOT NULL
        )
    ''')
    
    # Load common passwords
    cur.execute('SELECT COUNT(*) FROM common_passwords')
    count = cur.fetchone()[0]
    
    if count == 0:
        password_file = '/app/100k-most-used-passwords-NCSC.txt'
        if os.path.exists(password_file):
            print('Loading common passwords...')
            with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                count_loaded = 0
                batch = []
                
                for row in reader:
                    if row and row[0].strip():
                        password = row[0].strip()
                        # Skip if password is too long
                        if len(password) <= 255:
                            batch.append(password)
                            if len(batch) >= 1000:
                                # Insert batch
                                for pwd in batch:
                                    try:
                                        cur.execute(
                                            'INSERT INTO common_passwords (password) VALUES (%s)',
                                            (pwd,)
                                        )
                                        count_loaded += 1
                                    except psycopg2.IntegrityError:
                                        conn.rollback()
                                        continue
                                conn.commit()
                                print(f'Loaded {count_loaded} passwords...')
                                batch = []
                
                # Insert remaining passwords
                for pwd in batch:
                    try:
                        cur.execute(
                            'INSERT INTO common_passwords (password) VALUES (%s)',
                            (pwd,)
                        )
                        count_loaded += 1
                    except psycopg2.IntegrityError:
                        conn.rollback()
                        continue
                conn.commit()
                print(f'Successfully loaded {count_loaded} common passwords!')
        else:
            print(f'WARNING: Password file not found at {password_file}')
    else:
        print(f'Common passwords already loaded ({count} entries)')
    
    cur.close()
    conn.close()
    print('Database initialized successfully!')
except Exception as e:
    print(f'Error initializing database: {e}')
    import traceback
    traceback.print_exc()
"

# Start the Flask application
echo "========================================="
echo "Starting web server..."
echo "HTTPS: https://127.0.0.1/"
echo "HTTP:  http://127.0.0.1:80/"
echo "========================================="
exec python /app/app.py