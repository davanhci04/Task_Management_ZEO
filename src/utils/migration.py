import uuid
import transaction
from datetime import datetime
from database.connection import db_connection

class DataMigration:
    """Migration script để thêm UUID cho dữ liệu cũ"""
    
    @staticmethod
    def migrate_to_uuid():
        """Thêm UUID cho projects và tasks chưa có"""
        print("🔄 Starting data migration...")
        
        try:
            root = db_connection.get_root()
            users = root.get('users', {})
            
            migration_count = 0
            
            for username, user in users.items():
                print(f"📝 Migrating user: {username}")
                
                # Migrate projects
                for project in user.projects:
                    if not hasattr(project, 'id'):
                        project.id = str(uuid.uuid4())
                        project.owner_username = username
                        project.is_archived = getattr(project, 'is_archived', False)
                        project.color = getattr(project, 'color', "#3498db")
                        migration_count += 1
                        print(f"  ✅ Added ID to project: {project.name}")
                    
                    # Migrate tasks
                    for task in project.tasks:
                        if not hasattr(task, 'id'):
                            task.id = str(uuid.uuid4())
                            task.project_id = project.id
                            task.priority = getattr(task, 'priority', "Medium")
                            task.tags = getattr(task, 'tags', [])
                            migration_count += 1
                            print(f"    ✅ Added ID to task: {task.title}")
                
                # Migrate completed tasks
                if hasattr(user, 'completed_tasks'):
                    for completed_task in user.completed_tasks:
                        if not hasattr(completed_task, 'id'):
                            completed_task.id = str(uuid.uuid4())
                            migration_count += 1
                            print(f"  ✅ Added ID to completed task: {completed_task.title}")
            
            transaction.commit()
            print(f"✅ Migration completed! {migration_count} items migrated.")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            transaction.abort()
            return False
    
    @staticmethod
    def validate_data_integrity():
        """Kiểm tra tính toàn vẹn dữ liệu"""
        print("🔍 Validating data integrity...")
        
        try:
            root = db_connection.get_root()
            users = root.get('users', {})
            
            issues = []
            
            for username, user in users.items():
                # Check duplicate project names
                project_names = {}
                for project in user.projects:
                    if project.name in project_names:
                        issues.append(f"User {username}: Duplicate project name '{project.name}'")
                    else:
                        project_names[project.name] = project
                    
                    # Check duplicate task titles within project
                    task_titles = {}
                    for task in project.tasks:
                        if task.title in task_titles:
                            issues.append(f"Project {project.name}: Duplicate task title '{task.title}'")
                        else:
                            task_titles[task.title] = task
            
            if issues:
                print("⚠️ Data integrity issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✅ Data integrity validation passed!")
            
            return len(issues) == 0
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    @staticmethod
    def check_migration_needed():
        """Kiểm tra xem có cần migration không"""
        try:
            root = db_connection.get_root()
            users = root.get('users', {})
            
            for user in users.values():
                for project in user.projects:
                    if not hasattr(project, 'id'):
                        return True
                    for task in project.tasks:
                        if not hasattr(task, 'id'):
                            return True
            return False
            
        except Exception as e:
            print(f"❌ Error checking migration: {e}")
            return False

def run_migration_if_needed(self):
    """Chạy migration cho dữ liệu cũ"""
    try:
        from config.settings import DEBUG
        if DEBUG:
            print("🔍 Checking for migration needs...")
        
        # Kiểm tra xem có dữ liệu cũ không
        if DataMigration.check_migration_needed():
            print("📦 Running data migration...")
            DataMigration.migrate_to_uuid()
            DataMigration.validate_data_integrity()
        else:
            if DEBUG:
                print("✅ No migration needed")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

