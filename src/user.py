"""
HI 741 – Final Project
11 May 2026
Steven Nichols

user.py

User class – authenticated user with role-based access control.
"""

# Ordered list of action keys available to each role
ROLE_ACTIONS: dict[str, list[str]] = {
    "clinician":  ["retrieve_patient", "add_patient", "remove_patient",
                   "count_visits", "view_note"],
    "nurse":      ["retrieve_patient", "add_patient", "remove_patient",
                   "count_visits", "view_note"],
    "admin":      ["count_visits", "monitor_workload"],
    "management": ["generate_key_statistics", "monitor_revenue"],
}

# Only these roles may access Protected Health Information
_PHI_ROLES: set[str] = {"clinician", "nurse"}


class User:
    """An authenticated system user whose role determines data access and available actions."""

    def __init__(self, username: str, role: str):
        self.username = username
        self.role     = role

    def can_access_phi(self) -> bool:
        """Return True if this user's role permits access to PHI."""
        return self.role in _PHI_ROLES

    def allowed_actions(self) -> list[str]:
        """Return the ordered list of action keys permitted for this user's role."""
        return ROLE_ACTIONS.get(self.role, [])

    def __repr__(self) -> str:
        return f"[User: {self.username}, role={self.role}]"
