"""
Modal dialog to collect Task info (title, description, priority, category, due date).
"""

from datetime import date
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QDialogButtonBox, QDateEdit
)
from PyQt5.QtCore import QDate

class TaskEditorDialog(QDialog):
    """Simple pop-up form for creating a new task."""
    def __init__(self, parent, categories: list[tuple[int, str]]):
        super().__init__(parent)
        self.setWindowTitle("Add Task")

        # --- form widgets ---
        self.title = QLineEdit()
        self.desc = QTextEdit()
        self.priority = QComboBox()
        self.priority.addItems(["Low", "Medium", "High"])

        # Category dropdown with a (None) option
        self.category = QComboBox()
        self.category.addItem("(None)", -1)
        for cid, name in categories:
            self.category.addItem(name, cid)

        # Date picker defaults to today
        self.due = QDateEdit()
        self.due.setCalendarPopup(True)
        self.due.setDate(QDate.currentDate())

        # --- layout ---
        form = [
            ("Title", self.title),
            ("Description", self.desc),
            ("Priority", self.priority),
            ("Category", self.category),
            ("Due Date", self.due),
        ]
        layout = QVBoxLayout(self)
        for label, widget in form:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(widget)
            layout.addLayout(row)

        # OK / Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        """Return the filled-in values as a dict."""
        title = self.title.text().strip()
        desc = self.desc.toPlainText().strip()
        prio = self.priority.currentText()
        cid = self.category.currentData()
        cid = None if cid == -1 else cid
        qd = self.due.date()
        due = date(qd.year(), qd.month(), qd.day())
        return dict(title=title, description=desc, priority=prio, category_id=cid, due_date=due)
