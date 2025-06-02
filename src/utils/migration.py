from logging import DEBUG
import uuid
import transaction
from datetime import datetime
from database.connection import db_connection
from database.models import Task
from PyQt5.QtWidgets import QMessageBox  

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
                
                for project in user.projects:
                    if not hasattr(project, 'id'):
                        project.id = str(uuid.uuid4())
                        project.owner_username = username
                        project.is_archived = getattr(project, 'is_archived', False)
                        project.color = getattr(project, 'color', "#3498db")
                        migration_count += 1
                        print(f"  ✅ Added ID to project: {project.name}")
                    
                    for task in project.tasks:
                        if not hasattr(task, 'id'):
                            task.id = str(uuid.uuid4())
                            task.project_id = project.id
                            task.priority = getattr(task, 'priority', "Medium")
                            task.tags = getattr(task, 'tags', [])
                            migration_count += 1
                            print(f"    ✅ Added ID to task: {task.title}")
                
                if hasattr(user, 'completed_tasks') and user.completed_tasks:
                    print(f"  🔄 Migrating {len(user.completed_tasks)} completed tasks back to projects...")
                    
                    for completed_task in list(user.completed_tasks):
                        target_project = None
                        if hasattr(completed_task, 'project_name'):
                            target_project = next((p for p in user.projects if p.name == completed_task.project_name), None)
                        
                        if target_project:
                            restored_task = Task(
                                completed_task.title,
                                getattr(completed_task, 'description', ''),
                                getattr(completed_task, 'deadline', ''),
                                "Done" 
                            )
                            restored_task.id = str(uuid.uuid4())
                            restored_task.project_id = target_project.id
                            if hasattr(completed_task, 'created_at'):
                                restored_task.created_at = completed_task.created_at
                            
                            target_project.tasks.append(restored_task)
                            migration_count += 1
                            print(f"    ↩️ Restored completed task: {completed_task.title} to project: {target_project.name}")
                    
                    user.completed_tasks.clear()
                    print(f"  🗑️ Cleared completed_tasks collection for user: {username}")
            
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
                project_names = {}
                for project in user.projects:
                    if project.name in project_names:
                        issues.append(f"User {username}: Duplicate project name '{project.name}'")
                    else:
                        project_names[project.name] = project
                    
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
                
                if hasattr(user, 'completed_tasks') and user.completed_tasks:
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
        
        if DataMigration.check_migration_needed():
            print("📦 Running data migration...")
            success = DataMigration.migrate_to_uuid()
            if success:
                DataMigration.validate_data_integrity()
            else:
                print("⚠️ Migration failed, but continuing...")
        else:
            if DEBUG:
                print("✅ No migration needed")
        
    except ImportError as e:
        print(f"⚠️ Migration import error: {e}")
        print("Continuing without migration...")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        print("Continuing without migration...")

def edit_task_by_identifiers(self, project_identifier, task_identifier):
    """Edit task bằng identifiers (ID hoặc name)"""
    if not self.current_user:
        return
    
    clean_project_name = project_identifier.split(' (')[0] if ' (' in project_identifier else project_identifier
    clean_task_title = task_identifier.split(' ', 1)[1] if task_identifier.startswith(('📋', '⚡', '✅')) else task_identifier
    
    if hasattr(self.current_user, 'get_project_by_id'):
        project = self.current_user.get_project_by_id(project_identifier)
        if not project:  
            project = self.current_user.get_project_by_name(clean_project_name)
    else:
        project = self.current_user.get_project_by_name(clean_project_name)
    
    if not project:
        QMessageBox.warning(self, "Error", f"Project '{clean_project_name}' not found!")
        return

    if hasattr(project, 'get_task_by_id'):
        task = project.get_task_by_id(task_identifier)
        if not task:  
            task = project.get_task_by_title(clean_task_title)
    else:
        task = project.get_task_by_title(clean_task_title)
    
    if not task:
        QMessageBox.warning(self, "Error", f"Task '{clean_task_title}' not found!")
        return
    
    if hasattr(project, 'id') and hasattr(task, 'id'):
        self.edit_task_by_ids(project.id, task.id)
    else:
        self.edit_task_legacy(project, task)

def edit_task_legacy(self, project, task):
    """Edit task cho dữ liệu legacy không có ID"""
    from gui.edit_task_dialog import EditTaskDialog
    from persistent.list import PersistentList
    
    if not hasattr(self.current_user, 'completed_tasks'):
        self.current_user.completed_tasks = PersistentList()
    
    dialog = EditTaskDialog(task, self)
    result = dialog.exec_()
    
    if result == EditTaskDialog.Accepted:
        task_data = dialog.get_task_data()
        old_status = task.status
        db_connection.invalidate_cache()
        root = db_connection.get_root()
        current_user = root['users'][self.current_user.username]
        
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
                
                if old_status != "Done" and task_data['status'] == "Done":
                    self.move_task_to_completed(current_project, current_task, current_user)
        
        transaction.commit()
        self.current_user = current_user
        self.refresh_tree()
        QMessageBox.information(self, "Success", "Task updated successfully!")
        
    elif result == 2:
        self.delete_task_legacy(project, task)

def delete_task_legacy(self, project, task):
    """Xóa task cho dữ liệu legacy"""
    db_connection.invalidate_cache()
    
    root = db_connection.get_root()
    current_user = root['users'][self.current_user.username]
    
    for p in current_user.projects:
        if p.name == project.name:
            for t in list(p.tasks):  
                if t.title == task.title and t.created_at == task.created_at:
                    p.tasks.remove(t)
                    break
            break
    
    transaction.commit()
    self.current_user = current_user
    self.refresh_tree()
    QMessageBox.information(self, "Success", "Task deleted successfully!")


def __init__(self):
    super().__init__()
    self.current_user = None
    self.refresh_timer = None
    
    if DEBUG:
        from config.settings import print_config  
        print_config()
        
    self.init_ui()
    self.connect_to_database()
    
    self.run_migration_if_needed()
    
    self.start_auto_refresh()
    
    self.show_login_at_startup()