"""
HI 741 – Final Project
11 May 2026
Steven Nichols

note.py

ClinicalNote class – a single clinical note linked to a patient encounter.
"""


class ClinicalNote:
    """A single clinical note for a patient encounter."""

    def __init__(self, note_id: str, patient_id: str, encounter_id: str,
                 note_date: str, note_type: str, note_text: str):
        self.note_id      = note_id
        self.patient_id   = patient_id
        self.encounter_id = encounter_id
        self.note_date    = note_date       # "YYYY-MM-DD"
        self.note_type    = note_type
        self.note_text    = note_text

    def __repr__(self) -> str:
        return f"[Note: {self.note_id}, patient={self.patient_id}, date={self.note_date}]"
