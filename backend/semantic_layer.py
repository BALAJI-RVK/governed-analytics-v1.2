"""
Reusable Semantic Layer – one approved definition per business metric
"""

METRIC_DEFINITIONS = {
    "avg_cse_marks_by_semester": {
        "title": "Avg CSE Marks by Semester",
        "description": "Average CSE student marks grouped by semester (Slide 03 Benchmark)",
        "formula": "Avg Marks = SUM(marks) / COUNT(students WHERE department = 'CSE')",
        "sql": """
            SELECT semester, ROUND(AVG(marks), 2) AS avg_marks, COUNT(*) AS student_count
            FROM students WHERE department = 'CSE'
            GROUP BY semester ORDER BY semester
        """,
        "estimated_rows": 60,
        "category": "students"
    },
    "avg_marks_by_semester": {
        "title": "Avg Marks by Semester (All)",
        "description": "University-wide average student marks grouped by semester",
        "formula": "Avg Marks = SUM(marks) / COUNT(students)",
        "sql": """
            SELECT semester, ROUND(AVG(marks), 2) AS avg_marks, COUNT(*) AS student_count
            FROM students GROUP BY semester ORDER BY semester
        """,
        "estimated_rows": 300,
        "category": "students"
    },
    "avg_marks_by_dept": {
        "title": "Avg Marks by Department",
        "description": "Academic performance comparison across university departments",
        "formula": "Avg Marks = SUM(marks) / COUNT(students) GROUP BY department",
        "sql": """
            SELECT department, ROUND(AVG(marks), 2) AS avg_marks, COUNT(*) AS student_count
            FROM students GROUP BY department ORDER BY avg_marks DESC
        """,
        "estimated_rows": 300,
        "category": "students"
    },
    "revenue_by_region": {
        "title": "Revenue by Region",
        "description": "Regional revenue breakdown using approved net revenue metric",
        "formula": "Revenue = Sales Amount - Discounts - Returns (Slide 05 Definition)",
        "sql": """
            SELECT region,
                   ROUND(SUM(amount - discount), 2) AS revenue,
                   COUNT(*) AS orders
            FROM sales WHERE return_flag = 0
            GROUP BY region ORDER BY revenue DESC
        """,
        "estimated_rows": 370,
        "category": "sales"
    },
    "total_sales": {
        "title": "Full Sales Summary & Net Revenue",
        "description": "Enterprise-wide sales overview applying governed metric formulas",
        "formula": "Net Revenue = SUM(CASE WHEN return_flag = 0 THEN amount - discount ELSE 0 END)",
        "sql": """
            SELECT
                COUNT(*) AS total_orders,
                ROUND(SUM(amount), 2) AS gross_amount,
                ROUND(SUM(discount), 2) AS total_discount,
                ROUND(SUM(CASE WHEN return_flag = 0 THEN amount - discount ELSE 0 END), 2) AS net_revenue,
                SUM(CASE WHEN return_flag = 1 THEN 1 ELSE 0 END) AS returned_orders
            FROM sales
        """,
        "estimated_rows": 400,
        "category": "sales"
    },
    "sales_by_product": {
        "title": "Sales by Product Category",
        "description": "Product-level analytical breakdown for business analysts",
        "formula": "Product Revenue = SUM(amount - discount) WHERE return_flag = 0",
        "sql": """
            SELECT product, COUNT(*) AS orders,
                   ROUND(SUM(amount - discount), 2) AS revenue
            FROM sales WHERE return_flag = 0
            GROUP BY product ORDER BY revenue DESC
        """,
        "estimated_rows": 370,
        "category": "sales"
    },
    "expensive_full_scan": {
        "title": "Cross-Join Cartesian Scan (Cost Stress Test)",
        "description": "Cost control stress-test: joins 400 sales with 300 students without filter",
        "formula": "Cartesian Product Scan = 400 × 300 = 120,000 intermediate records",
        "sql": """
            SELECT s.region, st.department,
                   COUNT(*) AS combo_count,
                   ROUND(AVG(st.marks), 2) AS avg_marks
            FROM sales s CROSS JOIN students st
            GROUP BY s.region, st.department
            LIMIT 50
        """,
        "estimated_rows": 120000,
        "category": "mixed"
    }
}


def get_available_metrics(role: str) -> list:
    from config import ROLES
    role_info = ROLES.get(role, {})
    allowed = role_info.get("allowed_metrics", [])
    if "all" in allowed:
        return list(METRIC_DEFINITIONS.keys())
    return [m for m in METRIC_DEFINITIONS if m in allowed]


def resolve_metric(metric_name: str):
    return METRIC_DEFINITIONS.get(metric_name)


def execute_metric(conn, metric_name: str) -> list:
    metric = resolve_metric(metric_name)
    if not metric:
        return []
    cur = conn.cursor()
    cur.execute(metric["sql"])
    rows = cur.fetchall()
    return [dict(row) for row in rows]
