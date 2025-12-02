from datetime import date
from ui.auth_dialog import SignupDialog, LoginDialog
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QLabel,
    QToolBar,
    QAction,
    QSplitter,
    QListWidget,
    QVBoxLayout,
    QWidget,
    QTableView,
    QMessageBox,
    QHeaderView,
)

from storage import Storage
from models import User
from ui.task_editor import TaskEditorDialog
from ui.task_table import TaskTableModel
from ui.report_dialog import ReportDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlanPal")
        self.resize(900, 600)

        # DB & user state
        self.db: Storage | None = None
        self.current_user: User | None = None

        # category helpers
        self.cat_pairs: list[tuple[int, str]] = []
        self.cat_lookup: dict[int, str] = {}

        # ----- Toolbar -----
        tb = QToolBar("Main")
        self.addToolBar(tb)

        # Initialize DB (optional toolbar button)
        self.act_init = QAction("Initialize Data", self)
        self.act_init.setStatusTip("Create/upgrade database schema")
        self.act_init.triggered.connect(self.on_init_data)
        tb.addAction(self.act_init)

        # User actions
        self.act_new_user = QAction("New User", self)
        self.act_new_user.setStatusTip("Create a new user profile")
        self.act_new_user.triggered.connect(self.on_new_user)
        tb.addAction(self.act_new_user)

        self.act_login = QAction("Login / Switch User", self)
        self.act_login.setStatusTip("Login as an existing user")
        self.act_login.triggered.connect(self.on_login)
        tb.addAction(self.act_login)

        tb.addSeparator()

        # Category actions
        self.act_add_cat = QAction("Add Category", self)
        self.act_add_cat.setStatusTip("Create a new category")
        self.act_add_cat.triggered.connect(self.on_add_category)
        tb.addAction(self.act_add_cat)

        self.act_del_cat = QAction("Delete Category", self)
        self.act_del_cat.setStatusTip("Delete the selected category")
        self.act_del_cat.triggered.connect(self.on_delete_category)
        tb.addAction(self.act_del_cat)

        tb.addSeparator()

        # Task actions
        self.act_add_task = QAction("Add Task", self)
        self.act_add_task.setStatusTip("Create a new task")
        self.act_add_task.triggered.connect(self.on_add_task)
        tb.addAction(self.act_add_task)

        self.act_edit_task = QAction("Edit Task", self)
        self.act_edit_task.setStatusTip("Edit selected task")
        self.act_edit_task.triggered.connect(self.on_edit_task)
        tb.addAction(self.act_edit_task)

        self.act_delete_task = QAction("Delete Task", self)
        self.act_delete_task.setStatusTip("Delete selected task")
        self.act_delete_task.triggered.connect(self.on_delete_task)
        tb.addAction(self.act_delete_task)

        tb.addSeparator()

        # Visual report
        self.act_report = QAction("Report", self)
        self.act_report.setStatusTip("Show a visual report of tasks")
        self.act_report.triggered.connect(self.on_show_report)
        tb.addAction(self.act_report)

        # Status bar
        self.statusBar().showMessage("Starting...")

        # ----- Body: splitter with sidebar + main panel -----
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left: sidebar (All / Today / categories)
        self.sidebar = QListWidget()
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        splitter.addWidget(self.sidebar)

        # Right: info label + table
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.info = QLabel("Welcome to PlanPal. Please log in or sign up.")
        right_layout.addWidget(self.info)

        self.table = QTableView()
        self.model = TaskTableModel([], {})
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table)

        splitter.addWidget(right)
        splitter.setSizes([260, 740])

        # Initial sidebar contents
        self._render_sidebar()

        #set up DB and force login/signup before tasks
        self._ensure_db()
        self.show_auth_dialog_on_startup()


    # Helpers

    def _ensure_db(self) -> bool:
        """Make sure the Storage instance exists."""
        if self.db is None:
            try:
                self.db = Storage()
                self.db.migrate()
            except Exception as e:
                QMessageBox.critical(self, "Database error", str(e))
                return False
        return True

    def _load_categories(self):
        """Load all categories into helper structures."""
        if not self.db or not self.current_user:
            self.cat_pairs = []
            self.cat_lookup = {}
            return

        cats = self.db.list_categories(self.current_user.id)
        self.cat_pairs = [(c.id, c.name) for c in cats]
        self.cat_lookup = {c.id: c.name for c in cats}

    def _render_sidebar(self):
        """Fill the sidebar list: All, Today, then categories."""
        self.sidebar.clear()
        self.sidebar.addItem("All Tasks")
        self.sidebar.addItem("Today")

        for _id, name in self.cat_pairs:
            self.sidebar.addItem(name)

        if self.sidebar.count() > 0 and self.sidebar.currentRow() == -1:
            self.sidebar.setCurrentRow(0)

    def _current_filter(self) -> dict:
        row = self.sidebar.currentRow()
        if row <= 0:
            return {"mode": "all"}
        if row == 1:
            return {"mode": "today"}
        cat_idx = row - 2
        if 0 <= cat_idx < len(self.cat_pairs):
            cid, _name = self.cat_pairs[cat_idx]
            return {"mode": "category", "category_id": cid}
        return {"mode": "all"}

    def _update_task_count_label(self, visible_count: int):
        if self.current_user:
            user_part = f"User: {self.current_user.username}  |  "
        else:
            user_part = ""
        self.info.setText(f"{user_part}{visible_count} task(s) shown")


    # Startup auth dialog

    def show_auth_dialog_on_startup(self):
        """
        Show a blocking dialog that forces the user to either Login or Sign Up
        before they can interact with tasks.
        """
        if not self._ensure_db():
            return

        # If we already have a user (e.g. for some reason), skip
        if self.current_user:
            self._after_login_setup()
            return

        while not self.current_user:
            mb = QMessageBox(self)
            mb.setWindowTitle("Welcome to PlanPal")
            mb.setText("Welcome! Please log in or sign up to continue.")
            login_btn = mb.addButton("Login", QMessageBox.AcceptRole)
            signup_btn = mb.addButton("Sign Up", QMessageBox.ActionRole)
            quit_btn = mb.addButton("Quit", QMessageBox.RejectRole)
            mb.exec_()

            clicked = mb.clickedButton()
            if clicked == login_btn:
                self.on_login()
            elif clicked == signup_btn:
                self.on_new_user()
            else:
                # Quit the app if they don't want to auth
                self.close()
                return

        # Once we have a user, load data
        self._after_login_setup()

    def _after_login_setup(self):
        """Called after successful login/signup."""
        self.statusBar().showMessage(f"Logged in as {self.current_user.username}")
        self._load_categories()
        self._render_sidebar()
        self.refresh_table()


    # Core actions


    def on_init_data(self):
        """Toolbar action: re-run migrate and refresh view."""
        if not self._ensure_db():
            return
        self.db.migrate()
        self._load_categories()
        self._render_sidebar()
        self.refresh_table()
        self.statusBar().showMessage("Database checked.")

    def on_new_user(self):
        """Create a new user profile (username + password)."""
        if not self._ensure_db():
            return

        dlg = SignupDialog(self)
        if dlg.exec_() != dlg.Accepted:
            return

        username, pwd, confirm = dlg.values()
        if not username or not pwd:
            QMessageBox.warning(self, "Invalid data", "Username and password are required.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Passwords don't match", "Please re-enter your password.")
            return

        try:
            user = self.db.create_user(username, pwd)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create user:\n{e}")
            return

        self.current_user = user
        self._after_login_setup()

    def on_login(self):
        """Login as an existing user."""
        if not self._ensure_db():
            return

        dlg = LoginDialog(self)
        if dlg.exec_() != dlg.Accepted:
            return

        username, pwd = dlg.values()
        if not username or not pwd:
            QMessageBox.warning(self, "Invalid data", "Username and password are required.")
            return

        user = self.db.authenticate_user(username, pwd)
        if not user:
            QMessageBox.warning(self, "Login failed", "Invalid username or password.")
            return

        self.current_user = user
        self._after_login_setup()

    def refresh_table(self):
        """Refresh the table view based on current user and sidebar filter."""
        if not self.db or not self.current_user:
            self.model.set_data([], self.cat_lookup)
            self.info.setText("Please log in or sign up to see your tasks.")
            return

        tasks = self.db.list_tasks(user_id=self.current_user.id)
        f = self._current_filter()

        if f["mode"] == "today":
            today = date.today()
            tasks = [t for t in tasks if t.due_date == today]
        elif f["mode"] == "category":
            cid = f.get("category_id")
            tasks = [t for t in tasks if t.category_id == cid]

        self.model.set_data(tasks, self.cat_lookup)
        self._update_task_count_label(len(tasks))


    # Sidebar events


    def on_sidebar_changed(self, _row: int):
        self.refresh_table()


    # Category actions

    def on_add_category(self):
        if not self._ensure_db():
            return
        if not self.current_user:
            QMessageBox.information(self, "Login required", "Please login first.")
            return

        name, ok = QInputDialog.getText(self, "Add Category", "Enter new category name:")
        if not ok or not name.strip():
            return
        name = name.strip()

        self.db.add_category(self.current_user.id, name, None)
        self._load_categories()
        self._render_sidebar()
        self.refresh_table()
        self.statusBar().showMessage(f"Added Category '{name}'")

    def on_delete_category(self):
        if not self.db:
            return

        row = self.sidebar.currentRow()
        if row < 2:  # 0 = All, 1 = Today
            self.statusBar().showMessage("Select a category (not All/Today) to delete.")
            return

        cat_idx = row - 2
        if not (0 <= cat_idx < len(self.cat_pairs)):
            return

        cid, name = self.cat_pairs[cat_idx]

        reply = QMessageBox.question(
            self,
            "Delete Category",
            f"Delete category '{name}'? Tasks will lose this category.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.db.delete_category(cid)
        self._load_categories()
        self._render_sidebar()
        self.refresh_table()
        self.statusBar().showMessage(f"Deleted Category '{name}'")


    # Task actions


    def on_add_task(self):
        if not self._ensure_db():
            return
        if not self.current_user:
            QMessageBox.information(self, "Login required", "Please login first.")
            return

        dlg = TaskEditorDialog(self, self.cat_pairs)
        if dlg.exec_():
            vals = dlg.values()
            self.db.add_task(
                user_id=self.current_user.id,
                title=vals["title"],
                description=vals["description"],
                category_id=vals["category_id"],
                due_date=vals["due_date"],
                priority=vals["priority"],
            )
            self.refresh_table()
            self.statusBar().showMessage(f"Added Task '{vals['title']}'")

    def on_edit_task(self):
        if not self.db:
            return

        idx = self.table.currentIndex()
        if not idx.isValid():
            self.statusBar().showMessage("Select a task first")
            return

        task = self.model.task_at(idx.row())
        if not task:
            return

        dlg = TaskEditorDialog(self, self.cat_pairs, task=task)
        if dlg.exec_():
            vals = dlg.values()
            self.db.update_task(
                task_id=task.id,
                title=vals["title"],
                description=vals["description"],
                category_id=vals["category_id"],
                due_date=vals["due_date"],
                priority=vals["priority"],
            )
            self.refresh_table()
            self.statusBar().showMessage(f"Updated Task '{vals['title']}'")

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

        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Delete task '{task.title}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.db.delete_task(task.id)
        self.refresh_table()
        self.statusBar().showMessage(f"Deleted Task '{task.title}'")

    # ---------------------------------------------------------------------
    # Reports


    def on_show_report(self):
        if not self.db or not self.current_user:
            QMessageBox.information(self, "No data", "Please login and add some tasks first.")
            return

        tasks = self.db.list_tasks(user_id=self.current_user.id)
        if not tasks:
            QMessageBox.information(self, "No tasks", "No tasks to report on yet.")
            return

        dlg = ReportDialog(self, tasks, self.cat_lookup)
        dlg.exec_()
