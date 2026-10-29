# Governed Self-Service Analytics with Query Cost Control

**Data Engineering for AI · Final Year Capstone (KL University · DSCI-72)**

A production-style analytical data platform that balances three core forces:
$$\textbf{User Freedom} \quad + \quad \textbf{Data Governance} \quad + \quad \textbf{Query Cost Control}$$

---

## 👥 Project Information

- **Institution**: KL University · Department of Computer Science & Information Technology
- **Course**: Data Engineering for AI (DSCI-72) · Final Year Capstone Project
- **Guide**: **Dr. Ch Ramesh Kumar**
- **Team**: `2300090166` · `2300090172` · `2300090175` · `2300090180`

---

## 🚀 Quick Start

Open PowerShell or Command Prompt and run:

```bash
cd backend
python server.py
```

*(On Windows, if Python is not in your global PATH:)*
```powershell
$env:Path = "C:\Users\rvkba\AppData\Local\Programs\Python\Python314;C:\Users\rvkba\AppData\Local\Programs\Python\Python314\Scripts;" + $env:Path
python server.py
```

Then open in your browser:
```
http://localhost:8000
```

Zero external packages or build steps required (`pure Python standard library + sqlite3`).

---

## ✨ Features & Capstone Alignment

### 1. Active Custom SQL Studio with Live Query Planner
- Write custom ad-hoc `SELECT` queries directly in the UI.
- The active query cost engine evaluates queries using SQLite `EXPLAIN QUERY PLAN`:
  - Detects full table scans, sorting overhead, and prohibitive quadratic Cartesian cross-joins.
  - Predicts intermediate scanned rows and computes estimated dollar cost (\$) before execution.
  - Enforces role-based table authorization (`students`, `sales`, `query_logs`).

### 2. Reusable Semantic Layer (Slide 05)
- Standardized approved business metric definitions preventing discrepancy across teams:
  $$\text{Revenue} = \text{Sales Amount} - \text{Discounts} - \text{Returns}$$
- Benchmark query: *Average CSE student marks by semester* (Slide 03).

### 3. Active 5-Stage Live Pipeline Stepper
Visual interactive tracker animating each query request through:
1. **User Request** (Input query or metric)
2. **Semantic Layer / AST** (Metric resolution or syntax AST validation)
3. **Access Governance** (Role-based access check against allowed tables)
4. **Cost Estimator** (EXPLAIN plan + row statistics & cost calculation)
5. **Policy Engine** (Enforces Soft Budget \$0.50 and Hard Budget \$1.00 &rarr; **ALLOW / WARN / BLOCK**)
6. **Execution & Visualization** (Interactive data table + dynamic Chart.js chart)

### 4. Built-in Presentation & Architecture Tabs
- **Tab 1: Interactive Query Studio** (The live governed workbench)
- **Tab 2: System Architecture (Slides 07 & 08)** (End-to-End data engineering pipeline & 9 DE responsibilities)
- **Tab 3: Capstone Presentation (Slides 01–10)** (Slide-by-slide guide for presenting to evaluators)
- **Tab 4: Audit & Governance Logs** (Live immutable audit trail of all executions)

---

## 🎯 Built-in Demo Scenarios (Matching PPT Slides 03 & 04)

Click the scenario buttons on the left panel for 1-click evaluation:

| # | Scenario | Role | Mode | Expected | Rule / Policy Triggered |
|---|----------|------|------|----------|--------------------------|
| **1** | CSE average marks by semester | `analyst` | Semantic | **ALLOW** | Low compute cost (\$0.0012 &le; \$0.50 budget) |
| **2** | Enterprise Net Revenue formula | `analyst` | Semantic | **ALLOW** | Approved metric definition ($\text{Sales} - \text{Discounts} - \text{Returns}$) |
| **3** | Expensive cross-join Cartesian scan | `admin` | Semantic | **BLOCK** | Predicts 120,000 rows (\$2.40+ compute &gt; \$1.00 hard budget) |
| **4** | student_viewer tries sales data | `student_viewer` | Semantic | **BLOCK** | Access Governance Denied (Restricted warehouse table) |
| **5** | Custom SQL: Students filter with WHERE | `analyst` | Custom SQL | **ALLOW** | Selectivity reduction factor applied; under budget |
| **6** | Custom SQL: Students CROSS JOIN sales | `admin` | Custom SQL | **BLOCK** | Query planner detects Cartesian scan &rarr; exceeds budget |
| **7** | Custom SQL: student_viewer queries sales | `student_viewer` | Custom SQL | **BLOCK** | Table AST extractor identifies unauthorized table |

---

## 📂 Project Structure

```
governed-analytics/
├── backend/
│   ├── server.py            # HTTP Server + unified REST endpoints
│   ├── config.py            # Budgets, roles, table permissions & metadata
│   ├── database.py          # SQLite warehouse (students & sales seed data)
│   ├── semantic_layer.py    # Approved metric formulas (Slide 05)
│   ├── access_control.py    # RBAC + Table-level AST SQL authorization
│   ├── cost_estimator.py    # Active EXPLAIN QUERY PLAN cost engine
│   └── policy_engine.py     # ALLOW / WARN / BLOCK decision logic
├── frontend/
│   └── index.html           # Presentation-grade modern UI (Tailwind + Chart.js)
└── README.md
```

---

## How the presentation concepts are implemented

| Concept from slides              | File / Module                |
|----------------------------------|------------------------------|
| Semantic Layer                   | `semantic_layer.py`          |
| Access Governance                | `access_control.py`          |
| Query Cost Estimation            | `cost_estimator.py`          |
| Cost Control Policies            | `policy_engine.py` + config  |
| Self-Service Analytics           | Frontend metric selector     |
| Full Data Engineering pipeline   | Seed → Warehouse → Query path|

---

## Sample Data

- **300 students** (CSE, ECE, ME, IT, CIVIL) with marks & semester  
- **400 sales** records across regions & products (with discounts & returns)

---

## Technology (intentionally lightweight)

- Python 3 standard library (`http.server`, `sqlite3`)
- No FastAPI / Flask / SQLAlchemy required (works even offline)
- Single HTML/CSS/JS frontend

---

## Future Scope (from original presentation)

- Cloud data warehouse integration (BigQuery, Snowflake, Redshift)
- Advanced cost prediction using real query plans
- AI-assisted natural-language analytics
- Automatic query optimization
- Multi-warehouse support & lineage visualization

---

**Team**: 2300090166 · 2300090172 · 2300090175 · 2300090180  
**Guide**: Dr. Ch Ramesh Kumar  
**Department**: Computer Science And Information Technology  
**KL University · DSCI-72**
