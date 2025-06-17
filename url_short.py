from flask import Flask, request, redirect, jsonify, render_template
import mysql.connector
import hashlib
import base64

#starting the Flask App
app =Flask(__name__)

#database congiguration 
DB_CONFIG = {
    'host':'localhost',
    'user':'root',
    'password':'root',
    'database':'test'
}

#db connection function defining
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

#function for generate short url
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

#serve the html form
@app.route('/')
def home():
    return render_template('index.html')

#handle url shortening 

@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    if not long_url:
        flash("⚠️ Please enter a valid URL.", "error")
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT short_url, clicks FROM url_mapping WHERE long_url = %s", (long_url,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        short_code = existing_entry['short_url']
        clicks = existing_entry['clicks']
    else:
        short_code = generate_short_url(long_url)
        clicks = 0
        cursor.execute("INSERT INTO url_mapping (long_url, short_url, clicks) VALUES (%s, %s, %s)", (long_url, short_code, 0))
        conn.commit()

    conn.close()
    short_url = f"{request.host_url}{short_code}"
    return render_template("index.html", short_url=short_url, long_url=long_url, clicks=clicks)


#redirect shortened urls
@app.route('/<short_url>',methods=['GET'])
def redirect_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT long_url FROM url_mapping WHERE short_url = %s",(short_url,))
    entry = cursor.fetchone()
    if  entry:
        cursor.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = %s",(short_url,))
        conn.commit()
        conn.close()
        return redirect(entry['long_url'])
    conn.close()
    return "Error: URL NOT FOUND",404

#run the flask application 

if __name__=='__main__': 
   app.run(debug=True)