"""
HI 741 – Final Project
11 May 2026
Steven Nichols

encounter.py

Encounter class – a single clinical visit with linked procedures.
"""


class Encounter:
    """Represents one clinical encounter (visit) in the data system."""

    def __init__(self, encounter_id: str, patient_id: str, provider_id: str,
                 department_id: str, encounter_date: str, encounter_type: str):
        self.encounter_id   = encounter_id
        self.patient_id     = patient_id
        self.provider_id    = provider_id
        self.department_id  = department_id
        self.encounter_date = encounter_date    # "YYYY-MM-DD"
        self.encounter_type = encounter_type    # "Outpatient", "Inpatient", "Emergency"
        self.procedures     = []

    def add_procedure(self, procedure) -> None:
        """Link a Procedure object to this encounter."""
        self.procedures.append(procedure)

    def __repr__(self) -> str:
        return (f"[Encounter: {self.encounter_id}, "
                f"patient={self.patient_id}, date={self.encounter_date}]")
