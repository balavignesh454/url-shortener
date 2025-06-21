import re
from flask import Flask, request, redirect, render_template, flash, url_for
import sqlite3
import hashlib
import base64

app = Flask(__name__)
app.secret_key = "firstpro"  # Required for flash messages


# DB connection function
def get_db_connection():
    conn = sqlite3.connect("urlshortener.db")
    conn.row_factory = sqlite3.Row
    return conn

# Generate short URL
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

# Serve home page
@app.route('/')
def home():
    return render_template('index.html')

# Handle URL shortening
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
      # Basic URL validation using regex
    url_pattern = re.compile(
        r'^(http:\/\/|https:\/\/)?([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}(\/\S*)?$'
    )
    
    if not long_url or not re.match(url_pattern, long_url):
        flash("⚠️ Please enter a valid URL.", "error")
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT short_url, clicks FROM url_mapping WHERE long_url = ?", (long_url,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        short_code = existing_entry['short_url']
        clicks = existing_entry['clicks']
    else:
        short_code = generate_short_url(long_url)
        clicks = 0
        cursor.execute("INSERT INTO url_mapping (long_url, short_url, clicks) VALUES (?, ?, ?)", (long_url, short_code, 0))
        conn.commit()

    conn.close()
    short_url = f"{request.host_url}{short_code}"
    return render_template("index.html", short_url=short_url, long_url=long_url, clicks=clicks)

# Redirect from short URL
@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT long_url FROM url_mapping WHERE short_url = ?", (short_url,))
    entry = cursor.fetchone()

    if entry:
        cursor.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = ?", (short_url,))
        conn.commit()
        conn.close()
        return redirect(entry['long_url'])

    conn.close()
    return "Error: URL NOT FOUND", 404

# Initialize database
def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL,
            short_url TEXT NOT NULL,
            clicks INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Call DB initializer when app starts
initialize_db()

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
