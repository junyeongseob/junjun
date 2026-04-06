from flask import Flask, send_from_directory, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "attendance.db"

people_info = [
    ("남산분소장", "남산분소 업무총괄"),
    ("김재홍", "남산분소 현장관리"),
    ("강이레", "남산분소 현장관리"),
    ("윤동희", "안전관리"),
    ("예린", "공원자원해설"),
    ("권용조", "공원자원해설"),
    ("손영인", "공원자원해설"),
    ("옥희영", "공원자원해설"),
    ("김영호", "공원환경관리"),
    ("서종명", "공원환경관리"),
    ("고현찬", "공원환경관리"),
    ("김복현", "녹색순찰대"),
    ("서진숙", "녹색순찰대"),
    ("정문길", "녹색순찰대"),
    ("김태문", "녹색순찰대"),
    ("최성복", "사회복무요원")
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/schedule")
def schedule():
    dates = request.args.get("dates")
    month = request.args.get("month")
    conn = get_db()
    cur = conn.cursor()

    if dates:
        date_list = dates.split(",")
        placeholders = ",".join("?" * len(date_list))
        cur.execute(
            f"SELECT name, date, status FROM work_schedule WHERE date IN ({placeholders})",
            date_list
        )
    else:
        cur.execute(
            "SELECT name, date, status FROM work_schedule WHERE date LIKE ?",
            (f"{month}%",)
        )

    rows = cur.fetchall()
    conn.close()

    result = {}
    for r in rows:
        result.setdefault(r["name"], {})[r["date"]] = r["status"]

    ordered = {}
    for name, _ in people_info:
        ordered[name] = result.get(name, {})

    return jsonify(ordered)

@app.route("/special")
def special():
    month = request.args.get("month")
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT duty, name, date FROM special_duty WHERE date LIKE ?",
        (f"{month}%",)
    )

    rows = cur.fetchall()
    conn.close()

    result = {}
    for r in rows:
        result.setdefault(r["date"], {}).setdefault(r["duty"], []).append(r["name"])

    return jsonify(result)

# ⭐ 추가된 부분
@app.route("/add_schedule", methods=["POST"])
def add_schedule():
    data = request.json
    name = data["name"]
    date = data["date"]
    status = data["status"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO work_schedule (name, date, status) VALUES (?, ?, ?)",
        (name, date, status)
    )

    conn.commit()
    conn.close()

    return jsonify({"result": "success"})

@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "test.html")

if __name__ == "__main__":
    app.run()
