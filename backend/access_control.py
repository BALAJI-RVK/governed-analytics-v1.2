"""
Access Governance – Role-Based Access Control (RBAC) & Table Policy Enforcer
Data Engineering for AI · Final Year Capstone
"""

import re
from config import ROLES
from semantic_layer import resolve_metric


def check_access(role: str, metric_name: str) -> dict:
    role_info = ROLES.get(role)
    if not role_info:
        return {"allowed": False, "reason": f"Unknown role: '{role}'", "code": "UNKNOWN_ROLE"}

    metric = resolve_metric(metric_name)
    if not metric:
        return {"allowed": False, "reason": f"Unknown metric: '{metric_name}'", "code": "UNKNOWN_METRIC"}

    allowed = role_info.get("allowed_metrics", [])
    if "all" in allowed or metric_name in allowed:
        return {
            "allowed": True,
            "role": role,
            "metric": metric_name,
            "reason": f"Role '{role}' is permitted to access approved metric '{metric_name}'",
            "code": "ACCESS_GRANTED"
        }

    return {
        "allowed": False,
        "role": role,
        "metric": metric_name,
        "reason": f"Access Denied: Role '{role}' is NOT authorized to access metric '{metric_name}' under governance policy.",
        "code": "ACCESS_DENIED"
    }


def extract_tables_from_sql(sql: str) -> list:
    """Extract table names referenced in FROM and JOIN clauses."""
    # Strip string literals and comments
    cleaned = re.sub(r"'[^']*'", "", sql)
    cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
    
    # Match FROM and JOIN targets
    matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)", cleaned, re.IGNORECASE)
    known_tables = {"students", "sales", "query_logs"}
    found = []
    for m in matches:
        t = m.lower()
        if t in known_tables and t not in found:
            found.append(t)
    return found


def check_sql_access(role: str, sql: str) -> dict:
    """
    Enforce governance policies on custom SQL queries:
    1. Read-only verification (SELECT only).
    2. Table-level authorization per role.
    """
    role_info = ROLES.get(role)
    if not role_info:
        return {"allowed": False, "reason": f"Unknown role: '{role}'", "code": "UNKNOWN_ROLE", "tables": []}

    cleaned = sql.strip().rstrip(";").strip()

    # Disallow destructive/DML/DDL queries
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "attach", "detach", "vacuum", "pragma"]
    first_word = cleaned.split()[0].lower() if cleaned else ""
    if first_word != "select" and first_word != "with":
        return {
            "allowed": False,
            "reason": "Security Governance Policy: Only read-only SELECT and WITH analytical queries are permitted in self-service mode.",
            "code": "SECURITY_RESTRICTION",
            "tables": []
        }

    for word in forbidden:
        if re.search(rf"\b{word}\b", cleaned, re.IGNORECASE):
            return {
                "allowed": False,
                "reason": f"Security Governance Policy: Disallowed keyword '{word.upper()}' detected. Read-only analytical queries only.",
                "code": "SECURITY_RESTRICTION",
                "tables": []
            }

    tables = extract_tables_from_sql(cleaned)
    allowed_tables = role_info.get("allowed_tables", [])

    if not tables:
        # If no tables recognized, check if querying valid entities
        return {
            "allowed": True,
            "role": role,
            "tables": [],
            "reason": "No sensitive warehouse tables referenced (scalar/system query).",
            "code": "ACCESS_GRANTED"
        }

    # Verify authorization for each table
    unauthorized = [t for t in tables if t not in allowed_tables]
    if unauthorized:
        return {
            "allowed": False,
            "role": role,
            "tables": tables,
            "unauthorized_tables": unauthorized,
            "reason": f"Access Denied: Role '{role}' does not have permission to query warehouse table(s): {', '.join(unauthorized)}. Allowed: {', '.join(allowed_tables)}",
            "code": "ACCESS_DENIED"
        }

    return {
        "allowed": True,
        "role": role,
        "tables": tables,
        "reason": f"Governance Check Passed: Role '{role}' is authorized to query table(s): {', '.join(tables)}",
        "code": "ACCESS_GRANTED"
    }
