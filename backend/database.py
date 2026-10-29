"""
SQLite Data Warehouse + sample data seeding
"""

import sqlite3
import random
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS students")
    cur.execute("DROP TABLE IF EXISTS sales")
    cur.execute("DROP TABLE IF EXISTS query_logs")

    cur.execute("""
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            semester INTEGER,
            marks REAL,
            year INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE sales (
            order_id INTEGER PRIMARY KEY,
            region TEXT,
            product TEXT,
            amount REAL,
            discount REAL,
            return_flag INTEGER,
            quantity INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            metric TEXT,
            estimated_cost REAL,
            decision TEXT,
            timestamp TEXT
        )
    """)

    # Seed students (~300)
    departments = ["CSE", "ECE", "ME", "IT", "CIVIL"]
    names = [
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
        "Krishna", "Ishaan", "Ananya", "Diya", "Saanvi", "Aadhya", "Pari", "Anika",
        "Myra", "Sara", "Navya", "Ira", "Rahul", "Priya", "Karan", "Neha", "Rohan"
    ]
    students = []
    for i in range(1, 301):
        students.append((
            i,
            f"{random.choice(names)} {i}",
            random.choice(departments),
            random.randint(1, 8),
            round(random.uniform(45, 98), 1),
            random.choice([2022, 2023, 2024, 2025])
        ))
    cur.executemany(
        "INSERT INTO students VALUES (?,?,?,?,?,?)", students
    )

    # Seed sales (~400)
    regions = ["North", "South", "East", "West", "Central"]
    products = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headset"]
    sales = []
    for i in range(1, 401):
        amount = round(random.uniform(200, 2500), 2)
        discount = round(amount * random.uniform(0, 0.25), 2)
        sales.append((
            i,
            random.choice(regions),
            random.choice(products),
            amount,
            discount,
            1 if random.random() < 0.08 else 0,
            random.randint(1, 5)
        ))
    cur.executemany(
        "INSERT INTO sales VALUES (?,?,?,?,?,?,?)", sales
    )

    conn.commit()
    conn.close()
    print("[+] Database seeded: 300 students + 400 sales records")

if __name__ == "__main__":
    init_db()
