def format_date(date_str):
    from datetime import datetime
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def validate_task_status(status):
    valid_statuses = ["To Do", "Doing", "Done"]
    return status in valid_statuses

def show_message(title, message):
    from PyQt5.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()