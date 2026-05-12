"""
HI 741 – Final Project
11 May 2026
Steven Nichols

patient.py

Patient class – demographic and clinical attributes for one patient; maintains a list of encounters.
"""


class Patient:
    """A single patient with demographics and a linked encounter list."""

    def __init__(self, patient_id: str, age: int, gender: str,
                 bmi: float, a1c: float | None, bp_sys: int, bp_dia: int, smoking: bool):
        self.patient_id = patient_id
        self.age        = age
        self.gender     = gender
        self.bmi        = bmi
        self.a1c        = a1c
        self.bp_sys     = bp_sys
        self.bp_dia     = bp_dia
        self.smoking    = smoking
        self.encounters = []

    def add_encounter(self, encounter) -> None:
        """Link an Encounter object to this patient."""
        self.encounters.append(encounter)

    def count_encounters(self) -> int:
        """Return the number of encounters for this patient."""
        return len(self.encounters)

    def meets_criteria(self, criteria: dict) -> bool:
        """Return True if the patient satisfies all values in the criteria dict."""
        for key, value in criteria.items():
            if key == "min_age" and self.age < value:
                return False
            if key == "max_age" and self.age > value:
                return False
            if key == "gender" and (
                self.gender.lower() not in {v.lower() for v in value}
                if isinstance(value, set)
                else self.gender.lower() != value.lower()
            ):
                return False
            if key == "bmi_threshold" and self.bmi < value:
                return False
            if key == "a1c_threshold" and (self.a1c is None or self.a1c < value):
                return False
            if key == "smoking" and self.smoking != value:
                return False
        return True

    def __repr__(self) -> str:
        return f"[Patient: {self.patient_id}, age={self.age}, gender={self.gender}]"
