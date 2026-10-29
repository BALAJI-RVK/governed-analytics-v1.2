"""
Configuration for Governed Self-Service Analytics
Data Engineering for AI · Final Year Capstone (KL University)
"""

# Project & Presentation Metadata
PROJECT_META = {
    "title": "Governed Self-Service Analytics with Query Cost Control",
    "subtitle": "A Data Engineering Platform for Cost-Aware and Governed Data Exploration",
    "department": "Department of Computer Science and Information Technology",
    "institution": "KL UNIVERSITY (DSCI-72)",
    "guide": "Dr. Ch Ramesh Kumar",
    "team": [
        {"id": "2300090166", "name": "Team Member 1"},
        {"id": "2300090172", "name": "Team Member 2"},
        {"id": "2300090175", "name": "Team Member 3"},
        {"id": "2300090180", "name": "Team Member 4"}
    ]
}

# Cost control policies (illustrative warehouse values)
SOFT_BUDGET = 0.50      # above this → WARN ($0.50)
HARD_BUDGET = 1.00      # above this → BLOCK ($1.00)
COST_PER_1000_ROWS = 0.02

ROLES = {
    "admin": {
        "title": "Administrator / Data Lead",
        "description": "Full warehouse access to all tables and metrics",
        "allowed_metrics": ["all"],
        "allowed_tables": ["students", "sales", "query_logs"]
    },
    "analyst": {
        "title": "Business Analyst",
        "description": "Sales warehouse + aggregated student data access",
        "allowed_metrics": [
            "avg_marks_by_semester",
            "avg_marks_by_dept",
            "avg_cse_marks_by_semester",
            "revenue_by_region",
            "total_sales",
            "sales_by_product"
        ],
        "allowed_tables": ["students", "sales"]
    },
    "student_viewer": {
        "title": "Student / Viewer",
        "description": "Restricted access: only aggregated student performance data",
        "allowed_metrics": [
            "avg_marks_by_semester",
            "avg_marks_by_dept",
            "avg_cse_marks_by_semester"
        ],
        "allowed_tables": ["students"]
    }
}

DB_PATH = "data_warehouse.db"
