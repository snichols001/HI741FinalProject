"""
HI 741 – Final Project
May 2026
Steven Nichols

app.py

Tkinter UI application – login frame, menu frame, and all action dialogs.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib

# Backend must be set before importing matplotlib submodules; imports that
# follow are intentionally placed here to satisfy that constraint.
matplotlib.use("TkAgg")
# pylint: disable=wrong-import-position
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from patient import Patient
from encounter import Encounter
from data_store import DataStore
from usage_logger import UsageLogger
from user import User
from analytics import (
    monitor_provider_workload,
    department_revenue,
    key_statistics,
)
# pylint: enable=wrong-import-position

# Maps action keys → button label and App method name
_ACTION_LABELS: dict[str, str] = {
    "retrieve_patient":        "Retrieve Patient",
    "add_patient":             "Add Patient",
    "remove_patient":          "Remove Patient",
    "count_visits":            "Count Visits",
    "view_note":               "View Note",
    "generate_key_statistics": "Generate Key Statistics",
    "monitor_revenue":         "Monitor Revenue",
    "monitor_workload":        "Monitor Workload",
}

_ACTION_HANDLERS: dict[str, str] = {
    "retrieve_patient":        "open_retrieve_patient",
    "add_patient":             "open_add_patient",
    "remove_patient":          "open_remove_patient",
    "count_visits":            "open_count_visits",
    "view_note":               "open_view_note",
    "generate_key_statistics": "open_key_statistics",
    "monitor_revenue":         "open_monitor_revenue",
    "monitor_workload":        "open_monitor_workload",
}

_BG      = "#f0f4f8"
_BLUE    = "#2563eb"
_GREEN   = "#16a34a"
_RED     = "#dc2626"
# macOS Aqua overrides button backgrounds to light grey, making white text invisible
_BTN_FG  = "black" if sys.platform == "darwin" else "white"
# Explicit entry colors ensure readability regardless of system dark/light mode
_ENTRY_BG = "white"
_ENTRY_FG = "black"


# ── Login Frame ───────────────────────────────────────────────────────────────

class LoginFrame(tk.Frame):
    """Login screen prompting for username and password."""

    def __init__(self, parent: tk.Widget, app: "App"):
        super().__init__(parent, bg=_BG)
        self.app = app
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Clinical Data Warehouse",
                 font=("Helvetica", 18, "bold"), bg=_BG).pack(pady=(40, 6))
        tk.Label(self, text="Please log in to continue.",
                 font=("Helvetica", 11), bg=_BG, fg="#555").pack(pady=(0, 20))

        form = tk.Frame(self, bg=_BG)
        form.pack()

        tk.Label(form, text="Username:", bg=_BG).grid(row=0, column=0, sticky="e", padx=10, pady=6)
        self._username = ttk.Entry(form, width=24)
        self._username.grid(row=0, column=1, padx=10, pady=6)

        tk.Label(form, text="Password:", bg=_BG).grid(row=1, column=0, sticky="e", padx=10, pady=6)
        self._password = ttk.Entry(form, show="*", width=24)
        self._password.grid(row=1, column=1, padx=10, pady=6)

        self._error_label = tk.Label(self, text="", fg=_RED, bg=_BG)
        self._error_label.pack(pady=4)

        tk.Button(self, text="Log In", width=18, command=self._submit,
                  bg=_BLUE, fg=_BTN_FG, relief="flat", pady=6).pack(pady=6)

        self._username.bind("<Return>", lambda _: self._password.focus())
        self._password.bind("<Return>", lambda _: self._submit())

    def _submit(self) -> None:
        username = self._username.get().strip()
        password = self._password.get().strip()
        if not username or not password:
            self._error_label.config(text="Please enter both username and password.")
            return
        if not self.app.handle_login(username, password):
            self._error_label.config(text="Invalid username or password.")
            self._password.delete(0, tk.END)

    def reset(self) -> None:
        """Clear all fields and error text."""
        self._username.delete(0, tk.END)
        self._password.delete(0, tk.END)
        self._error_label.config(text="")
        self._username.focus()


# ── Menu Frame ────────────────────────────────────────────────────────────────

class MenuFrame(tk.Frame):
    """Role-based action menu displayed after a successful login."""

    def __init__(self, parent: tk.Widget, app: "App"):
        super().__init__(parent, bg=_BG)
        self.app = app

    def refresh(self, user: User) -> None:
        """Rebuild the button list for the given user's role."""
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Clinical Data Warehouse",
                 font=("Helvetica", 16, "bold"), bg=_BG).pack(pady=(30, 4))
        tk.Label(self, text=f"Logged in as: {user.username}  |  Role: {user.role}",
                 font=("Helvetica", 10), bg=_BG, fg="#555").pack(pady=(0, 22))

        btn_frame = tk.Frame(self, bg=_BG)
        btn_frame.pack()

        for action in user.allowed_actions():
            label        = _ACTION_LABELS.get(action, action)
            handler_name = _ACTION_HANDLERS.get(action, "")
            cmd          = getattr(self.app, handler_name, None)
            tk.Button(btn_frame, text=label, width=30, pady=6,
                      bg=_BLUE, fg=_BTN_FG, relief="flat",
                      command=cmd).pack(pady=4)

        tk.Button(btn_frame, text="Exit", width=30, pady=6,
                  bg=_RED, fg=_BTN_FG, relief="flat",
                  command=self.app.handle_exit).pack(pady=(20, 4))


