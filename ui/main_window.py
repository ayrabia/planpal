from PyQt5.QtWidgets import QInputDialog, QMainWindow, QLabel, QToolBar, QAction, QSplitter, QListWidget, QVBoxLayout, \
    QWidget, QTableView
from PyQt5.QtCore import Qt
from storage import Storage
from ui.task_editor import TaskEditorDialog
from ui.task_table import TaskTableModel
from PyQt5.QtWidgets import QHeaderView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlanPal")
        self.resize(900, 600)

        #Storage is created on demand when user clicks the button
        self.db: Storage | None = None
        self.cat_pairs: list[tuple[int, str]] = []  # (id, name)


        #Toolbar with one action: Initialize Data
        tb = QToolBar("Main")
        self.addToolBar(tb)

        self.act_init = QAction("Initialize Data", self)
        self.act_init.setStatusTip("Create the database file and a default user")
        self.act_init.triggered.connect(self.on_init_data)
        tb.addAction(self.act_init)

        self.act_add_cat = QAction("Add Category", self)
        self.act_add_cat.setStatusTip("Create a new category")
        self.act_add_cat.triggered.connect(self.on_add_category)
        tb.addAction(self.act_add_cat)
        # Add Task action
        self.act_add_task = QAction("Add Task", self)
        self.act_add_task.setStatusTip("Create a new task")
        self.act_add_task.triggered.connect(self.on_add_task)
        tb.addAction(self.act_add_task)

        # Edit Task
        self.act_edit_task = QAction("Edit Task", self)
        self.act_edit_task.setStatusTip("Edit selected task")
        self.act_edit_task.triggered.connect(self.on_edit_task)
        tb.addAction(self.act_edit_task)

        # Delete Task
        self.act_delete_task = QAction("Delete Task", self)
        self.act_delete_task.setStatusTip("Delete selected task")
        self.act_delete_task.triggered.connect(self.on_delete_task)
        tb.addAction(self.act_delete_task)
        
        #Status bar feedback
        self.statusBar().showMessage("Ready")

        #---- Body: Splitter with sidebar + placeholder panel
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        #Left: Side bar (All tasks, Today, Categories)
        self.sidebar = QListWidget()
        splitter.addWidget(self.sidebar)
        self.sidebar.setMaximumWidth(240)

        self.sidebar.currentRowChanged.connect(lambda _: self.refresh_table())

        #Right: placeholder panel (Will have the table later)
        right = QWidget()
        r_layout = QVBoxLayout(right)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)

        hdr = self.table.horizontalHeader()
        hdr.setVisible(True)
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)
        hdr.setMinimumSectionSize(80)
        hdr.resizeSection(0, 40)

        hdr.resizeSection(0, 40)

        self.cat_lookup = {}
        self.model = TaskTableModel([], self.cat_lookup)
        self.table.setModel(self.model)
        r_layout.addWidget(self.table)

        self.info = QLabel("Initialize the database, then add category.")
        self.info.setAlignment(Qt.AlignCenter)
        r_layout.addWidget(self.info)

        splitter.addWidget(right)
        splitter.setSizes([260, 740])

        #Initial render
        self._render_sidebar()


    def on_init_data(self):
        """Create DB (if missing) and ensure default user exists"""
        try:
            if self.db is None:
                self.db = Storage()
            self.db.migrate()

            user = self.db.get_or_create_user("default")
            self.statusBar().showMessage(f"Database ready. User: {user.username}(id = {user.id})")
            self.info.setText(f"DB OK | User: {user.username}(id = {user.id})")
            self._load_categories()
            self._render_sidebar()
            self.refresh_table()
        except Exception as e:
            self.statusBar().showMessage("Initialization failed")
            self.info.setText(f"Initialization failed \n {e}")

    def on_add_category(self):
        """Prompt for a new category name, add, refresh"""
        if self.db is None:
            #Initialize first
            self.on_init_data()
            if self.db is None:
                return
        name, ok = QInputDialog.getText(self, "Add Category", "Enter new category name")
        if ok and name.strip():
            self.db.add_category(name.strip(), None)
            self._load_categories()
            self._render_sidebar()
            self.refresh_table()
            self.statusBar().showMessage(f"Added Category '{name.strip()}'")


    def on_add_task(self):
        """Prompt for a new task name, add, refresh"""
        if self.db is None:
            self.on_init_data()
            if self.db is None:
                return

        #open dialog
        dlg = TaskEditorDialog(self, self.cat_pairs)
        if dlg.exec_():
            vals = dlg.values()
            user = self.db.get_or_create_user("default")
            self.db.add_task(
                user_id=user.id,
                title=vals["title"],
                description=vals["description"],
                category_id=vals["category_id"],
                due_date=vals["due_date"],
                priority=vals["priority"],
            )
            #Update the task count display
            self.refresh_table()
            self._update_task_count()
            self.statusBar().showMessage(f"Added Task '{vals['title']}'")

    # ----------helpers----------
    def _load_categories(self):
        """Fetch categories from DB into (id,name) list"""
        cats = self.db.list_categories() if self.db else []
        self.cat_pairs = [(c.id, c.name) for c in cats if c.id is not None]
        self.cat_lookup = {c.id: c.name for c in cats if c.id is not None}

    def _current_filter(self):
        """
        Interpret the current sidebar selection:
        row 0 = All Tasks, row 1 = Today, rows >=2 = specific category
        """
        row = self.sidebar.currentRow()
        if row <= 0:
            return dict(only_today=False, category_id=None)
        if row == 1:
            return dict(only_today=True, category_id=None)
        # categories start at index 2
        idx = row - 2
        cat_id = self.cat_pairs[idx][0] if 0 <= idx < len(self.cat_pairs) else None
        return dict(only_today=False, category_id=cat_id)

    def refresh_table(self):
        """Pull tasks from DB, apply simple filters, and update the table."""
        if not self.db:
            # not initialized yet
            self.model.set_data([], {})
            self.info.setText("Initialize the database, then add a task.")
            return

        # get all tasks for current user
        user = self.db.get_or_create_user("default")
        tasks = self.db.list_tasks(user_id=user.id)

        # apply sidebar filters in Python (DB filter coming later)
        f = self._current_filter()
        if f["category_id"] is not None:
            tasks = [t for t in tasks if t.category_id == f["category_id"]]
        if f["only_today"]:
            from datetime import date as _date
            tasks = [t for t in tasks if t.due_date == _date.today()]

        # update model + UI
        self.model.set_data(tasks, self.cat_lookup)
        self.table.resizeColumnsToContents()
        self.info.setText(f"Tasks: {len(tasks)}")

    def _render_sidebar(self):
        """Render the sidebar list"""
        self.sidebar.clear()
        self.sidebar.addItem("All Tasks")
        self.sidebar.addItem("Today")
        if not self.cat_pairs:
            self.sidebar.addItem("(no categories yet)")
            self.sidebar.setEnabled(False)
        else:
            self.sidebar.setEnabled(True)
            for _, name in self.cat_pairs:
                self.sidebar.addItem(name)

    def _task_count(self) -> int:
        if not self.db:
            return 0
        user = self.db.get_or_create_user("default")
        return len(self.db.list_tasks(user_id=user.id))

    def _update_task_count(self):
        self.info.setText(f"Tasks: {self._task_count()}")

    def on_edit_task(self):
        if not self.db:
            return

        idx = self.table.currentIndex()
        if not idx.isValid():
            self.statusBar().showMessage("Select a task first")
            return

        # get the task object
        task = self.model.task_at(idx.row())
        if not task:
            return

        # open dialog pre-filled
        dlg = TaskEditorDialog(self, self.cat_pairs, task=task)
        if dlg.exec_():
            vals = dlg.values()

            # update DB
            self.db.update_task(
                task_id=task.id,
                title=vals["title"],
                description=vals["description"],
                category_id=vals["category_id"],
                due_date=vals["due_date"],
                priority=vals["priority"],
            )

            self.refresh_table()
            self.statusBar().showMessage(f"Updated task: {vals['title']}")

    def on_delete_task(self):
        if not self.db:
            return

        idx = self.table.currentIndex()
        if not idx.isValid():
            self.statusBar().showMessage("Select a task first")
            return

        task = self.model.task_at(idx.row())
        if not task:
            return

        # Delete from DB
        self.db.delete_task(task.id)

        self.refresh_table()
        self.statusBar().showMessage(f"Deleted Task '{task.title}'")
