from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB = "complaints.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    # Complaints table
    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        user_email TEXT,
        complaint TEXT,
        status TEXT DEFAULT 'Pending',
        handled_by TEXT DEFAULT 'Not Assigned - Pending',
        created_at TEXT
    )''')
    # History table - THIS SOLVES YOUR PROBLEM
    c.execute('''CREATE TABLE IF NOT EXISTS remarks_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER,
        remark TEXT,
        status TEXT,
        time TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# --- REGISTER ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)",
                  (data['name'], data['email'], data['password']))
        conn.commit()
        return jsonify({"message": "Registered"}), 200
    except:
        return jsonify({"message": "Email already exists"}), 400
    finally:
        conn.close()

# --- LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (data['email'], data['password']))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"id": user[0], "name": user[1], "email": user[2]}), 200
    return jsonify({"message": "Invalid"}), 401

# --- SUBMIT COMPLAINT ---
@app.route('/complaints', methods=['POST'])
def add_complaint():
    data = request.get_json()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().strftime("%d-%b %Y %I:%M %p")
    c.execute("INSERT INTO complaints (name, email, user_email, complaint, status, handled_by, created_at) VALUES (?,?,?,?,?,?,?)",
              (data.get('name'), data.get('email'), data.get('user_email'), data.get('complaint'), 'Pending', 'Not Assigned - Pending', now))
    complaint_id = c.lastrowid
    # Add first history entry
    c.execute("INSERT INTO remarks_history (complaint_id, remark, status, time) VALUES (?,?,?,?)",
              (complaint_id, "Complaint Registered", "Pending", now))
    conn.commit()
    conn.close()
    return jsonify({"message": "Complaint Added", "id": complaint_id})

# --- GET ALL COMPLAINTS (for admin) ---
@app.route('/complaints', methods=['GET'])
def get_all():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM complaints ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# --- GET MY HISTORY (USER LOGIN HISTORY) - YOUR MAIN REQUIREMENT ---
@app.route('/my_complaints/<email>', methods=['GET'])
def my_complaints(email):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM complaints WHERE user_email=? ORDER BY id DESC", (email,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# --- GET HISTORY TIMELINE FOR ONE COMPLAINT ---
@app.route('/history/<int:complaint_id>', methods=['GET'])
def get_history(complaint_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM remarks_history WHERE complaint_id=? ORDER BY id ASC", (complaint_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)

# --- UPDATE STATUS (YOUR CURRENT FUNCTION - FIXED) ---
@app.route('/complaints/<int:id>', methods=['PUT'])
def update_status(id):
    data = request.get_json()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    now = datetime.now().strftime("%d-%b %Y %I:%M %p")

    if data.get("status") == "Resolved":
        handled = "Resolved by Krishna"
        remark_text = data.get("remark", "Issue Resolved")
    else:
        handled = "Not Assigned - Pending"
        remark_text = data.get("remark", "We are checking your issue")

    c.execute("UPDATE complaints SET status=?, handled_by=? WHERE id=?",
              (data.get("status"), handled, id))

    # SAVE TO HISTORY TABLE - WILL NOT ERASE
    c.execute("INSERT INTO remarks_history (complaint_id, remark, status, time) VALUES (?,?,?,?)",
              (id, remark_text, data.get("status"), now))

    conn.commit()
    conn.close()
    return jsonify({"message": "Status Updated"})

if __name__ == "__main__":
    app.run(port=8000, debug=True)