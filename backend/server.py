"""
Governed Self-Service Analytics – Pure Python HTTP Server
No external web framework required.
"""

import json
import os
import sys
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from database import init_db, get_connection
from semantic_layer import get_available_metrics, resolve_metric, execute_metric, METRIC_DEFINITIONS
from access_control import check_access, check_sql_access
from cost_estimator import estimate_cost, estimate_sql_cost
from policy_engine import decide
from config import ROLES, SOFT_BUDGET, HARD_BUDGET, PROJECT_META

# Paths
BACKEND_DIR = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
PORT = 8000


class GovernedHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            # Serve frontend
            index = FRONTEND_DIR / "index.html"
            if index.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(index.read_bytes())
            else:
                self._send_json({"error": "Frontend not found"}, 404)
            return

        if path == "/api/health":
            self._send_json({"status": "ok", "service": "Governed Self-Service Analytics"})
            return

        if path == "/api/meta":
            self._send_json(PROJECT_META)
            return

        if path == "/api/roles":
            self._send_json({
                "roles": ROLES,
                "soft_budget": SOFT_BUDGET,
                "hard_budget": HARD_BUDGET
            })
            return

        if path == "/api/tables":
            conn = get_connection()
            cur = conn.cursor()
            tables_info = {}
            for tbl in ["students", "sales"]:
                cur.execute(f"PRAGMA table_info({tbl})")
                cols = [{"name": r[1], "type": r[2]} for r in cur.fetchall()]
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                count = cur.fetchone()[0]
                tables_info[tbl] = {
                    "columns": cols,
                    "row_count": count
                }
            conn.close()
            self._send_json(tables_info)
            return

        if path == "/api/metrics":
            role = qs.get("role", ["analyst"])[0]
            available = get_available_metrics(role)
            details = []
            for m in available:
                meta = METRIC_DEFINITIONS[m]
                details.append({
                    "name": m,
                    "title": meta.get("title", m),
                    "description": meta["description"],
                    "formula": meta.get("formula", ""),
                    "category": meta["category"],
                    "estimated_rows": meta["estimated_rows"],
                    "sql": meta.get("sql", "").strip()
                })
            self._send_json({"role": role, "metrics": details})
            return

        if path == "/api/logs":
            limit = int(qs.get("limit", ["15"])[0])
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, role, metric, estimated_cost, decision, timestamp "
                "FROM query_logs ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self._send_json(rows)
            return

        if path == "/api/demo-scenarios":
            self._send_json({
                "scenarios": [
                    {
                        "id": 1,
                        "title": "Example 1: Average CSE Marks (Slide 03)",
                        "subtitle": "Admin / Analyst query · Low cost & permitted",
                        "role": "analyst",
                        "mode": "semantic",
                        "metric": "avg_cse_marks_by_semester",
                        "expected": "ALLOW",
                        "explanation": "University admin query: 'Show average CSE student marks by semester'. Small warehouse scan (~60 rows), low compute cost ($0.0012 <= $0.50 budget)."
                    },
                    {
                        "id": 2,
                        "title": "Example 2: Enterprise Net Revenue (Slide 05)",
                        "subtitle": "Approved Metric Definition: Revenue = Sales - Discounts - Returns",
                        "role": "analyst",
                        "mode": "semantic",
                        "metric": "revenue_by_region",
                        "expected": "ALLOW",
                        "explanation": "Applies governed net revenue formula. Scans sales warehouse, compliant with analyst permissions and under hard budget."
                    },
                    {
                        "id": 3,
                        "title": "Example 3: Expensive Cartesian Cross-Join (Slide 03)",
                        "subtitle": "Admin query · Prohibitive warehouse compute overrun",
                        "role": "admin",
                        "mode": "semantic",
                        "metric": "expensive_full_scan",
                        "expected": "BLOCK",
                        "explanation": "Unconstrained cross join generates 120,000 intermediate records. Cost engine predicts $2.40+ compute, triggering policy BLOCK (> $1.00 hard limit)."
                    },
                    {
                        "id": 4,
                        "title": "Example 4: Sensitive Data Access Denied (Slide 03)",
                        "subtitle": "student_viewer tries to access financial/sales warehouse",
                        "role": "student_viewer",
                        "mode": "semantic",
                        "metric": "revenue_by_region",
                        "expected": "BLOCK",
                        "explanation": "Governance First: student_viewer role is only permitted to see aggregated student marks. Access denied regardless of query cost."
                    },
                    {
                        "id": 5,
                        "title": "Custom SQL: High Marks Student Filter",
                        "subtitle": "Ad-hoc query with WHERE clause filtering",
                        "role": "analyst",
                        "mode": "custom",
                        "sql": "SELECT department, COUNT(*) AS count, ROUND(AVG(marks), 2) AS avg_marks\nFROM students\nWHERE marks >= 75\nGROUP BY department\nORDER BY avg_marks DESC;",
                        "expected": "ALLOW",
                        "explanation": "Active SQL query analyzer confirms table authorization and applies selectivity reduction factor. Under budget."
                    },
                    {
                        "id": 6,
                        "title": "Custom SQL: Unindexed Cartesian Explosion",
                        "subtitle": "Ad-hoc students CROSS JOIN sales query",
                        "role": "admin",
                        "mode": "custom",
                        "sql": "SELECT st.name, st.department, s.product, s.amount\nFROM students st\nCROSS JOIN sales s;",
                        "expected": "BLOCK",
                        "explanation": "Active EXPLAIN QUERY PLAN detects quadratic Cartesian product scan. Cost engine predicts budget overrun (> $1.00) and blocks execution."
                    },
                    {
                        "id": 7,
                        "title": "Custom SQL: student_viewer queries sales table",
                        "subtitle": "Direct table governance enforcement in ad-hoc SQL",
                        "role": "student_viewer",
                        "mode": "custom",
                        "sql": "SELECT order_id, product, amount, discount\nFROM sales\nWHERE amount > 500;",
                        "expected": "BLOCK",
                        "explanation": "SQL AST table extractor identifies 'sales'. student_viewer is not authorized to query sales table. Blocked by Access Governance before execution."
                    }
                ]
            })
            return

        # Fallback to static files
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/query":
            try:
                body = self._read_json()
                username = body.get("username", "demo_user")
                role = body.get("role", "analyst")
                mode = body.get("mode", "semantic")   # "semantic" or "custom"
                metric_name = body.get("metric")
                custom_sql = body.get("sql", "").strip()

                conn = get_connection()
                start_time = time.time()

                if mode == "custom":
                    # --- CUSTOM SQL PIPELINE ---
                    if not custom_sql:
                        self._send_json({"detail": "SQL query text is required for custom mode"}, 400)
                        conn.close()
                        return

                    # 1. Access Governance Check (read-only + table level permissions)
                    access_result = check_sql_access(role, custom_sql)

                    # 2. Query Cost Estimation (Active SQLite EXPLAIN QUERY PLAN analysis)
                    cost_result = estimate_sql_cost(conn, custom_sql)

                    # 3. Policy Decision (ALLOW / WARN / BLOCK)
                    policy_result = decide(access_result, cost_result)

                    # 4. Execute if allowed
                    results = None
                    columns = []
                    row_count = 0
                    exec_time_ms = 0.0

                    if policy_result["can_execute"]:
                        t0 = time.time()
                        cur = conn.cursor()
                        cur.execute(custom_sql)
                        raw_rows = cur.fetchall()
                        exec_time_ms = round((time.time() - t0) * 1000, 2)
                        if cur.description:
                            columns = [d[0] for d in cur.description]
                            results = [dict(zip(columns, r)) for r in raw_rows]
                            row_count = len(results)
                        else:
                            results = []

                    # 5. Log query in audit log
                    query_summary = (custom_sql[:60] + "...") if len(custom_sql) > 60 else custom_sql
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO query_logs (username, role, metric, estimated_cost, decision, timestamp) "
                        "VALUES (?,?,?,?,?,?)",
                        (username, role, f"SQL: {query_summary}", cost_result["estimated_cost"],
                         policy_result["decision"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    conn.commit()
                    conn.close()

                    self._send_json({
                        "mode": "custom",
                        "sql": custom_sql,
                        "access": access_result,
                        "cost": cost_result,
                        "policy": policy_result,
                        "results": results,
                        "columns": columns,
                        "row_count": row_count,
                        "execution_time_ms": exec_time_ms,
                        "message": policy_result["reason"]
                    })
                    return

                else:
                    # --- SEMANTIC LAYER PIPELINE ---
                    if not metric_name:
                        self._send_json({"detail": "metric is required for semantic mode"}, 400)
                        conn.close()
                        return

                    metric = resolve_metric(metric_name)
                    if not metric:
                        self._send_json({"detail": f"Metric '{metric_name}' not found"}, 404)
                        conn.close()
                        return

                    # 1. Access Governance Check
                    access_result = check_access(role, metric_name)

                    # 2. Cost Estimation
                    cost_result = estimate_cost(metric_name)

                    # 3. Policy Decision
                    policy_result = decide(access_result, cost_result)

                    # 4. Execute if allowed
                    results = None
                    columns = []
                    row_count = 0
                    exec_time_ms = 0.0

                    if policy_result["can_execute"]:
                        t0 = time.time()
                        cur = conn.cursor()
                        cur.execute(metric["sql"])
                        raw_rows = cur.fetchall()
                        exec_time_ms = round((time.time() - t0) * 1000, 2)
                        if cur.description:
                            columns = [d[0] for d in cur.description]
                            results = [dict(zip(columns, r)) for r in raw_rows]
                            row_count = len(results)
                        else:
                            results = []

                    # 5. Log
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO query_logs (username, role, metric, estimated_cost, decision, timestamp) "
                        "VALUES (?,?,?,?,?,?)",
                        (username, role, metric_name, cost_result["estimated_cost"],
                         policy_result["decision"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    conn.commit()
                    conn.close()

                    self._send_json({
                        "mode": "semantic",
                        "metric": metric_name,
                        "title": metric.get("title", metric_name),
                        "description": metric["description"],
                        "formula": metric.get("formula", ""),
                        "sql": metric.get("sql", "").strip(),
                        "access": access_result,
                        "cost": cost_result,
                        "policy": policy_result,
                        "results": results,
                        "columns": columns,
                        "row_count": row_count,
                        "execution_time_ms": exec_time_ms,
                        "message": policy_result["reason"]
                    })
                    return

            except Exception as e:
                self._send_json({"detail": str(e)}, 500)
            return

        self._send_json({"detail": "Not found"}, 404)


def main():
    # Ensure DB exists
    if not os.path.exists(DB_PATH := str(BACKEND_DIR / "data_warehouse.db")):
        print("Initializing database...")
        os.chdir(BACKEND_DIR)
        init_db()
    else:
        # Always re-seed for clean demo
        os.chdir(BACKEND_DIR)
        init_db()

    print(f"\n[+] Governed Self-Service Analytics running at http://localhost:{PORT}")
    print(f"    Open http://localhost:{PORT} in your browser to explore the dashboard.\n")
    server = HTTPServer(("0.0.0.0", PORT), GovernedHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