# ── Base Dialog ───────────────────────────────────────────────────────────────

class _BaseDialog(tk.Toplevel):
    """Common layout helpers shared by all action dialogs."""

    def __init__(self, parent: tk.Widget, title: str, width: int = 480, height: int = 380):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=_BG)
        self._center(width, height)
        self.grab_set()

    def _center(self, width: int, height: int) -> None:
        """Position the dialog in the center of the screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - width)  // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _label_entry(self, parent: tk.Widget, label: str, row: int,
                     show: str = "") -> ttk.Entry:
        """Add a label-entry row to a grid frame and return the Entry widget."""
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=8, pady=4)
        entry = ttk.Entry(parent, width=22, show=show)
        entry.grid(row=row, column=1, padx=8, pady=4, sticky="w")
        return entry

    def _make_feedback(self, parent: tk.Widget) -> tk.Label:
        """Create and return a label used to display success or error messages."""
        label = tk.Label(parent, text="", wraplength=420, bg=_BG)
        label.pack(pady=4)
        return label

    def _set_feedback(self, label: tk.Label, text: str, ok: bool = True) -> None:
        """Update the feedback label text and color."""
        label.config(text=text, fg=_GREEN if ok else _RED)


# ── Retrieve Patient ──────────────────────────────────────────────────────────

class RetrievePatientDialog(_BaseDialog):
    """Prompt for a patient ID and display the most recent encounter."""

    def __init__(self, parent: tk.Widget, data_store: DataStore):
        super().__init__(parent, "Retrieve Patient", width=520, height=430)
        self.data_store = data_store
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Retrieve Patient",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=12)

        search_row = tk.Frame(self, bg=_BG)
        search_row.pack()
        self._pid = self._label_entry(search_row, "Patient ID:", 0)
        tk.Button(search_row, text="Search", command=self._search,
                  bg=_BLUE, fg=_BTN_FG, relief="flat").grid(row=0, column=2, padx=6)

        self._result = tk.Text(self, height=14, width=58, state="disabled", bg=_ENTRY_BG, fg=_ENTRY_FG,
                               font=("Courier", 10), relief="groove", bd=2)
        self._result.pack(pady=8, padx=12)
        self._fb = self._make_feedback(self)

    def _search(self) -> None:
        pid = self._pid.get().strip()
        if not pid:
            self._set_feedback(self._fb, "Please enter a Patient ID.", ok=False)
            return
        patient = self.data_store.get_patient(pid)
        if patient is None:
            self._set_feedback(self._fb, f"Patient '{pid}' not found.", ok=False)
            return
        enc = self.data_store.get_most_recent_encounter(pid)
        lines = [
            f"Patient ID  : {patient.patient_id}",
            f"Age         : {patient.age}",
            f"Gender      : {patient.gender}",
            f"BMI         : {patient.bmi}",
            f"A1C         : {patient.a1c if patient.a1c is not None else 'N/A'}",
            f"BP (sys/dia): {patient.bp_sys} / {patient.bp_dia}",
            f"Smoker      : {'Yes' if patient.smoking else 'No'}",
            "",
        ]
        if enc:
            lines += [
                "── Most Recent Encounter ──────────────────",
                f"Encounter ID: {enc.encounter_id}",
                f"Date        : {enc.encounter_date}",
                f"Type        : {enc.encounter_type}",
                f"Provider    : {enc.provider_id or 'N/A'}",
                f"Department  : {enc.department_id or 'N/A'}",
            ]
        else:
            lines.append("No encounters on record.")
        self._result.config(state="normal")
        self._result.delete("1.0", tk.END)
        self._result.insert(tk.END, "\n".join(lines))
        self._result.config(state="disabled")
        self._set_feedback(self._fb, "Patient found.", ok=True)


# ── Add Patient ───────────────────────────────────────────────────────────────

class AddPatientDialog(_BaseDialog):
    """Form to add a new patient or a new encounter for an existing patient."""

    def __init__(self, parent: tk.Widget, data_store: DataStore, patients_path: str):
        super().__init__(parent, "Add Patient", width=490, height=120)
        self.data_store    = data_store
        self.patients_path = patients_path
        self._patient_exists = False
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Add Patient",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=10)

        id_row = tk.Frame(self, bg=_BG)
        id_row.pack()
        self._pid = self._label_entry(id_row, "Patient ID:", 0)
        tk.Button(id_row, text="Check", command=self._check_id,
                  bg=_BLUE, fg=_BTN_FG, relief="flat").grid(row=0, column=2, padx=6)

        self._status = tk.Label(self, text="", fg=_BLUE, bg=_BG)
        self._status.pack(pady=2)

        # Demographics section – shown only for new patients
        self._demo_frame = tk.LabelFrame(self, text="Patient Demographics",
                                         bg=_BG, padx=8, pady=6)
        demo = tk.Frame(self._demo_frame, bg=_BG)
        demo.pack()
        self._age    = self._label_entry(demo, "Age:", 0)
        tk.Label(demo, text="Gender:", bg=_BG).grid(row=1, column=0, sticky="e", padx=8, pady=4)
        self._gender = ttk.Combobox(demo, values=["Male", "Female", "Non-binary"],
                                    width=20, state="readonly")
        self._gender.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        self._bmi    = self._label_entry(demo, "BMI:", 2)
        self._a1c    = self._label_entry(demo, "A1C (optional):", 3)
        self._bp_sys = self._label_entry(demo, "Systolic BP:", 4)
        self._bp_dia = self._label_entry(demo, "Diastolic BP:", 5)
        tk.Label(demo, text="Smoker:", bg=_BG).grid(row=6, column=0, sticky="e", padx=8, pady=4)
        self._smoking = tk.BooleanVar()
        tk.Checkbutton(demo, variable=self._smoking, bg=_BG).grid(
            row=6, column=1, sticky="w", padx=8)

        # Encounter section – shown after patient ID is checked
        self._enc_frame = tk.LabelFrame(self, text="Encounter", bg=_BG, padx=8, pady=6)
        enc = tk.Frame(self._enc_frame, bg=_BG)
        enc.pack()
        self._enc_date = self._label_entry(enc, "Date (YYYY-MM-DD):", 0)
        tk.Label(enc, text="Type:", bg=_BG).grid(row=1, column=0, sticky="e", padx=8, pady=4)
        self._enc_type = ttk.Combobox(enc, values=["Outpatient", "Inpatient", "Emergency"],
                                      width=20, state="readonly")
        self._enc_type.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        self._submit_btn = tk.Button(self, text="Submit", state="disabled",
                                     command=self._submit,
                                     bg=_GREEN, fg=_BTN_FG, relief="flat", pady=4)
        self._submit_btn.pack(pady=8)
        self._fb = self._make_feedback(self)

    def _check_id(self) -> None:
        pid = self._pid.get().strip()
        if not pid:
            self._status.config(text="Please enter a Patient ID.", fg=_RED)
            return
        if self.data_store.get_patient(pid):
            self._patient_exists = True
            self._status.config(text=f"Patient {pid} found – adding new encounter.", fg=_BLUE)
            self._demo_frame.pack_forget()
        else:
            self._patient_exists = False
            self._status.config(text="New patient – please fill in demographics.", fg=_BLUE)
            self._demo_frame.pack(padx=12, pady=4, fill="x")
        self._enc_frame.pack(padx=12, pady=4, fill="x")
        self._submit_btn.config(state="normal")
        # Resize window to fit the revealed fields
        self.update_idletasks()
        self.geometry(f"490x{self.winfo_reqheight() + 20}")

    def _submit(self) -> None:
        pid      = self._pid.get().strip()
        enc_date = self._enc_date.get().strip()
        enc_type = self._enc_type.get()

        if not enc_date or not enc_type:
            self._set_feedback(self._fb, "Please fill in all encounter fields.", ok=False)
            return
        try:
            datetime.strptime(enc_date, "%Y-%m-%d")
        except ValueError:
            self._set_feedback(self._fb, "Invalid date. Use YYYY-MM-DD.", ok=False)
            return

        if not self._patient_exists:
            try:
                age    = int(self._age.get().strip())
                bmi    = float(self._bmi.get().strip())
                a1c_s  = self._a1c.get().strip()
                a1c    = float(a1c_s) if a1c_s else None
                bp_sys = int(self._bp_sys.get().strip())
                bp_dia = int(self._bp_dia.get().strip())
            except ValueError:
                self._set_feedback(self._fb, "Invalid numeric values in demographics.", ok=False)
                return
            gender  = self._gender.get()
            smoking = self._smoking.get()
            if not gender:
                self._set_feedback(self._fb, "Please select a gender.", ok=False)
                return
            patient = Patient(pid, age, gender, bmi, a1c, bp_sys, bp_dia, smoking)
        else:
            patient = self.data_store.get_patient(pid)

        enc_id    = self.data_store.generate_encounter_id()
        encounter = Encounter(
            encounter_id=enc_id,
            patient_id=pid,
            provider_id="",
            department_id="",
            encounter_date=enc_date,
            encounter_type=enc_type
        )
        self.data_store.add_patient(patient, encounter)
        self.data_store.save_patients(self.patients_path)
        self._set_feedback(self._fb, f"Saved. Encounter ID: {enc_id}", ok=True)


# ── Remove Patient ────────────────────────────────────────────────────────────

class RemovePatientDialog(_BaseDialog):
    """Prompt for a patient ID and remove all associated records after confirmation."""

    def __init__(self, parent: tk.Widget, data_store: DataStore, patients_path: str):
        super().__init__(parent, "Remove Patient", width=420, height=220)
        self.data_store    = data_store
        self.patients_path = patients_path
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Remove Patient",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=16)

        row = tk.Frame(self, bg=_BG)
        row.pack()
        self._pid = self._label_entry(row, "Patient ID:", 0)
        tk.Button(row, text="Remove", command=self._remove,
                  bg=_RED, fg=_BTN_FG, relief="flat").grid(row=0, column=2, padx=6)

        self._fb = self._make_feedback(self)

    def _remove(self) -> None:
        pid = self._pid.get().strip()
        if not pid:
            self._set_feedback(self._fb, "Please enter a Patient ID.", ok=False)
            return
        if not self.data_store.get_patient(pid):
            self._set_feedback(self._fb, f"Patient '{pid}' not found.", ok=False)
            return
        confirmed = messagebox.askyesno(
            "Confirm Removal",
            f"Remove ALL records for patient '{pid}'?\nThis cannot be undone.",
            parent=self
        )
        if not confirmed:
            return
        self.data_store.remove_patient(pid)
        self.data_store.save_patients(self.patients_path)
        self._pid.delete(0, tk.END)
        self._set_feedback(self._fb, f"Patient '{pid}' removed.", ok=True)


# ── View Note ─────────────────────────────────────────────────────────────────

class ViewNoteDialog(_BaseDialog):
    """Prompt for patient ID and date, then display matching clinical notes."""

    def __init__(self, parent: tk.Widget, data_store: DataStore):
        super().__init__(parent, "View Note", width=540, height=450)
        self.data_store = data_store
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="View Clinical Note",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=10)

        inputs = tk.Frame(self, bg=_BG)
        inputs.pack()
        self._pid  = self._label_entry(inputs, "Patient ID:", 0)
        self._date = self._label_entry(inputs, "Date (YYYY-MM-DD):", 1)
        tk.Button(inputs, text="Search", command=self._search,
                  bg=_BLUE, fg=_BTN_FG, relief="flat").grid(
                  row=2, column=1, pady=8, sticky="e", padx=8)

        self._result = tk.Text(self, height=14, width=62, state="disabled", bg=_ENTRY_BG, fg=_ENTRY_FG,
                               font=("Courier", 10), relief="groove", bd=2)
        self._result.pack(pady=6, padx=12)
        self._fb = self._make_feedback(self)

    def _search(self) -> None:
        pid  = self._pid.get().strip()
        date = self._date.get().strip()
        if not pid or not date:
            self._set_feedback(self._fb, "Please enter both a Patient ID and a date.", ok=False)
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            self._set_feedback(self._fb, "Invalid date format. Use YYYY-MM-DD.", ok=False)
            return
        notes = self.data_store.get_notes(pid, date)
        self._result.config(state="normal")
        self._result.delete("1.0", tk.END)
        if not notes:
            self._result.insert(tk.END, f"No notes found for patient '{pid}' on {date}.")
            self._set_feedback(self._fb, "No notes found.", ok=False)
        else:
            for i, note in enumerate(notes, start=1):
                self._result.insert(
                    tk.END,
                    f"[{i}]  Note ID: {note.note_id}  |  Type: {note.note_type}\n"
                    f"{note.note_text}\n{'─' * 60}\n"
                )
            self._set_feedback(self._fb, f"{len(notes)} note(s) found.", ok=True)
        self._result.config(state="disabled")


# ── Count Visits ──────────────────────────────────────────────────────────────

class CountVisitsDialog(_BaseDialog):
    """Prompt for a date and display visit counts for that day."""

    def __init__(self, parent: tk.Widget, data_store: DataStore, can_access_phi: bool):
        super().__init__(parent, "Count Visits", width=460, height=400)
        self.data_store     = data_store
        self.can_access_phi = can_access_phi
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Count Visits",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=10)

        row = tk.Frame(self, bg=_BG)
        row.pack()
        self._date = self._label_entry(row, "Date (YYYY-MM-DD):", 0)
        tk.Button(row, text="Count", command=self._count,
                  bg=_BLUE, fg=_BTN_FG, relief="flat").grid(row=0, column=2, padx=6)

        self._result = tk.Text(self, height=13, width=52, state="disabled", bg=_ENTRY_BG, fg=_ENTRY_FG,
                               font=("Courier", 10), relief="groove", bd=2)
        self._result.pack(pady=8, padx=12)
        self._fb = self._make_feedback(self)

    def _count(self) -> None:
        date_str = self._date.get().strip()
        if not date_str:
            self._set_feedback(self._fb, "Please enter a date.", ok=False)
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self._set_feedback(self._fb, "Invalid date format. Use YYYY-MM-DD.", ok=False)
            return

        total = self.data_store.count_visits_on_date(date_str)
        dept_counts = {
            dept.name: sum(1 for e in dept.encounters if e.encounter_date == date_str)
            for dept in self.data_store.departments.values()
        }

        lines = [f"Total visits on {date_str}: {total}", "", "By Department:"]
        for dept_name, count in dept_counts.items():
            lines.append(f"  {dept_name}: {count}")

        if self.can_access_phi:
            pat_counts = {
                pid: sum(1 for e in p.encounters if e.encounter_date == date_str)
                for pid, p in self.data_store.patients.items()
                if any(e.encounter_date == date_str for e in p.encounters)
            }
            lines += ["", "By Patient:"]
            for pid, count in sorted(pat_counts.items()):
                lines.append(f"  {pid}: {count}")

        self._result.config(state="normal")
        self._result.delete("1.0", tk.END)
        self._result.insert(tk.END, "\n".join(lines))
        self._result.config(state="disabled")
        self._set_feedback(self._fb, "Done.", ok=True)


# ── Key Statistics ────────────────────────────────────────────────────────────

class KeyStatisticsDialog(_BaseDialog):
    """Generate and display summary charts for patient and encounter data."""

    def __init__(self, parent: tk.Widget, data_store: DataStore):
        super().__init__(parent, "Key Statistics", width=720, height=540)
        self.data_store = data_store
        self._build()

    def _build(self) -> None:
        stats = key_statistics(self.data_store.patients, self.data_store.encounters)

        tk.Label(self, text="Key Statistics",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=8)
        tk.Label(self, bg=_BG, text=(
            f"Total patients: {stats['patient_count']}   "
            f"Total encounters: {stats['encounter_count']}"
        ), font=("Helvetica", 10)).pack()

        fig = Figure(figsize=(7.0, 4.2), dpi=95)

        ax1 = fig.add_subplot(2, 2, 1)
        ax1.hist(stats["ages"], bins=12, color=_BLUE, edgecolor="white")
        ax1.set_title("Age Distribution", fontsize=9)
        ax1.set_xlabel("Age", fontsize=8)
        ax1.set_ylabel("Count", fontsize=8)
        ax1.tick_params(labelsize=7)

        ax2 = fig.add_subplot(2, 2, 2)
        genders = stats["genders"]
        ax2.pie(genders.values(), labels=genders.keys(), autopct="%1.0f%%",
                textprops={"fontsize": 7})
        ax2.set_title("Gender Distribution", fontsize=9)

        ax3 = fig.add_subplot(2, 2, 3)
        ax3.hist(stats["bmis"], bins=12, color=_GREEN, edgecolor="white")
        ax3.set_title("BMI Distribution", fontsize=9)
        ax3.set_xlabel("BMI", fontsize=8)
        ax3.set_ylabel("Count", fontsize=8)
        ax3.tick_params(labelsize=7)

        ax4 = fig.add_subplot(2, 2, 4)
        enc_types = stats["encounter_types"]
        ax4.bar(enc_types.keys(), enc_types.values(), color="#7c3aed", edgecolor="white")
        ax4.set_title("Encounter Types", fontsize=9)
        ax4.tick_params(labelsize=7)

        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=6)


# ── Monitor Revenue ───────────────────────────────────────────────────────────

class MonitorRevenueDialog(_BaseDialog):
    """Display total procedure revenue by department in a sortable table."""

    def __init__(self, parent: tk.Widget, data_store: DataStore):
        super().__init__(parent, "Monitor Revenue", width=420, height=300)
        self.data_store = data_store
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Department Revenue",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=12)

        tree = ttk.Treeview(self, columns=("dept", "revenue"), show="headings", height=8)
        tree.heading("dept",    text="Department")
        tree.heading("revenue", text="Total Revenue ($)")
        tree.column("dept",    width=210, anchor="w")
        tree.column("revenue", width=160, anchor="e")
        tree.pack(padx=16, pady=8, fill="both", expand=True)

        revenue = department_revenue(self.data_store.departments)
        for dept_name, total in sorted(revenue.items(), key=lambda x: -x[1]):
            tree.insert("", tk.END, values=(dept_name, f"{total:,.2f}"))


# ── Monitor Workload ──────────────────────────────────────────────────────────

class MonitorWorkloadDialog(_BaseDialog):
    """Display all providers ranked by encounter count."""

    def __init__(self, parent: tk.Widget, data_store: DataStore):
        super().__init__(parent, "Monitor Workload", width=450, height=400)
        self.data_store = data_store
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Provider Workload",
                 font=("Helvetica", 13, "bold"), bg=_BG).pack(pady=12)

        frame = tk.Frame(self)
        frame.pack(padx=16, pady=4, fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=("provider", "specialty", "encounters"),
                            show="headings", height=12)
        tree.heading("provider",   text="Provider ID")
        tree.heading("specialty",  text="Specialty")
        tree.heading("encounters", text="Encounters")
        tree.column("provider",   width=100, anchor="w")
        tree.column("specialty",  width=180, anchor="w")
        tree.column("encounters", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        workload = monitor_provider_workload(self.data_store.providers)
        for pid, count in workload.items():
            provider  = self.data_store.providers.get(pid)
            specialty = provider.specialty if provider else ""
            tree.insert("", tk.END, values=(pid, specialty, count))


# ── Main Application ──────────────────────────────────────────────────────────

class App(tk.Tk):
    """Main Tkinter application – manages frame switching and dispatches all user actions."""

    def __init__(self, data_store: DataStore, logger: UsageLogger,
                 data_dir: str, output_dir: str):
        super().__init__()
        self.data_store     = data_store
        self.logger         = logger
        self.data_dir       = data_dir
        self.output_dir     = output_dir
        self.current_user: User | None = None
        self._patients_path = os.path.join(data_dir, "patients.csv")
        self._build()

    def _build(self) -> None:
        self.title("Clinical Data Warehouse")
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(bg=_BG)

        # Force black text on all tk widgets so macOS dark mode cannot make labels invisible
        self.option_add("*foreground", "black")
        self.option_add("*background", _BG)

        # Force a cross-platform theme so macOS dark mode cannot override widget colors
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TEntry",    fieldbackground="white", foreground="black",
                        selectbackground=_BLUE, selectforeground="white")
        style.configure("TCombobox", fieldbackground="white", foreground="black",
                        selectbackground=_BLUE, selectforeground="white")
        style.map("TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("Treeview",         background="white", foreground="black",
                        fieldbackground="white")
        style.configure("Treeview.Heading", background=_BG,    foreground="black")

        container = tk.Frame(self, bg=_BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._frames: dict[str, tk.Frame] = {}
        for FrameClass in (LoginFrame, MenuFrame):
            frame = FrameClass(container, self)
            self._frames[FrameClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self._show("LoginFrame")

    def _show(self, name: str) -> None:
        """Bring the named frame to the front."""
        self._frames[name].tkraise()

    # ── Auth ──────────────────────────────────────────────────────────────────

    def handle_login(self, username: str, password: str) -> bool:
        """Authenticate the user and switch to the menu on success."""
        user = self.data_store.authenticate(username, password)
        if user is None:
            self.logger.log_event(username, "", "login_failed", False)
            return False
        self.current_user = user
        self.logger.log_event(username, user.role, "login", True)
        self._frames["MenuFrame"].refresh(user)
        self._show("MenuFrame")
        return True

    def handle_exit(self) -> None:
        """Log the exit event and terminate the application."""
        if self.current_user:
            self.logger.log_event(
                self.current_user.username, self.current_user.role, "exit", True
            )
        self.destroy()

    # ── Action dispatchers ────────────────────────────────────────────────────

    def open_retrieve_patient(self) -> None:
        """Open the retrieve patient dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "retrieve_patient", True)
        RetrievePatientDialog(self, self.data_store)

    def open_add_patient(self) -> None:
        """Open the add patient dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "add_patient", True)
        AddPatientDialog(self, self.data_store, self._patients_path)

    def open_remove_patient(self) -> None:
        """Open the remove patient dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "remove_patient", True)
        RemovePatientDialog(self, self.data_store, self._patients_path)

    def open_view_note(self) -> None:
        """Open the view note dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "view_note", True)
        ViewNoteDialog(self, self.data_store)

    def open_count_visits(self) -> None:
        """Open the count visits dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "count_visits", True)
        CountVisitsDialog(self, self.data_store, self.current_user.can_access_phi())

    def open_key_statistics(self) -> None:
        """Open the key statistics chart dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "generate_key_statistics", True)
        KeyStatisticsDialog(self, self.data_store)

    def open_monitor_revenue(self) -> None:
        """Open the department revenue dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "monitor_revenue", True)
        MonitorRevenueDialog(self, self.data_store)

    def open_monitor_workload(self) -> None:
        """Open the provider workload dialog."""
        self.logger.log_event(self.current_user.username, self.current_user.role,
                              "monitor_workload", True)
        MonitorWorkloadDialog(self, self.data_store)
