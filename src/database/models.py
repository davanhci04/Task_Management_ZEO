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
        # Thêm completed_tasks nếu chưa có
        if not hasattr(self, 'completed_tasks'):
            self.completed_tasks = PersistentList()
        self.created_at = datetime.now()
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == self._hash_password(password)
    
    def get_project_by_id(self, project_id):
        """Tìm project theo ID"""
        for project in self.projects:
            if hasattr(project, 'id') and project.id == project_id:
                return project
        return None
    
    def get_project_by_name(self, name):
        """Tìm project theo tên (backward compatibility)"""
        for project in self.projects:
            if project.name == name:
                return project
        return None
    
    def validate_project_name(self, name, exclude_id=None):
        """Kiểm tra tên project có trùng không"""
        for project in self.projects:
            if project.name == name:
                if exclude_id is None or (hasattr(project, 'id') and project.id != exclude_id):
                    return False
        return True

class Project(Persistent):
    def __init__(self, name, description=""):
        # Thêm UUID nếu chưa có
        if not hasattr(self, 'id'):
            self.id = str(uuid.uuid4())
        
        self.name = name
        self.description = description
        self.tasks = PersistentList()
        self.created_at = datetime.now()
        
        # Thêm metadata
        self.owner_username = None
        self.is_archived = False
        self.color = "#3498db"  # Default color
        
    def get_task_by_id(self, task_id):
        """Tìm task theo ID"""
        for task in self.tasks:
            if hasattr(task, 'id') and task.id == task_id:
                return task
        return None
        
    def get_task_by_title(self, title):
        """Tìm task theo title (backward compatibility)"""
        for task in self.tasks:
            if task.title == title:
                return task
        return None
    
    def get_all_tasks_by_title(self, title):
        """Lấy tất cả tasks cùng title"""
        return [task for task in self.tasks if task.title == title]
        
    def remove_task(self, task):
        """Xóa task khỏi project"""
        if task in self.tasks:
            self.tasks.remove(task)
    
    def validate_task_title(self, title, exclude_id=None):
        """Kiểm tra title task có trùng không"""
        for task in self.tasks:
            if task.title == title:
                if exclude_id is None or (hasattr(task, 'id') and task.id != exclude_id):
                    return False
        return True
    
    def get_display_name(self):
        """Lấy tên hiển thị với thống kê"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task.status == "Done")
        return f"{self.name} ({completed_tasks}/{total_tasks})"
    
    def get_unique_name(self):
        """Lấy tên unique (name + short ID)"""
        short_id = self.id[:8] if hasattr(self, 'id') else 'legacy'
        return f"{self.name} [{short_id}]"

class Task(Persistent):
    def __init__(self, title, description="", deadline="", status="To Do"):
        # Thêm UUID nếu chưa có
        if not hasattr(self, 'id'):
            self.id = str(uuid.uuid4())
            
        self.title = title
        self.description = description
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now()
        self.completed_at = None
        
        # Thêm metadata
        self.project_id = None
        self.priority = "Medium"  # Low, Medium, High
        self.tags = []
        
    def mark_completed(self):
        """Đánh dấu task hoàn thành"""
        self.status = "Done"
        self.completed_at = datetime.now()
    
    def get_display_name(self):
        """Lấy tên hiển thị với status"""
        status_icon = {"To Do": "📋", "Doing": "⚡", "Done": "✅"}
        icon = status_icon.get(self.status, "📋")
        return f"{icon} {self.title}"
    
    def get_unique_name(self):
        """Lấy tên unique (title + short ID)"""
        short_id = self.id[:8] if hasattr(self, 'id') else 'legacy'
        return f"{self.title} [{short_id}]"
    
    def get_full_path(self):
        """Lấy đường dẫn đầy đủ"""
        project_id = self.project_id or 'unknown'
        return f"projects/{project_id}/tasks/{self.id}"

class CompletedTask(Persistent):
    def __init__(self, task, project_name):
        # Copy từ task gốc
        self.id = task.id if hasattr(task, 'id') else str(uuid.uuid4())
        self.title = task.title
        self.description = task.description
        self.deadline = task.deadline
        self.project_name = project_name
        self.project_id = task.project_id if hasattr(task, 'project_id') else None
        self.created_at = task.created_at
        self.completed_at = datetime.now()
        
        # Thêm metadata
        self.priority = getattr(task, 'priority', 'Medium')
        self.tags = getattr(task, 'tags', [])