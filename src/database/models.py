from persistent import Persistent
from persistent.list import PersistentList
import hashlib
import uuid
from datetime import datetime

class User(Persistent):
    def __init__(self, username, password):
        self.username = username
        self.password_hash = self._hash_password(password)
        self.projects = PersistentList()
        self.created_at = datetime.now()
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == self._hash_password(password)
    
    def get_project_by_id(self, project_id):
        for project in self.projects:
            if hasattr(project, 'id') and project.id == project_id:
                return project
        return None
    
    def get_project_by_name(self, name):
        for project in self.projects:
            if project.name == name:
                return project
        return None
    
    def validate_project_name(self, name, exclude_id=None):
        for project in self.projects:
            if project.name == name:
                if exclude_id is None or (hasattr(project, 'id') and project.id != exclude_id):
                    return False
        return True

class Project(Persistent):
    def __init__(self, name, description=""):
        if not hasattr(self, 'id'):
            self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.tasks = PersistentList()
        self.created_at = datetime.now()
        
        self.owner_username = None
        self.is_archived = False
        self.color = "#3498db"  
        
    def get_task_by_id(self, task_id):
        for task in self.tasks:
            if hasattr(task, 'id') and task.id == task_id:
                return task
        return None
        
    def get_task_by_title(self, title):
        for task in self.tasks:
            if task.title == title:
                return task
        return None
    
    def get_all_tasks_by_title(self, title):
        return [task for task in self.tasks if task.title == title]
        
    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
    
    def validate_task_title(self, title, exclude_id=None):
        for task in self.tasks:
            if task.title == title:
                if exclude_id is None or (hasattr(task, 'id') and task.id != exclude_id):
                    return False
        return True
    
    def is_fully_completed(self):
        if not self.tasks:
            return False 
        
        return all(task.status == "Done" for task in self.tasks)
    
    def get_completion_percentage(self):
        """Lấy phần trăm hoàn thành"""
        if not self.tasks:
            return 0
        
        completed_count = sum(1 for task in self.tasks if task.status == "Done")
        return (completed_count / len(self.tasks)) * 100
    
    def get_display_name(self):
        """Lấy tên hiển thị với thống kê"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task.status == "Done")
        
        if self.is_fully_completed():
            return f"✅ {self.name} ({completed_tasks}/{total_tasks})"
        else:
            return f"{self.name} ({completed_tasks}/{total_tasks})"
    
    def get_unique_name(self):
        """Lấy tên unique (name + short ID)"""
        short_id = self.id[:8] if hasattr(self, 'id') else 'legacy'
        return f"{self.name} [{short_id}]"

class Task(Persistent):
    def __init__(self, title, description="", deadline="", status="To Do"):
        if not hasattr(self, 'id'):
            self.id = str(uuid.uuid4())
            
        self.title = title
        self.description = description
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now()
        self.completed_at = None
        self.project_id = None
        self.priority = "Medium"
        self.tags = []
        
    def mark_completed(self):
        self.status = "Done"
        self.completed_at = datetime.now()
    
    def get_display_name(self):
        status_icon = {"To Do": "📋", "Doing": "⚡", "Done": "✅"}
        icon = status_icon.get(self.status, "📋")
        return f"{icon} {self.title}"
    
    def get_unique_name(self):
        short_id = self.id[:8] if hasattr(self, 'id') else 'legacy'
        return f"{self.title} [{short_id}]"
    
    def get_full_path(self):
        """Lấy đường dẫn đầy đủ"""
        project_id = self.project_id or 'unknown'
        return f"projects/{project_id}/tasks/{self.id}"