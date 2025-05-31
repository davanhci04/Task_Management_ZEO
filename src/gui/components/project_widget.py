from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class ProjectWidget(QWidget):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.title_label = QLabel(self.project.name)
        self.status_label = QLabel(f"Status: {self.project.status}")
        self.deadline_label = QLabel(f"Deadline: {self.project.deadline}")

        self.edit_button = QPushButton("Edit Project")
        self.edit_button.clicked.connect(self.edit_project)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.deadline_label)
        layout.addWidget(self.edit_button)

        self.setLayout(layout)

    def edit_project(self):
        # Logic to edit the project will be implemented here
        pass