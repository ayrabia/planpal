from PyQt5.QtWidgets import QInputDialog, QMainWindow, QLabel, QToolBar, QAction, QSplitter, QListWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from storage import Storage

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

        #Status bar feedback
        self.statusBar().showMessage("Ready")

        #---- Body: Splitter with sidebar + placeholder panel
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        #Left: Side bar (All tasks, Today, Categories)
        self.sidebar = QListWidget()
        splitter.addWidget(self.sidebar)
        self.sidebar.setMaximumWidth(240)

        #Right: placeholder panel (Will have the table later)
        right = QWidget()
        r_layout = QVBoxLayout(right)
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
            self.statusBar().showMessage(f"Added Category '{name.strip()}'")

    # ----------helpers----------
    def _load_categories(self):
        """Fetch categories from DB into (id,name) list"""
        cats = self.db.list_categories() if self.db else []
        self.cat_pairs = [(c.id, c.name) for c in cats if c.id is not None]

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



