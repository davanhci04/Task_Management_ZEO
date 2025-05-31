from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class TaskWidget(QWidget):
    def __init__(self, task, parent=None):
        super(TaskWidget, self).__init__(parent)
        self.task = task
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel(f"Task: {self.task.title}")
        status_label = QLabel(f"Status: {self.task.status}")
        deadline_label = QLabel(f"Deadline: {self.task.deadline}")

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_task)

        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(deadline_label)
        layout.addWidget(edit_button)

        self.setLayout(layout)

    def edit_task(self):
        # Logic to edit the task will be implemented here
        pass