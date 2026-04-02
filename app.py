from flask import Flask, send_from_directory, jsonify, request
import sqlite3
import os

app = Flask(__name__)

# 🔥 DB 경로 (Render 대응)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

# 이름 순서 및 업무
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

# DB 연결
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 근무표 조회
@app.route("/schedule", methods=["GET"])
def get_schedule():
    dates = request.args.get("dates")
    month = request.args.get("month")
    date = request.args.get("date")

    conn = get_db()
    cur = conn.cursor()

    if dates:
        date_list = dates.split(",")
        placeholders = ",".join("?" * len(date_list))
        cur.execute(
            f"SELECT name, date, status FROM work_schedule WHERE date IN ({placeholders}) ORDER BY name, date",
            date_list
        )
    elif date:
        cur.execute(
            "SELECT name, date, status FROM work_schedule WHERE date=? ORDER BY name",
            (date,)
        )
    elif month:
        cur.execute(
            "SELECT name, date, status FROM work_schedule WHERE date LIKE ? ORDER BY name, date",
            (f"{month}%",)
        )
    else:
        return jsonify({})

    rows = cur.fetchall()
    conn.close()

    schedule = {}
    for row in rows:
        if row["name"] not in schedule:
            schedule[row["name"]] = {}
        schedule[row["name"]][row["date"]] = row["status"]

    ordered_schedule = {}
    for name, _ in people_info:
        ordered_schedule[name] = schedule.get(name, {})

    return jsonify(ordered_schedule)

# 비상 근무 조회
@app.route("/special", methods=["GET"])
def get_special():
    month = request.args.get("month")
    date = request.args.get("date")

    conn = get_db()
    cur = conn.cursor()

    if date:
        cur.execute(
            "SELECT duty, name, date FROM special_duty WHERE date=?",
            (date,)
        )
    elif month:
        cur.execute(
            "SELECT duty, name, date FROM special_duty WHERE date LIKE ?",
            (f"{month}%",)
        )
    else:
        return jsonify({})

    rows = cur.fetchall()
    conn.close()

    special = {}
    for row in rows:
        if row["date"] not in special:
            special[row["date"]] = {}
        if row["duty"] not in special[row["date"]]:
            special[row["date"]][row["duty"]] = []
        special[row["date"]][row["duty"]].append(row["name"])

    return jsonify(special)

# HTML 제공
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "test.html")

# 🔥 로컬 실행용 (Render에서는 gunicorn이 실행함)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)