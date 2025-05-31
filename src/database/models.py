from persistent import Persistent
from persistent.list import PersistentList
import hashlib
from datetime import datetime

class User(Persistent):
    def __init__(self, username, password):
        self.username = username
        self.password_hash = self._hash_password(password)
        self.projects = PersistentList()
        # Thêm completed_tasks nếu chưa có
        if not hasattr(self, 'completed_tasks'):
            self.completed_tasks = PersistentList()
        self.created_at = datetime.now()
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == self._hash_password(password)

class Project(Persistent):
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.tasks = PersistentList()
        self.created_at = datetime.now()
        
    def get_task_by_title(self, title):
        """Tìm task theo title"""
        for task in self.tasks:
            if task.title == title:
                return task
        return None
        
    def remove_task(self, task):
        """Xóa task khỏi project"""
        if task in self.tasks:
            self.tasks.remove(task)

class Task(Persistent):
    def __init__(self, title, description="", deadline="", status="To Do"):
        self.title = title
        self.description = description
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now()
        self.completed_at = None
        
    def mark_completed(self):
        """Đánh dấu task hoàn thành"""
        self.status = "Done"
        self.completed_at = datetime.now()

class CompletedTask(Persistent):
    def __init__(self, task, project_name):
        self.title = task.title
        self.description = task.description
        self.deadline = task.deadline
        self.project_name = project_name
        self.created_at = task.created_at
        self.completed_at = datetime.now()