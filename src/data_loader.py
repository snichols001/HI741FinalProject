"""
HI 741 – Final Project
11 May 2026
Steven Nichols

data_loader.py

Functions for loading and parsing all clinical data CSV files.
"""

import csv
import os

from patient import Patient
from provider import Provider
from department import Department
from encounter import Encounter
from procedure import Procedure
from note import ClinicalNote


# Private helpers

def _parse_int(value: str, field_name: str, row_num: int) -> int | None:
    value = value.strip()
    if not value:
        print(f"Warning: Row {row_num} skipped – missing {field_name}")
        return None
    try:
        return int(value)
    except ValueError:
        print(f"Warning: Row {row_num} skipped – {field_name} not a valid integer: '{value}'")
        return None


def _parse_float(value: str, field_name: str, row_num: int) -> float | None:
    value = value.strip()
    if not value:
        return None     # float fields such as a1c may be legitimately empty
    try:
        return float(value)
    except ValueError:
        print(f"Warning: Row {row_num} skipped – {field_name} not a valid number: '{value}'")
        return None


def _parse_bool(value: str, field_name: str, row_num: int) -> bool | None:
    mapping = {"true": True, "false": False}
    v = value.strip().lower()
    if v not in mapping:
        print(f"Warning: Row {row_num} skipped – {field_name} must be true/false, got '{value}'")
        return None
    return mapping[v]


def _open_csv(path: str):
    """Open a CSV file for reading, or return None if the file is missing."""
    if not os.path.exists(path):
        print(f"Warning: File not found: {path}")
        return None
    return open(path, "r", encoding="utf-8", newline="")


# Loaders

def load_credentials(path: str) -> dict[str, tuple[str, str]]:
    """Load credentials.csv and return a dict mapping username → (password, role)."""
    credentials: dict[str, tuple[str, str]] = {}
    file = _open_csv(path)
    if file is None:
        return credentials
    try:
        reader = csv.DictReader(file)
        for row in reader:
            username = row.get("username", "").strip()
            password = row.get("password", "").strip()
            role     = row.get("role", "").strip()
            if username and password and role:
                credentials[username] = (password, role)
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return credentials


def load_patients(path: str) -> dict[str, Patient]:
    """Load patients.csv and return a dict mapping patient_id → Patient."""
    patients: dict[str, Patient] = {}
    file = _open_csv(path)
    if file is None:
        return patients
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            pid = row.get("patient_id", "").strip()
            if not pid:
                print(f"Warning: Row {row_num} skipped – missing patient_id")
                continue
            age     = _parse_int(row.get("age", ""),    "age",    row_num)
            bmi     = _parse_float(row.get("bmi", ""),  "bmi",    row_num)
            a1c     = _parse_float(row.get("a1c", ""),  "a1c",    row_num)
            bp_sys  = _parse_int(row.get("bp_sys", ""), "bp_sys", row_num)
            bp_dia  = _parse_int(row.get("bp_dia", ""), "bp_dia", row_num)
            smoking = _parse_bool(row.get("smoking", ""), "smoking", row_num)
            # Skip row if any required field failed to parse
            if any(v is None for v in [age, bmi, bp_sys, bp_dia, smoking]):
                continue
            patients[pid] = Patient(
                patient_id=pid,
                age=age,
                gender=row.get("gender", "").strip(),
                bmi=bmi,
                a1c=a1c,
                bp_sys=bp_sys,
                bp_dia=bp_dia,
                smoking=smoking
            )
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return patients


def load_providers(path: str) -> dict[str, Provider]:
    """Load providers.csv and return a dict mapping provider_id → Provider."""
    providers: dict[str, Provider] = {}
    file = _open_csv(path)
    if file is None:
        return providers
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            pid = row.get("provider_id", "").strip()
            if not pid:
                print(f"Warning: Row {row_num} skipped – missing provider_id")
                continue
            providers[pid] = Provider(
                provider_id=pid,
                name=row.get("name", "").strip(),
                specialty=row.get("specialty", "").strip(),
                department_id=row.get("department_id", "").strip()
            )
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return providers


