from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_login = False  # Flag để biết user muốn quay lại login
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Register")
        self.setModal(True)
        self.resize(350, 280)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Create New Account")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_edit)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        layout.addWidget(self.password_edit)
        
        # Confirm Password
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm your password")
        layout.addWidget(self.confirm_password_edit)
        
        # Password requirements
        requirements_label = QLabel("• Password must be at least 6 characters")
        requirements_label.setStyleSheet("color: gray; font-size: 12px; margin: 5px;")
        layout.addWidget(requirements_label)
        
        # Main buttons
        button_layout = QHBoxLayout()
        
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register)
        register_btn.setDefault(True)
        register_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        button_layout.addWidget(register_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Separator line
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet("color: gray; margin: 10px;")
        layout.addWidget(separator)
        
        # Login section
        login_label = QLabel("Already have an account?")
        login_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(login_label)
        
        login_btn = QPushButton("Back to Login")
        login_btn.clicked.connect(self.go_to_login)
        layout.addWidget(login_btn)
        
        self.setLayout(layout)
        
        # Set focus to username field
        self.username_edit.setFocus()
        
    def register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill all fields!")
            return
            
        if len(username) < 3:
            QMessageBox.warning(self, "Error", "Username must be at least 3 characters!")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
            
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters!")
            return
            
        self.accept()
        
    def go_to_login(self):
        """Chuyển về login dialog"""
        self.should_login = True
        self.reject()  # Đóng register dialog
        
    def get_user_data(self):
        return {
            'username': self.username_edit.text().strip(),
            'password': self.password_edit.text()
        }
        
    def should_show_login(self):
        return self.should_login