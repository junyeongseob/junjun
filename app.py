from flask import Flask, send_from_directory, jsonify, request
import sqlite3
import os
from openpyxl import load_workbook
from datetime import datetime

app = Flask(__name__)

# 🔥 DB 경로 안정화 (Render 대응)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

# 🔥 DB 초기화 (테이블 없으면 자동 생성)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 근무표 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS work_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        status TEXT
    )
    """)

    # 비상근무 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS special_duty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duty TEXT,
        name TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 🔥 서버 시작 시 DB 초기화 실행
init_db()

# 근무표 조회
@app.route("/schedule")
def get_schedule():
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
    elif month:
        cur.execute(
            "SELECT name, date, status FROM work_schedule WHERE date LIKE ?",
            (f"{month}%",)
        )
    else:
        return jsonify({})

    rows = cur.fetchall()
    conn.close()

    result = {}
    for r in rows:
        result.setdefault(r["name"], {})[r["date"]] = r["status"]

    return jsonify(result)

# 비상근무 조회
@app.route("/special")
def get_special():
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

# 근무 추가
@app.route("/add_schedule", methods=["POST"])
def add_schedule():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO work_schedule (name, date, status) VALUES (?, ?, ?)",
        (data["name"], data["date"], data["status"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result": "ok"})

# 근무 일괄 추가
@app.route("/add_schedule_bulk", methods=["POST"])
def add_schedule_bulk():
    data = request.json["data"]

    conn = get_db()
    cur = conn.cursor()

    for line in data:
        if "\t" in line:
            parts = line.split("\t")
        else:
            parts = line.split(",")

        if len(parts) != 3:
            continue

        name, date, status = [p.strip() for p in parts]

        cur.execute(
            "INSERT INTO work_schedule (name, date, status) VALUES (?, ?, ?)",
            (name, date, status)
        )

    conn.commit()
    conn.close()

    return jsonify({"result": "ok"})

# 비상근무 추가
@app.route("/add_special", methods=["POST"])
def add_special():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO special_duty (duty, name, date) VALUES (?, ?, ?)",
        (data["duty"], data["name"], data["date"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result": "ok"})

# 근무 삭제
@app.route("/delete_schedule", methods=["POST"])
def delete_schedule():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM work_schedule WHERE name=? AND date=?",
        (data["name"], data["date"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result": "ok"})

# 비상근무 삭제
@app.route("/delete_special", methods=["POST"])
def delete_special():
    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM special_duty WHERE name=? AND date=? AND duty=?",
        (data["name"], data["date"], data["duty"])
    )

    conn.commit()
    conn.close()

    return jsonify({"result": "ok"})

# 🔥 엑셀 자동 업로드
@app.route("/upload_excel_auto", methods=["POST"])
def upload_excel_auto():
    file = request.files.get("file")

    if not file:
        return jsonify({"message": "파일 없음"}), 400

    wb = load_workbook(file, data_only=True)
    ws = wb.active

    conn = get_db()
    cur = conn.cursor()

    inserted = 0

    # 남산분소 양식 기준 1차 설정값
    # 안 맞으면 이 3개만 나중에 조정하면 됨
    date_row = 2
    name_col = 2
    start_col = 3

    for row in range(3, ws.max_row + 1):
        name = ws.cell(row=row, column=name_col).value

        if not name:
            continue

        for col in range(start_col, ws.max_column + 1):
            date_cell = ws.cell(row=date_row, column=col).value
            status = ws.cell(row=row, column=col).value

            if not date_cell or not status:
                continue

            # 날짜 변환
            if isinstance(date_cell, datetime):
                date_str = date_cell.strftime("%Y-%m-%d")
            else:
                date_str = str(date_cell).strip()

            name_str = str(name).strip()
            status_str = str(status).strip()

            if name_str in ["None", "nan", ""]:
                continue
            if status_str in ["None", "nan", ""]:
                continue

            cur.execute(
                "INSERT INTO work_schedule (name, date, status) VALUES (?, ?, ?)",
                (name_str, date_str, status_str)
            )
            inserted += 1

    conn.commit()
    conn.close()

    return jsonify({"message": f"{inserted}개 자동 입력 완료"})

# HTML
@app.route("/")
def index():
    return send_from_directory(os.getcwd(), "test.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
