from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit, 
                           QComboBox, QDateEdit, QMessageBox)
from PyQt5.QtCore import QDate

class TaskDialog(QDialog):
    def __init__(self, parent=None, projects=None):
        super().__init__(parent)
        self.projects = projects or []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("New Task")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout()
        
        # Task Title
        layout.addWidget(QLabel("Task Title:"))
        self.title_edit = QLineEdit()
        layout.addWidget(self.title_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["To Do", "Doing", "Done"])
        layout.addWidget(self.status_combo)
        
        # Deadline
        layout.addWidget(QLabel("Deadline:"))
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setDate(QDate.currentDate().addDays(7))
        self.deadline_edit.setCalendarPopup(True)
        layout.addWidget(self.deadline_edit)
        
        # Project
        layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        if self.projects:
            for project in self.projects:
                self.project_combo.addItem(project.name)
        else:
            self.project_combo.addItem("No projects available")
            
        layout.addWidget(self.project_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_task)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set focus to title field
        self.title_edit.setFocus()
        
    def create_task(self):
        title = self.title_edit.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Error", "Task title is required!")
            return
            
        if not self.projects:
            QMessageBox.warning(self, "Error", "No projects available!")
            return
            
        self.accept()
        
    def get_task_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'status': self.status_combo.currentText(),
            'deadline': self.deadline_edit.date().toString('yyyy-MM-dd')
        }
        
    def get_selected_project_index(self):
        return self.project_combo.currentIndex()