def load_departments(path: str) -> dict[str, Department]:
    """Load departments.csv and return a dict mapping department_id → Department."""
    departments: dict[str, Department] = {}
    file = _open_csv(path)
    if file is None:
        return departments
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            did = row.get("department_id", "").strip()
            if not did:
                print(f"Warning: Row {row_num} skipped – missing department_id")
                continue
            departments[did] = Department(
                department_id=did,
                name=row.get("name", "").strip(),
                location=row.get("location", "").strip()
            )
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return departments


def load_encounters(path: str, patients: dict, providers: dict,
                    departments: dict) -> dict[str, Encounter]:
    """Load encounters.csv, create Encounter objects, and link them to
    the corresponding Patient, Provider, and Department objects."""
    encounters: dict[str, Encounter] = {}
    file = _open_csv(path)
    if file is None:
        return encounters
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            eid = row.get("encounter_id", "").strip()
            if not eid:
                print(f"Warning: Row {row_num} skipped – missing encounter_id")
                continue
            encounter = Encounter(
                encounter_id=eid,
                patient_id=row.get("patient_id", "").strip(),
                provider_id=row.get("provider_id", "").strip(),
                department_id=row.get("department_id", "").strip(),
                encounter_date=row.get("encounter_date", "").strip(),
                encounter_type=row.get("encounter_type", "").strip()
            )
            encounters[eid] = encounter
            # Link encounter to its patient, provider, and department
            if encounter.patient_id in patients:
                patients[encounter.patient_id].add_encounter(encounter)
            if encounter.provider_id in providers:
                providers[encounter.provider_id].add_encounter(encounter)
            if encounter.department_id in departments:
                departments[encounter.department_id].add_encounter(encounter)
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return encounters


def load_procedures(path: str, encounters: dict) -> dict[str, Procedure]:
    """Load procedures.csv, create Procedure objects, and link them to
    the corresponding Encounter objects."""
    procedures: dict[str, Procedure] = {}
    file = _open_csv(path)
    if file is None:
        return procedures
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            proc_id = row.get("procedure_id", "").strip()
            if not proc_id:
                print(f"Warning: Row {row_num} skipped – missing procedure_id")
                continue
            cost = _parse_float(row.get("cost", ""), "cost", row_num)
            if cost is None:
                continue
            procedure = Procedure(
                procedure_id=proc_id,
                encounter_id=row.get("encounter_id", "").strip(),
                patient_id=row.get("patient_id", "").strip(),
                procedure_code=row.get("procedure_code", "").strip(),
                procedure_name=row.get("procedure_name", "").strip(),
                cost=cost
            )
            procedures[proc_id] = procedure
            # Link procedure to its encounter
            if procedure.encounter_id in encounters:
                encounters[procedure.encounter_id].add_procedure(procedure)
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return procedures


def load_notes(path: str) -> dict[str, ClinicalNote]:
    """Load notes.csv and return a dict mapping note_id → ClinicalNote."""
    notes: dict[str, ClinicalNote] = {}
    file = _open_csv(path)
    if file is None:
        return notes
    try:
        reader = csv.DictReader(file)
        for row_num, row in enumerate(reader, start=2):
            nid = row.get("note_id", "").strip()
            if not nid:
                print(f"Warning: Row {row_num} skipped – missing note_id")
                continue
            notes[nid] = ClinicalNote(
                note_id=nid,
                patient_id=row.get("patient_id", "").strip(),
                encounter_id=row.get("encounter_id", "").strip(),
                note_date=row.get("note_date", "").strip(),
                note_type=row.get("note_type", "").strip(),
                note_text=row.get("note_text", "").strip()
            )
    except csv.Error as e:
        print(f"Warning: CSV parsing error in {path}: {e}")
    finally:
        file.close()
    return notes


def load_all(data_dir: str = "./data"):
    """Load all clinical tables from data_dir, link objects across tables,
    and return (patients, providers, departments, encounters, procedures)."""
    departments = load_departments(os.path.join(data_dir, "departments.csv"))
    providers   = load_providers(os.path.join(data_dir, "providers.csv"))
    patients    = load_patients(os.path.join(data_dir, "patients.csv"))
    encounters  = load_encounters(os.path.join(data_dir, "encounters.csv"),
                                  patients, providers, departments)
    procedures  = load_procedures(os.path.join(data_dir, "procedures.csv"), encounters)
    return patients, providers, departments, encounters, procedures
