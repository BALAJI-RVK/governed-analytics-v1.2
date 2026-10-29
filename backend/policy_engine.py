"""
Policy Engine – Final Decision & Enforcement (Slide 04 & 06)
Evaluates Governance Rules + Cost Budgets to yield ALLOW / WARN / BLOCK
"""

from config import SOFT_BUDGET, HARD_BUDGET


def decide(access_result: dict, cost_result: dict) -> dict:
    cost = cost_result.get("estimated_cost", 0.0)

    # 1. Governance Access Check First
    if not access_result.get("allowed", False):
        return {
            "decision": "BLOCK",
            "reason": access_result.get("reason", "Access Denied by Governance Policy"),
            "code": "GOVERNANCE_BLOCK",
            "can_execute": False,
            "badge_color": "red",
            "stage_governance": {"status": "FAIL", "message": access_result.get("reason")},
            "stage_cost": {"status": "SKIPPED", "message": "Query stopped before cost budget enforcement."},
            "soft_budget": SOFT_BUDGET,
            "hard_budget": HARD_BUDGET
        }

    # 2. Hard Budget Limit Enforcement
    if cost > HARD_BUDGET:
        return {
            "decision": "BLOCK",
            "reason": f"Cost Control Policy Blocked: Estimated cost ${cost:.2f} exceeds hard budget limit of ${HARD_BUDGET:.2f}. Query rejected to prevent warehouse cost overrun.",
            "code": "COST_HARD_LIMIT",
            "can_execute": False,
            "badge_color": "red",
            "stage_governance": {"status": "PASS", "message": access_result.get("reason")},
            "stage_cost": {"status": "FAIL", "message": f"${cost:.2f} > ${HARD_BUDGET:.2f} Hard Budget"},
            "soft_budget": SOFT_BUDGET,
            "hard_budget": HARD_BUDGET
        }

    # 3. Soft Budget Limit Warning
    if cost > SOFT_BUDGET:
        return {
            "decision": "WARN",
            "reason": f"Soft Budget Warning: Estimated cost ${cost:.2f} exceeds soft threshold of ${SOFT_BUDGET:.2f}. Query executed but flagged in audit log.",
            "code": "COST_SOFT_LIMIT",
            "can_execute": True,
            "badge_color": "orange",
            "stage_governance": {"status": "PASS", "message": access_result.get("reason")},
            "stage_cost": {"status": "WARN", "message": f"${cost:.2f} > ${SOFT_BUDGET:.2f} Soft Budget"},
            "soft_budget": SOFT_BUDGET,
            "hard_budget": HARD_BUDGET
        }

    # 4. Standard Allowed Query
    return {
        "decision": "ALLOW",
        "reason": f"Query Approved: Cost of ${cost:.2f} is well within budget (${HARD_BUDGET:.2f}) and governance checks passed.",
        "code": "OK",
        "can_execute": True,
        "badge_color": "green",
        "stage_governance": {"status": "PASS", "message": access_result.get("reason")},
        "stage_cost": {"status": "PASS", "message": f"${cost:.2f} <= ${SOFT_BUDGET:.2f} Budget OK"},
        "soft_budget": SOFT_BUDGET,
        "hard_budget": HARD_BUDGET
    }
