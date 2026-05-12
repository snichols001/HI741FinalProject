"""
HI 741 – Final Project
11 May 2026
Steven Nichols

data_store.py

DataStore class – in-memory store for all clinical data; provides CRUD and file persistence.
"""

import csv
import os
import random
import string

from patient import Patient
from encounter import Encounter
from note import ClinicalNote
from user import User
from data_loader import load_all, load_credentials, load_notes


class DataStore:
    """Central in-memory store for all clinical data loaded from CSV files."""

    def __init__(self, data_dir: str):
        self.data_dir    = data_dir
        self.patients    = {}
        self.encounters  = {}
        self.procedures  = {}
        self.providers   = {}
        self.departments = {}
        self.notes       = {}
        self._credentials: dict[str, tuple[str, str]] = {}

    def load(self) -> None:
        """Load all tables from CSV files in data_dir."""
        self._credentials = load_credentials(os.path.join(self.data_dir, "credentials.csv"))
        self.patients, self.providers, self.departments, self.encounters, self.procedures = \
            load_all(self.data_dir)
        self.notes = load_notes(os.path.join(self.data_dir, "notes.csv"))

    def authenticate(self, username: str, password: str) -> User | None:
        """Return a User if credentials match, or None on failure."""
        entry = self._credentials.get(username.strip())
        if entry is None:
            return None
        stored_password, role = entry
        if password.strip() == stored_password:
            return User(username.strip(), role)
        return None

    def get_patient(self, patient_id: str) -> Patient | None:
        """Return the Patient for the given ID, or None if not found."""
        return self.patients.get(patient_id.strip())

    def add_patient(self, patient: Patient, encounter: Encounter) -> None:
        """Add a new patient, or link a new encounter to an existing patient."""
        if patient.patient_id not in self.patients:
            self.patients[patient.patient_id] = patient
        self.encounters[encounter.encounter_id] = encounter
        self.patients[patient.patient_id].add_encounter(encounter)
        if encounter.provider_id in self.providers:
            self.providers[encounter.provider_id].add_encounter(encounter)
        if encounter.department_id in self.departments:
            self.departments[encounter.department_id].add_encounter(encounter)

    def remove_patient(self, patient_id: str) -> bool:
        """Remove all records for a patient. Return True if found and removed."""
        patient = self.patients.get(patient_id)
        if patient is None:
            return False
        enc_ids = [e.encounter_id for e in patient.encounters]
        for eid in enc_ids:
            enc = self.encounters.pop(eid, None)
            if enc:
                # Remove from the provider's and department's encounter lists
                if enc.provider_id in self.providers:
                    self.providers[enc.provider_id].encounters = [
                        e for e in self.providers[enc.provider_id].encounters
                        if e.encounter_id != eid
                    ]
                if enc.department_id in self.departments:
                    self.departments[enc.department_id].encounters = [
                        e for e in self.departments[enc.department_id].encounters
                        if e.encounter_id != eid
                    ]
        self.notes = {nid: n for nid, n in self.notes.items()
                      if n.patient_id != patient_id}
        del self.patients[patient_id]
        return True

    def get_most_recent_encounter(self, patient_id: str) -> Encounter | None:
        """Return the most recent encounter for a patient, or None."""
        patient = self.patients.get(patient_id)
        if not patient or not patient.encounters:
            return None
        return max(patient.encounters, key=lambda e: e.encounter_date)

    def get_notes(self, patient_id: str, note_date: str) -> list[ClinicalNote]:
        """Return all notes for a patient on a given date."""
        return [
            n for n in self.notes.values()
            if n.patient_id == patient_id and n.note_date == note_date
        ]

    def count_visits_on_date(self, date_str: str) -> int:
        """Return the total number of encounters on a specific date."""
        return sum(1 for e in self.encounters.values() if e.encounter_date == date_str)

    def generate_encounter_id(self) -> str:
        """Return a randomly generated encounter ID not already in use."""
        while True:
            eid = "E" + "".join(random.choices(string.digits, k=5))
            if eid not in self.encounters:
                return eid

    def save_patients(self, path: str) -> None:
        """Write the current patient records back to a CSV file."""
        fieldnames = ["patient_id", "age", "gender", "bmi", "a1c",
                      "bp_sys", "bp_dia", "smoking"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in self.patients.values():
                writer.writerow({
                    "patient_id": p.patient_id,
                    "age":        p.age,
                    "gender":     p.gender,
                    "bmi":        p.bmi,
                    "a1c":        p.a1c if p.a1c is not None else "",
                    "bp_sys":     p.bp_sys,
                    "bp_dia":     p.bp_dia,
                    "smoking":    p.smoking,
                })
