"""
HI 741 – Final Project
11 May 2026
Steven Nichols

provider.py

Provider class – a healthcare provider with specialty and a linked encounter list.
"""


class Provider:
    """Represents a healthcare provider in the clinical data system."""

    def __init__(self, provider_id: str, name: str, specialty: str, department_id: str):
        self.provider_id   = provider_id
        self.name          = name
        self.specialty     = specialty
        self.department_id = department_id
        self.encounters    = []

    def add_encounter(self, encounter) -> None:
        """Link an Encounter object to this provider."""
        self.encounters.append(encounter)

    def encounter_count(self) -> int:
        """Return the total number of encounters handled by this provider."""
        return len(self.encounters)

    def __repr__(self) -> str:
        return f"[Provider: {self.provider_id}, {self.name}, {self.specialty}]"
