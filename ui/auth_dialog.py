

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFormLayout,
    QLineEdit, QDialogButtonBox
)


class SignupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create your PlanPal account")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel("<h2>Sign up for PlanPal</h2>")
        subtitle = QLabel("Create a username and password to start managing your tasks.")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)

        form.addRow("Username:", self.username_edit)
        form.addRow("Password:", self.password_edit)
        form.addRow("Confirm password:", self.confirm_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            self.username_edit.text().strip(),
            self.password_edit.text(),
            self.confirm_edit.text(),
        )


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log in to PlanPal")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)

        title = QLabel("<h2>Welcome back</h2>")
        subtitle = QLabel("Enter your username and password.")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form.addRow("Username:", self.username_edit)
        form.addRow("Password:", self.password_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            self.username_edit.text().strip(),
            self.password_edit.text(),
        )