def edit_task_by_identifiers(self, project_identifier, task_identifier):
    """Edit task bằng identifiers (ID hoặc name)"""
    if not self.current_user:
        return
    
    # Clean project name (remove stats if present)
    clean_project_name = project_identifier.split(' (')[0] if ' (' in project_identifier else project_identifier
    
    # Clean task title (remove icon if present) 
    clean_task_title = task_identifier.split(' ', 1)[1] if task_identifier.startswith(('📋', '⚡', '✅')) else task_identifier
    
    # Tìm project
    if hasattr(self.current_user, 'get_project_by_id'):
        project = self.current_user.get_project_by_id(project_identifier)
        if not project:  # Fallback to name search
            project = self.current_user.get_project_by_name(clean_project_name)
    else:
        project = self.current_user.get_project_by_name(clean_project_name)
    
    if not project:
        QMessageBox.warning(self, "Error", f"Project '{clean_project_name}' not found!")
        return
    
    # Tìm task
    if hasattr(project, 'get_task_by_id'):
        task = project.get_task_by_id(task_identifier)
        if not task:  # Fallback to title search
            task = project.get_task_by_title(clean_task_title)
    else:
        task = project.get_task_by_title(clean_task_title)
    
    if not task:
        QMessageBox.warning(self, "Error", f"Task '{clean_task_title}' not found!")
        return
    
    # Sử dụng ID nếu có, otherwise fallback to names
    if hasattr(project, 'id') and hasattr(task, 'id'):
        self.edit_task_by_ids(project.id, task.id)
    else:
        self.edit_task_legacy(project, task)

def edit_task_legacy(self, project, task):
    """Edit task cho dữ liệu legacy không có ID"""
    from gui.edit_task_dialog import EditTaskDialog
    from persistent.list import PersistentList
    
    # Ensure completed_tasks exists
    if not hasattr(self.current_user, 'completed_tasks'):
        self.current_user.completed_tasks = PersistentList()
    
    # Hiển thị edit dialog
    dialog = EditTaskDialog(task, self)
    result = dialog.exec_()
    
    if result == EditTaskDialog.Accepted:
        # Update task
        task_data = dialog.get_task_data()
        old_status = task.status
        
        # Invalidate cache trước khi update
        db_connection.invalidate_cache()
        
        # Lấy lại user mới nhất từ server
        root = db_connection.get_root()
        current_user = root['users'][self.current_user.username]
        
        # Tìm lại project và task bằng name
        current_project = None
        for p in current_user.projects:
            if p.name == project.name:
                current_project = p
                break
        
        if current_project:
            current_task = None
            for t in current_project.tasks:
                if t.title == task.title and t.created_at == task.created_at:
                    current_task = t
                    break
            
            if current_task:
                current_task.title = task_data['title']
                current_task.description = task_data['description']
                current_task.status = task_data['status']
                current_task.deadline = task_data['deadline']
                
                # Nếu status chuyển thành "Done", di chuyển task
                if old_status != "Done" and task_data['status'] == "Done":
                    self.move_task_to_completed(current_project, current_task, current_user)
        
        transaction.commit()
        self.current_user = current_user
        self.refresh_tree()
        QMessageBox.information(self, "Success", "Task updated successfully!")
        
    elif result == 2:  # Delete task
        self.delete_task_legacy(project, task)

def delete_task_legacy(self, project, task):
    """Xóa task cho dữ liệu legacy"""
    # Invalidate cache trước khi delete
    db_connection.invalidate_cache()
    
    # Lấy lại user mới nhất từ server
    root = db_connection.get_root()
    current_user = root['users'][self.current_user.username]
    
    # Tìm project và task bằng name
    for p in current_user.projects:
        if p.name == project.name:
            for t in list(p.tasks):  # Tạo copy để tránh modification during iteration
                if t.title == task.title and t.created_at == task.created_at:
                    p.tasks.remove(t)
                    break
            break
    
    transaction.commit()
    self.current_user = current_user
    self.refresh_tree()
    QMessageBox.information(self, "Success", "Task deleted successfully!")

def move_task_to_completed(self, project, task, user):
    """Di chuyển task đã hoàn thành sang danh sách completed"""
    from database.models import CompletedTask
    from persistent.list import PersistentList
    
    # Tạo completed task
    completed_task = CompletedTask(task, project.name)
    
    # Ensure completed_tasks exists
    if not hasattr(user, 'completed_tasks'):
        user.completed_tasks = PersistentList()
        
    user.completed_tasks.append(completed_task)
    
    # Xóa task khỏi project
    if task in project.tasks:
        project.tasks.remove(task)

# Trong method __init__ của MainWindow, thêm sau dòng connect_to_database():

def __init__(self):
    super().__init__()
    self.current_user = None
    self.refresh_timer = None
    
    # In cấu hình nếu debug mode
    if DEBUG:
        print_config()
        
    self.init_ui()
    self.connect_to_database()
    
    # Chạy migration nếu cần
    self.run_migration_if_needed()
    
    # Bắt đầu auto-refresh với interval từ config
    self.start_auto_refresh()
    
    # Hiển thị login dialog ngay khi khởi động
    self.show_login_at_startup()