"""
HI 741 – Final Project
11 May 2026
Steven Nichols

department.py

Department class – a hospital department tracking encounters for analytics.
"""


class Department:
    """Represents a hospital department with linked encounters."""

    def __init__(self, department_id: str, name: str, location: str):
        self.department_id = department_id
        self.name          = name
        self.location      = location
        self.encounters    = []

    def add_encounter(self, encounter) -> None:
        """Link an Encounter object to this department."""
        self.encounters.append(encounter)

    def encounter_count(self) -> int:
        """Return the total number of encounters in this department."""
        return len(self.encounters)

    def total_revenue(self) -> float:
        """Return the sum of all procedure costs across every encounter in this department."""
        return sum(
            proc.cost
            for enc in self.encounters
            for proc in enc.procedures
        )

    def __repr__(self) -> str:
        return f"[Department: {self.department_id}, {self.name}, {self.location}]"
