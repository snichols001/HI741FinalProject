"""
HI 741 – Final Project
11 May 2026
Steven Nichols

procedure.py

Procedure class – a single billed procedure performed during an encounter.
"""


class Procedure:
    """Represents one medical procedure with a billing code and cost."""

    def __init__(self, procedure_id: str, encounter_id: str, patient_id: str,
                 procedure_code: str, procedure_name: str, cost: float):
        self.procedure_id   = procedure_id
        self.encounter_id   = encounter_id
        self.patient_id     = patient_id
        self.procedure_code = procedure_code
        self.procedure_name = procedure_name
        self.cost           = cost

    def __repr__(self) -> str:
        return f"[Procedure: {self.procedure_id}, {self.procedure_name}, ${self.cost:.2f}]"
