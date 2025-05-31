from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox)

class ProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout()
        
        # Project Name
        layout.addWidget(QLabel("Project Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(self.description_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_project)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_project(self):
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Project name is required!")
            return
            
        self.accept()
        
    def get_project_name(self):
        return self.name_edit.text().strip()
        
    def get_project_description(self):
        return self.description_edit.toPlainText().strip()