"""
Read-only table model for tasks.
Shows: ✓, Title, Description, Category, Due Date, Priority
"""

from typing import List, Dict
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from models import Task

COLUMNS = ["✓", "Title", "Description", "Category", "Due Date", "Priority"]


class TaskTableModel(QAbstractTableModel):
    def __init__(self, tasks: List[Task], cat_lookup: Dict[int, str]):
        super().__init__()
        self.tasks = tasks              # list of Task objects
        self.cat_lookup = cat_lookup    # {category_id: name}

    def set_data(self, tasks: List[Task], cat_lookup: Dict[int, str]):
        """Replace all data and notify the view."""
        self.beginResetModel()
        self.tasks = tasks
        self.cat_lookup = cat_lookup
        self.endResetModel()



    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.tasks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return COLUMNS[section]
        return section + 1  # row numbers

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        t = self.tasks[index.row()]
        col = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            # ✓ column
            if col == 0:
                return "✓" if t.status == "Done" else ""

            # Title
            if col == 1:
                return t.title or ""


            if col == 2:
                desc = t.description or ""

                return desc

            # Category name
            if col == 3:
                return self.cat_lookup.get(t.category_id or -1, "")

            # Due Date
            if col == 4:
                return t.due_date.isoformat() if t.due_date else ""

            # Priority
            if col == 5:
                return t.priority or ""

        # center the checkmark column
        if role == Qt.TextAlignmentRole and col == 0:
            return Qt.AlignCenter

        return QVariant()


    def task_at(self, row: int) -> Task:
        return self.tasks[row]
