from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QLabel, QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt

class CompletedTasksDialog(QDialog):
    def __init__(self, completed_tasks, parent=None):
        super().__init__(parent)
        self.completed_tasks = completed_tasks
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Completed Tasks")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"Completed Tasks ({len(self.completed_tasks)} total)")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px; color: #2E7D32;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Task", "Project", "Completed Date", "Description"])
        
        # Populate table
        self.populate_table()
        
        # Resize columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        # Style table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if len(self.completed_tasks) > 0:
            clear_btn = QPushButton("Clear All Completed")
            clear_btn.clicked.connect(self.clear_completed)
            clear_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; font-weight: bold; }")
            button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; }")
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def populate_table(self):
        """Populate table with completed tasks"""
        self.table.setRowCount(len(self.completed_tasks))
        for row, task in enumerate(self.completed_tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task.title))
            self.table.setItem(row, 1, QTableWidgetItem(task.project_name))
            
            # Format completed date
            completed_date = task.completed_at.strftime("%Y-%m-%d %H:%M")
            self.table.setItem(row, 2, QTableWidgetItem(completed_date))
            
            # Truncate description if too long
            description = task.description
            if len(description) > 100:
                description = description[:100] + "..."
            self.table.setItem(row, 3, QTableWidgetItem(description))
        
    def clear_completed(self):
        reply = QMessageBox.question(self, "Confirm Clear", 
                                   "Are you sure you want to clear all completed tasks?\n\nThis action cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.completed_tasks.clear()
            self.populate_table()
            QMessageBox.information(self, "Success", "All completed tasks have been cleared!")