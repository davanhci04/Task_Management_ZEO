from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTextEdit, 
                           QComboBox, QDateEdit, QMessageBox)
from PyQt5.QtCore import QDate, Qt

class EditTaskDialog(QDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Edit Task")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout()
        
        # Task Title
        layout.addWidget(QLabel("Task Title:"))
        self.title_edit = QLineEdit(self.task.title)
        layout.addWidget(self.title_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(self.task.description)
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["To Do", "Doing", "Done"])
        self.status_combo.setCurrentText(self.task.status)
        layout.addWidget(self.status_combo)
        
        # Deadline
        layout.addWidget(QLabel("Deadline:"))
        self.deadline_edit = QDateEdit()
        if self.task.deadline:
            try:
                date = QDate.fromString(self.task.deadline, 'yyyy-MM-dd')
                self.deadline_edit.setDate(date)
            except:
                self.deadline_edit.setDate(QDate.currentDate())
        else:
            self.deadline_edit.setDate(QDate.currentDate())
        self.deadline_edit.setCalendarPopup(True)
        layout.addWidget(self.deadline_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        button_layout.addWidget(save_btn)
        
        delete_btn = QPushButton("Delete Task")
        delete_btn.clicked.connect(self.delete_task)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; }")
        button_layout.addWidget(delete_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.title_edit.setFocus()
        
    def save_changes(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Task title cannot be empty!")
            return
        self.accept()
        
    def delete_task(self):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete task '{self.task.title}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.done(2) 
        
    def get_task_data(self):
        return {
            'title': self.title_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'status': self.status_combo.currentText(),
            'deadline': self.deadline_edit.date().toString('yyyy-MM-dd')
        }