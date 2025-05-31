from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credentials = None
        self.should_register = False  # Flag để biết user muốn register
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Login")
        self.setModal(True)
        self.resize(350, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Login to Task Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        layout.addWidget(self.username_edit)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)
        
        # Main buttons
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        login_btn.setDefault(True)
        button_layout.addWidget(login_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Separator line
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet("color: gray; margin: 10px;")
        layout.addWidget(separator)
        
        # Register section
        register_label = QLabel("Don't have an account?")
        register_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(register_label)
        
        register_btn = QPushButton("Create New Account")
        register_btn.clicked.connect(self.go_to_register)
        register_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        layout.addWidget(register_btn)
        
        self.setLayout(layout)
        
        # Set focus to username field
        self.username_edit.setFocus()
        
    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields!")
            return
            
        self.credentials = (username, password)
        self.accept()
        
    def go_to_register(self):
        """Chuyển sang register dialog"""
        self.should_register = True
        self.reject()  # Đóng login dialog
        
    def get_credentials(self):
        return self.credentials
        
    def should_show_register(self):
        return self.should_register