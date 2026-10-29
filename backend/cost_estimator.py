"""
Query Cost Estimation Engine – Pre-Execution Cost & Resource Prediction
Data Engineering for AI · Final Year Capstone (Slide 06)
"""

import re
from semantic_layer import resolve_metric
from config import COST_PER_1000_ROWS, SOFT_BUDGET, HARD_BUDGET


def _calculate_risk(cost: float) -> str:
    if cost > HARD_BUDGET:
        return "high"
    elif cost > SOFT_BUDGET:
        return "medium"
    return "low"


def estimate_cost(metric_name: str) -> dict:
    """Cost estimation for approved semantic layer metrics."""
    metric = resolve_metric(metric_name)
    if not metric:
        return {
            "estimated_rows": 0,
            "estimated_cost": 0.0,
            "estimated_data_mb": 0.0,
            "risk_level": "unknown",
            "details": "Metric not found in semantic catalog."
        }

    rows = metric.get("estimated_rows", 100)
    cost = round((rows / 1000) * COST_PER_1000_ROWS, 4)
    data_mb = round((rows * 256) / (1024 * 1024), 3)

    return {
        "metric": metric_name,
        "estimated_rows": rows,
        "estimated_cost": cost,
        "estimated_data_mb": data_mb,
        "risk_level": _calculate_risk(cost),
        "cost_per_1000_rows": COST_PER_1000_ROWS,
        "query_plan": [f"Pre-compiled semantic plan for '{metric_name}'"],
        "complexity_factors": [f"Scans ~{rows:,} pre-aggregated rows"],
        "details": f"Scans ~{rows:,} rows (~{data_mb} MB) → Estimated Compute: ${cost:.4f}"
    }


def estimate_sql_cost(conn, sql: str) -> dict:
    """
    Active Query Cost Engine for ad-hoc / custom SQL:
    1. Runs EXPLAIN QUERY PLAN on SQLite.
    2. Measures table scans, Cartesian cross joins, and sort overheads.
    3. Simulates cloud warehouse data volume (MB/GB) and compute cost ($).
    """
    cur = conn.cursor()
    query_plan = []
    complexity_factors = []

    # Get actual table sizes from DB warehouse
    table_counts = {}
    for tbl in ["students", "sales", "query_logs"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            table_counts[tbl] = cur.fetchone()[0]
        except Exception:
            table_counts[tbl] = 0

    # 1. Run EXPLAIN QUERY PLAN
    cleaned_sql = sql.strip().rstrip(";")
    try:
        cur.execute(f"EXPLAIN QUERY PLAN {cleaned_sql}")
        plan_rows = cur.fetchall()
        for r in plan_rows:
            # SQLite format: (id, parent, notused, detail)
            detail = r[3] if len(r) > 3 else str(r)
            query_plan.append(detail)
    except Exception as e:
        query_plan.append(f"Syntax/Planner Note: {e}")

    # 2. Analyze complexity
    detected_scans = []
    has_cross_join = bool(re.search(r"\bcross\s+join\b", cleaned_sql, re.IGNORECASE))
    tables_in_sql = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)", cleaned_sql, re.IGNORECASE)
    tables_in_sql = [t.lower() for t in tables_in_sql if t.lower() in table_counts]

    for plan_line in query_plan:
        if "SCAN" in plan_line.upper():
            for tbl in table_counts:
                if tbl in plan_line.lower() and tbl not in detected_scans:
                    detected_scans.append(tbl)
                    complexity_factors.append(f"Full table scan on '{tbl}' ({table_counts[tbl]:,} rows)")
        if "TEMP B-TREE" in plan_line.upper():
            complexity_factors.append("Temporary B-Tree materialized for sorting/grouping")

    # 3. Calculate estimated rows scanned
    if has_cross_join or (len(tables_in_sql) >= 2 and "where" not in cleaned_sql.lower() and "on" not in cleaned_sql.lower()):
        # Cartesian product
        mult = 1
        for t in (tables_in_sql or ["students", "sales"]):
            mult *= max(table_counts.get(t, 300), 1)
        estimated_rows = max(mult, 120000)
        complexity_factors.append(f"Cartesian Cross-Join detected: {estimated_rows:,} intermediate row product!")
    elif detected_scans:
        estimated_rows = sum(table_counts.get(t, 100) for t in detected_scans)
    else:
        # Default estimation based on referenced tables
        estimated_rows = sum(table_counts.get(t, 100) for t in tables_in_sql) if tables_in_sql else 100

    # Adjust for WHERE selectivity
    if "where" in cleaned_sql.lower() and not has_cross_join:
        estimated_rows = max(int(estimated_rows * 0.35), 10)
        complexity_factors.append("Filter predicate selectivity applied (~35% scan reduction)")

    # 4. Warehouse dollar cost heuristic
    # Big warehouse scale multiplier for illustrative demonstration ($0.02 / 1000 rows)
    base_cost = (estimated_rows / 1000.0) * COST_PER_1000_ROWS

    # If Cartesian cross join was detected, illustrate prohibitive cloud scan cost
    if has_cross_join or estimated_rows > 50000:
        base_cost = max(base_cost, 2.40)

    # Multiplier for heavy grouping / sorting
    if "TEMP B-TREE" in " ".join(query_plan).upper():
        base_cost *= 1.15

    estimated_cost = round(base_cost, 4)
    data_mb = round((estimated_rows * 256) / (1024 * 1024), 3)

    return {
        "estimated_rows": estimated_rows,
        "estimated_cost": estimated_cost,
        "estimated_data_mb": data_mb,
        "risk_level": _calculate_risk(estimated_cost),
        "cost_per_1000_rows": COST_PER_1000_ROWS,
        "query_plan": query_plan,
        "complexity_factors": complexity_factors,
        "details": f"Estimated ~{estimated_rows:,} rows scanned (~{data_mb} MB) → Computed Cost: ${estimated_cost:.4f}"
    }
