# ui/report_dialog.py

from collections import Counter
from typing import Dict, List

from PyQt5.QtWidgets import QDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models import Task


class ReportDialog(QDialog):
    """Simple bar chart: number of tasks per category."""
    def __init__(self, parent, tasks: List[Task], cat_lookup: Dict[int, str]):
        super().__init__(parent)
        self.setWindowTitle("Task Report")

        layout = QVBoxLayout(self)

        # Build counts per category
        counts = Counter()
        for t in tasks:
            label = cat_lookup.get(t.category_id or -1, "(No category)")
            counts[label] += 1

        labels = list(counts.keys()) or ["(No tasks)"]
        values = [counts[l] for l in labels] if counts else [0]

        # Matplotlib figure
        fig = Figure(figsize=(5, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.bar(range(len(labels)), values)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Number of tasks")
        ax.set_title("Tasks per Category")

        layout.addWidget(canvas)
        fig.tight_layout()
