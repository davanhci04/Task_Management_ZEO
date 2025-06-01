from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QLabel, QMenuBar, 
                           QAction, QMessageBox, QTreeWidget, QTreeWidgetItem,
                           QStackedWidget, QHeaderView, QMenu)
from PyQt5.QtCore import Qt, QTimer
from .login_dialog import LoginDialog
from .register_dialog import RegisterDialog
from .project_dialog import ProjectDialog
from .task_dialog import TaskDialog
from database.connection import db_connection
from database.models import User, Project, Task
import transaction
from PyQt5.QtGui import QColor
from persistent.list import PersistentList
from .edit_task_dialog import EditTaskDialog
from config.settings import DATABASE_CONFIG, NETWORK_CONFIG, DEBUG, print_config
from utils.migration import DataMigration

class MainWindow(QMainWindow):
    
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
    
    def connect_to_database(self):
        """Kết nối tới database với config từ .env"""
        if DEBUG:
            print("🔌 Attempting to connect to database...")
            
        if not db_connection.connect():
            QMessageBox.critical(self, "Database Error", 
                               f"Cannot connect to ZEO server at {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}\n\n"
                               "Please check:\n"
                               "1. ZEO server is running\n"
                               "2. Server address is correct\n"
                               "3. Firewall settings\n"
                               "4. Network connectivity")
            self.close()
        else:
            # Test connection
            db_connection.test_connection()
    
    def start_auto_refresh(self):
        """Bắt đầu auto-refresh với interval từ config"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            
        refresh_interval = NETWORK_CONFIG['auto_refresh_interval']
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(refresh_interval)
        
        if DEBUG:
            print(f"🔄 Auto-refresh started with {refresh_interval}ms interval")
    
    def auto_refresh_data(self):
        """Tự động refresh dữ liệu từ server"""
        if self.current_user:
            try:
                # Invalidate cache và sync với server
                db_connection.invalidate_cache()
                
                # Lấy lại user data mới nhất
                root = db_connection.get_root()
                if self.current_user.username in root['users']:
                    # Cập nhật current_user với dữ liệu mới từ server
                    self.current_user = root['users'][self.current_user.username]
                    
                    # Refresh tree view
                    self.refresh_tree()
                    
            except Exception as e:
                print(f"Auto refresh error: {e}")
        
    def init_ui(self):
        self.setWindowTitle("Task Manager")
        self.setGeometry(100, 100, 800, 600)
        
        # Tạo stacked widget để chuyển đổi giữa login và main interface
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Tạo login screen
        self.create_login_screen()
        
        # Tạo main interface
        self.create_main_interface()
        
        # Hiển thị login screen đầu tiên
        self.stacked_widget.setCurrentIndex(0)
        
    def create_login_screen(self):
        """Tạo màn hình đăng nhập"""
        login_widget = QWidget()
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_label = QLabel("Welcome to Task Manager")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 50px;")
        layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle_label = QLabel("Please login or create an account to continue")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px; color: gray; margin-bottom: 30px;")
        layout.addWidget(subtitle_label)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.setFixedSize(200, 50)
        login_btn.clicked.connect(self.show_login_dialog)
        login_btn.setStyleSheet("QPushButton { font-size: 14px; }")
        
        # Register button
        register_btn = QPushButton("Create New Account")
        register_btn.setFixedSize(200, 50)
        register_btn.clicked.connect(self.show_register_dialog)
        register_btn.setStyleSheet("QPushButton { font-size: 14px; background-color: #4CAF50; color: white; }")
        
        # Button layout
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(login_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(register_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        login_widget.setLayout(layout)
        self.stacked_widget.addWidget(login_widget)
        
    def create_main_interface(self):
        """Tạo giao diện chính"""
        main_widget = QWidget()
        
        # Tạo menu bar
        self.create_menu_bar()
        
        # Tạo toolbar
        self.create_toolbar()
        
        # Layout chính
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Welcome label (đơn giản, không có refresh button và status)
        self.welcome_label = QLabel("")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 16px; margin: 15px;")
        main_layout.addWidget(self.welcome_label)
        
        # Tree widget để hiển thị projects và tasks
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name", "Status", "Deadline"])
        main_layout.addWidget(self.tree_widget)
        
        # Kết nối signals
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 🆕 THÊM CONTEXT MENU
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        self.stacked_widget.addWidget(main_widget)
        
    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_project_action = QAction('New Project', self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        
        new_task_action = QAction('New Task', self)
        new_task_action.triggered.connect(self.create_new_task)
        file_menu.addAction(new_task_action)
        
        file_menu.addSeparator()
        
        # 🆕 DELETE PROJECT MENU
        delete_project_action = QAction('Delete Project...', self)
        delete_project_action.triggered.connect(self.show_delete_project_dialog)
        file_menu.addAction(delete_project_action)
        
        file_menu.addSeparator()
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_delete_project_dialog(self):
        """Hiển thị dialog chọn project để xóa từ menu"""
        if not self.current_user or not self.current_user.projects:
            QMessageBox.warning(self, "Warning", "No projects to delete!")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        
        # Tạo list project names với thống kê
        project_options = []
        for p in self.current_user.projects:
            task_count = len(p.tasks)
            completed_count = sum(1 for task in p.tasks if task.status == "Done")
            option = f"{p.name} ({completed_count}/{task_count} tasks)"
            project_options.append(option)
        
        project_name, ok = QInputDialog.getItem(
            self, 
            "Delete Project", 
            "Select project to delete:", 
            project_options, 
            0, 
            False
        )
        
        if ok and project_name:
            # Extract clean project name
            clean_name = project_name.split(' (')[0]
            
            # Find project by name
            project = None
            for p in self.current_user.projects:
                if p.name == clean_name:
                    project = p
                    break
            
            if project:
                if hasattr(project, 'id'):
                    self.delete_project(project.id)
                else:
                    self.delete_project(project.name)
            else:
                QMessageBox.warning(self, "Error", f"Project '{clean_name}' not found!")

    def create_toolbar(self):
        toolbar = self.addToolBar('Main')
        
        # New Project button
        self.new_project_btn = QPushButton("📁 New Project")
        self.new_project_btn.clicked.connect(self.create_new_project)
        toolbar.addWidget(self.new_project_btn)
        
        # New Task button
        self.new_task_btn = QPushButton("📝 New Task")
        self.new_task_btn.clicked.connect(self.create_new_task)
        toolbar.addWidget(self.new_task_btn)
        
        # Separator
        toolbar.addSeparator()
        
        # Completed Tasks button
        completed_btn = QPushButton("✅ Completed")
        completed_btn.setToolTip("View completed tasks")
        toolbar.addWidget(completed_btn)
        
        # Separator
        toolbar.addSeparator()
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.logout)
        toolbar.addWidget(logout_btn)
        
    def show_login_at_startup(self):
        """Hiển thị login dialog khi khởi động"""
        # Đợi một chút để UI load xong
        QTimer.singleShot(100, self.show_auth_flow)
        
    def show_auth_flow(self):
        """Hiển thị flow đăng nhập/đăng ký"""
        self.show_login_dialog()
        
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        result = dialog.exec_()
        
        if result == LoginDialog.Accepted:
            username, password = dialog.get_credentials()
            if self.authenticate_user(username, password):
                self.current_user = self.get_user(username)
                self.welcome_label.setText(f"Welcome, {self.current_user.username}!")
                self.stacked_widget.setCurrentIndex(1)  # Chuyển sang main interface
                
                self.refresh_tree()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password!")
                # Hiển thị lại login dialog
                self.show_login_dialog()
        elif dialog.should_show_register():
            # User muốn register, hiển thị register dialog
            self.show_register_dialog()
        else:
            # User cancel và chưa login
            if self.current_user is None:
                self.close()
            
    def show_register_dialog(self):
        dialog = RegisterDialog(self)
        result = dialog.exec_()
        
        if result == RegisterDialog.Accepted:
            user_data = dialog.get_user_data()
            if self.register_user(user_data['username'], user_data['password']):
                QMessageBox.information(self, "Success", 
                    "Account created successfully! Please login with your new account.")
                # Sau khi register thành công, quay lại login
                self.show_login_dialog()
            else:
                QMessageBox.warning(self, "Registration Failed", 
                    f"Username '{user_data['username']}' already exists!")
                # Hiển thị lại register dialog
                self.show_register_dialog()
        elif dialog.should_show_login():
            # User muốn quay lại login
            self.show_login_dialog()
        else:
            # User cancel, quay lại login
            if self.current_user is None:
                self.show_login_dialog()
    
    def authenticate_user(self, username, password):
        """Xác thực người dùng"""
        # Force reload để đảm bảo dữ liệu mới nhất
        db_connection.invalidate_cache()
        root = db_connection.get_root()
        if username in root['users']:
            user = root['users'][username]
            return user.check_password(password)
        return False
        
    def get_user(self, username):
        """Lấy thông tin user"""
        root = db_connection.get_root()
        return root['users'].get(username)
        
    def register_user(self, username, password):
        """Đăng ký user mới"""
        root = db_connection.get_root()
        if username in root['users']:
            return False
            
        new_user = User(username, password)
        root['users'][username] = new_user
        transaction.commit()
        return True
        
    def logout(self):
        """Đăng xuất"""
        self.current_user = None
        self.welcome_label.setText("")
        self.tree_widget.clear()
        self.stacked_widget.setCurrentIndex(0)  # Chuyển về login screen
        
    def run_migration_if_needed(self):
        """Chạy migration cho dữ liệu cũ"""
        try:
            if DEBUG:
                print("🔍 Checking for migration needs...")
            
            # Kiểm tra xem có dữ liệu cũ không
            root = db_connection.get_root()
            users = root.get('users', {})
            
            needs_migration = False
            for user in users.values():
                for project in user.projects:
                    if not hasattr(project, 'id'):
                        needs_migration = True
                        break
                if needs_migration:
                    break
            
            if needs_migration:
                print("📦 Running data migration...")
                DataMigration.migrate_to_uuid()
                DataMigration.validate_data_integrity()
            
        except Exception as e:
            print(f"❌ Migration error: {e}")

    def create_new_project(self):
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
            
        dialog = ProjectDialog(self)
        if dialog.exec_() == ProjectDialog.Accepted:
            project_name = dialog.get_project_name()
            project_description = dialog.get_project_description()
            
            # Kiểm tra tên project trùng
            if not self.current_user.validate_project_name(project_name):
                reply = QMessageBox.question(self, "Duplicate Name", 
                    f"Project name '{project_name}' already exists. Do you want to create it anyway?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            # Invalidate cache trước khi thêm
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tạo project mới với UUID
            new_project = Project(project_name, project_description)
            new_project.owner_username = current_user.username
            current_user.projects.append(new_project)
            transaction.commit()
            
            # Cập nhật current_user
            self.current_user = current_user
            
            self.refresh_tree()
            QMessageBox.information(self, "Success", 
                f"Project '{project_name}' created!\nProject ID: {new_project.id[:8]}...")

    def create_new_task(self):
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
            
        if not self.current_user.projects:
            QMessageBox.warning(self, "Warning", "Please create a project first!")
            return
            
        dialog = TaskDialog(self, self.current_user.projects)
        if dialog.exec_() == TaskDialog.Accepted:
            task_data = dialog.get_task_data()
            project_index = dialog.get_selected_project_index()
            
            # Lấy project được chọn
            selected_project = self.current_user.projects[project_index]
            
            # Kiểm tra tên task trùng
            if not selected_project.validate_task_title(task_data['title']):
                reply = QMessageBox.question(self, "Duplicate Title", 
                    f"Task title '{task_data['title']}' already exists in this project. Do you want to create it anyway?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            # Invalidate cache trước khi thêm
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tạo task mới với UUID
            new_task = Task(
                task_data['title'],
                task_data['description'],
                task_data['deadline'],
                task_data['status']
            )
            new_task.project_id = current_user.projects[project_index].id
            
            current_user.projects[project_index].tasks.append(new_task)
            transaction.commit()
            
            # Cập nhật current_user
            self.current_user = current_user
            
            self.refresh_tree()
            QMessageBox.information(self, "Success", 
                f"Task '{task_data['title']}' created!\nTask ID: {new_task.id[:8]}...")

    def on_item_double_clicked(self, item, column):
        """Xử lý khi double click trên item"""
        if item.parent() is None:  # Project item
            # Lấy project identifier từ data hoặc text
            project_identifier = item.data(0, Qt.UserRole)
            if not project_identifier:
                # Fallback: extract từ display text
                project_text = item.text(0)
                project_identifier = project_text.split(' (')[0] if ' (' in project_text else project_text
        
            if project_identifier and self.current_user:
                # Tìm project
                if hasattr(self.current_user, 'get_project_by_id'):
                    project = self.current_user.get_project_by_id(project_identifier)
                    if not project:
                        clean_name = project_identifier.split(' (')[0] if ' (' in project_identifier else project_identifier
                        project = self.current_user.get_project_by_name(clean_name)
                else:
                    clean_name = project_identifier.split(' (')[0] if ' (' in project_identifier else project_identifier
                    project = self.current_user.get_project_by_name(clean_name)
            
                if project:
                    if hasattr(project, 'id'):
                        print(f"Double clicked on project: {project.name} (ID: {project.id[:8]})")
                    else:
                        print(f"Double clicked on project: {project.name}")
        else:  # Task item
            # Lấy identifiers từ data hoặc text
            project_item = item.parent()
            project_identifier = project_item.data(0, Qt.UserRole)
            task_identifier = item.data(0, Qt.UserRole)
        
            if not project_identifier:
                project_text = project_item.text(0)
                project_identifier = project_text.split(' (')[0] if ' (' in project_text else project_text
        
            if not task_identifier:
                task_text = item.text(0)
                task_identifier = task_text.split(' ', 1)[1] if task_text.startswith(('📋', '⚡', '✅')) else task_text
        
            if project_identifier and task_identifier:
                self.edit_task_by_identifiers(project_identifier, task_identifier)

    def edit_task_by_names(self, project_name, task_title):
        """Edit task bằng project name và task title (backward compatibility)"""
        if not self.current_user:
            return
    
        # Clean project name (remove stats if present)
        clean_project_name = project_name.split(' (')[0] if ' (' in project_name else project_name
    
        # Clean task title (remove icon if present)
        clean_task_title = task_title.split(' ', 1)[1] if task_title.startswith(('📋', '⚡', '✅')) else task_title
    
        # Tìm project
        project = None
        for p in self.current_user.projects:
            if p.name == clean_project_name:
                project = p
                break
    
        if not project:
            QMessageBox.warning(self, "Error", f"Project '{clean_project_name}' not found!")
            return
    
        # Tìm task
        task = None
        for t in project.tasks:
            if t.title == clean_task_title:
                task = t
                break
    
        if not task:
            QMessageBox.warning(self, "Error", f"Task '{clean_task_title}' not found!")
            return
    
        # Sử dụng ID nếu có
        if hasattr(project, 'id') and hasattr(task, 'id'):
            self.edit_task_by_ids(project.id, task.id)
        else:
            # Legacy support
            self.edit_task_legacy(project, task)

    def edit_task_by_ids(self, project_id, task_id):
        """Edit task bằng IDs (preferred method) - BỎ COMPLETED LOGIC"""
        if not self.current_user:
            return
            
        # Tìm project và task bằng ID
        project = self.current_user.get_project_by_id(project_id)
        if not project:
            QMessageBox.warning(self, "Error", "Project not found!")
            return
            
        task = project.get_task_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "Error", "Task not found!")
            return
        
        # Hiển thị edit dialog
        dialog = EditTaskDialog(task, self)
        result = dialog.exec_()
        
        if result == EditTaskDialog.Accepted:
            # Update task
            task_data = dialog.get_task_data()
            
            # Invalidate cache trước khi update
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tìm lại project và task bằng ID
            current_project = current_user.get_project_by_id(project_id)
            current_task = current_project.get_task_by_id(task_id) if current_project else None
            
            if current_task:
                current_task.title = task_data['title']
                current_task.description = task_data['description']
                current_task.status = task_data['status']
                current_task.deadline = task_data['deadline']
                
                # BỎ LOGIC MOVE TO COMPLETED - Task Done vẫn ở trong project
                # if old_status != "Done" and task_data['status'] == "Done":
                #     self.move_task_to_completed(current_project, current_task, current_user)
            
            transaction.commit()
            self.current_user = current_user
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Task updated successfully!")
            
        elif result == 2:  # Delete task
            self.delete_task_by_id(project_id, task_id)
    
    def edit_task_legacy(self, project, task):
        """Edit task cho dữ liệu legacy không có ID - BỎ COMPLETED LOGIC"""
        # Hiển thị edit dialog
        dialog = EditTaskDialog(task, self)
        result = dialog.exec_()
        
        if result == EditTaskDialog.Accepted:
            # Update task
            task_data = dialog.get_task_data()
            
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
                    
                    # BỎ LOGIC MOVE TO COMPLETED
                    # if old_status != "Done" and task_data['status'] == "Done":
                    #     self.move_task_to_completed(current_project, current_task, current_user)
            
            transaction.commit()
            self.current_user = current_user
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Task updated successfully!")
            
        elif result == 2:  # Delete task
            self.delete_task_legacy(project, task)
    
    def refresh_tree(self):
        """Refresh tree widget với preserve expand/collapse state"""
        
        # 🔄 LƯU TRẠNG THÁI EXPAND/COLLAPSE TRƯỚC KHI REFRESH
        expanded_projects = {}
        
        # Lưu trạng thái của tất cả project items
        for i in range(self.tree_widget.topLevelItemCount()):
            project_item = self.tree_widget.topLevelItem(i)
            if project_item:
                # Lấy project identifier từ data hoặc text
                project_id = project_item.data(0, Qt.UserRole)
                if not project_id:
                    project_text = project_item.text(0)
                    project_id = project_text.split(' (')[0] if ' (' in project_text else project_text
                    # Remove emoji if present
                    if project_id.startswith('✅ '):
                        project_id = project_id[2:]
                
                # Lưu trạng thái expanded
                expanded_projects[str(project_id)] = project_item.isExpanded()
        
        # Clear tree như bình thường
        self.tree_widget.clear()
        
        if self.current_user and self.current_user.projects:
            for project in self.current_user.projects:
                project_item = QTreeWidgetItem(self.tree_widget)
                
                # Hiển thị tên project với thống kê (có ✅ nếu fully completed)
                total_tasks = len(project.tasks)
                completed_tasks = sum(1 for task in project.tasks if task.status == "Done")
                
                # Check if project is fully completed
                is_project_completed = total_tasks > 0 and completed_tasks == total_tasks
                
                if is_project_completed:
                    display_name = f"✅ {project.name} ({completed_tasks}/{total_tasks})"
                else:
                    display_name = f"{project.name} ({completed_tasks}/{total_tasks})"
                
                project_item.setText(0, display_name)
                project_item.setText(1, "Active")
                
                # LƯU PROJECT ID VÀO DATA của item
                if hasattr(project, 'id'):
                    project_item.setData(0, Qt.UserRole, project.id)
                    project_item.setToolTip(0, f"Project: {project.name}\nID: {project.id}\nCreated: {project.created_at.strftime('%Y-%m-%d')}")
                    project_identifier = str(project.id)
                else:
                    project_item.setData(0, Qt.UserRole, project.name)
                    project_item.setToolTip(0, f"Project: {project.name}\nCreated: {project.created_at.strftime('%Y-%m-%d')}")
                    project_identifier = str(project.name)
                
                # 🎨 PROJECT COLORING
                if is_project_completed:
                    # Project hoàn thành - màu xanh
                    for col in range(3):
                        project_item.setBackground(col, QColor(144, 238, 144))  # Light green
                else:
                    # Project chưa hoàn thành - màu mặc định
                    for col in range(3):
                        project_item.setBackground(col, QColor(245, 245, 245))  # Light gray
                
                # Đếm tasks theo status
                todo_count = sum(1 for task in project.tasks if task.status == "To Do")
                doing_count = sum(1 for task in project.tasks if task.status == "Doing") 
                done_count = sum(1 for task in project.tasks if task.status == "Done")
                
                project_item.setText(2, f"Tasks: {len(project.tasks)} (Todo: {todo_count}, Doing: {doing_count}, Done: {done_count})")
                
                # HIỂN THỊ TẤT CẢ TASKS (bao gồm Done)
                for task in project.tasks:
                    task_item = QTreeWidgetItem(project_item)
                    
                    # Hiển thị tên task với icon
                    if hasattr(task, 'get_display_name'):
                        display_name = task.get_display_name()
                    else:
                        status_icon = {"To Do": "📋", "Doing": "⚡", "Done": "✅"}
                        icon = status_icon.get(task.status, "📋")
                        display_name = f"{icon} {task.title}"
                    
                    task_item.setText(0, display_name)
                    task_item.setText(1, task.status)
                    task_item.setText(2, task.deadline)
                    
                    # LƯU TASK ID VÀO DATA của item
                    if hasattr(task, 'id'):
                        task_item.setData(0, Qt.UserRole, task.id)
                        task_item.setToolTip(0, f"Task: {task.title}\nID: {task.id}\nCreated: {task.created_at.strftime('%Y-%m-%d')}")
                    else:
                        task_item.setData(0, Qt.UserRole, task.title)
                        task_item.setToolTip(0, f"Task: {task.title}\nCreated: {task.created_at.strftime('%Y-%m-%d')}")
                    
                    # Màu sắc theo status
                    if task.status == "Done":
                        for col in range(3):
                            task_item.setBackground(col, QColor(200, 255, 200))  # Green for completed tasks
                    elif task.status == "Doing":
                        for col in range(3):
                            task_item.setBackground(col, QColor(255, 255, 200))  # Yellow for in-progress
                    else:  # To Do
                        for col in range(3):
                            task_item.setBackground(col, QColor(255, 230, 230))  # Light red for pending
            
            # 🔄 KHÔI PHỤC TRẠNG THÁI EXPAND/COLLAPSE
            if project_identifier in expanded_projects:
                was_expanded = expanded_projects[project_identifier]
                project_item.setExpanded(was_expanded)
            else:
                # Mặc định expand cho projects mới hoặc lần đầu
                project_item.setExpanded(True)
        
        else:
            # Hiển thị thông báo nếu chưa có projects
            info_item = QTreeWidgetItem(self.tree_widget)
            info_item.setText(0, "No projects yet. Create your first project!")
            info_item.setText(1, "")
            info_item.setText(2, "Use 'New Project' button to get started")
            for col in range(3):
                info_item.setBackground(col, QColor(240, 240, 240))
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        db_connection.close()
        event.accept()

    def edit_task_legacy(self, project, task):
        """Edit task cho dữ liệu legacy không có ID - BỎ COMPLETED LOGIC"""
        # Hiển thị edit dialog
        dialog = EditTaskDialog(task, self)
        result = dialog.exec_()
        
        if result == EditTaskDialog.Accepted:
            # Update task
            task_data = dialog.get_task_data()
            
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
                    
                    # BỎ LOGIC MOVE TO COMPLETED
                    # if old_status != "Done" and task_data['status'] == "Done":
                    #     self.move_task_to_completed(current_project, current_task, current_user)
            
            transaction.commit()
            self.current_user = current_user
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Task updated successfully!")
            
        elif result == 2:  # Delete task
            self.delete_task_legacy(project, task)
    
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
    
    def show_context_menu(self, position):
        """Hiển thị context menu cho items"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        if item.parent() is None:  # Project item
            # 🔧 CAPTURE DATA IMMEDIATELY TRƯỚC KHI TẠO LAMBDA
            project_identifier = item.data(0, Qt.UserRole)
            if not project_identifier:
                project_text = item.text(0)
                # Remove emoji if present
                if project_text.startswith('✅ '):
                    project_text = project_text[2:]
                project_identifier = project_text.split(' (')[0] if ' (' in project_text else project_text
            
            # Context menu cho project
            
            # Edit project action
            edit_action = QAction("✏️ Edit Project", self)
            edit_action.triggered.connect(lambda checked, pid=project_identifier: self.edit_project_by_identifier(pid))
            menu.addAction(edit_action)
            
            # Delete project action
            delete_action = QAction("🗑️ Delete Project", self)
            delete_action.triggered.connect(lambda checked, pid=project_identifier: self.delete_project(pid))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # Add task action
            add_task_action = QAction("➕ Add Task", self)
            add_task_action.triggered.connect(lambda checked: self.add_task_to_project_from_identifier(project_identifier))
            menu.addAction(add_task_action)
            
        else:  # Task item
            # 🔧 CAPTURE DATA IMMEDIATELY CHO TASK
            project_item = item.parent()
            project_identifier = project_item.data(0, Qt.UserRole)
            task_identifier = item.data(0, Qt.UserRole)
            
            if not project_identifier:
                project_text = project_item.text(0)
                if project_text.startswith('✅ '):
                    project_text = project_text[2:]
                project_identifier = project_text.split(' (')[0] if ' (' in project_text else project_text
            
            if not task_identifier:
                task_text = item.text(0)
                task_identifier = task_text.split(' ', 1)[1] if task_text.startswith(('📋', '⚡', '✅')) else task_text
            
            # Context menu cho task
            
            # Edit task action
            edit_action = QAction("✏️ Edit Task", self)
            edit_action.triggered.connect(lambda checked, pid=project_identifier, tid=task_identifier: self.edit_task_by_identifiers(pid, tid))
            menu.addAction(edit_action)
            
            # Delete task action
            delete_action = QAction("🗑️ Delete Task", self)
            delete_action.triggered.connect(lambda checked, pid=project_identifier, tid=task_identifier: self.confirm_and_delete_task(pid, tid))
            menu.addAction(delete_action)
        
        # Hiển thị menu tại vị trí click
        menu.exec_(self.tree_widget.mapToGlobal(position))

    def edit_project_by_identifier(self, project_identifier):
        """Edit project bằng identifier"""
        # TODO: Implement edit project dialog
        QMessageBox.information(self, "Edit Project", f"Edit project feature coming soon!\nProject: {project_identifier}")

    def add_task_to_project_from_identifier(self, project_identifier):
        """Thêm task vào project cụ thể"""
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
            
        if not self.current_user.projects:
            QMessageBox.warning(self, "Warning", "No projects available!")
            return
        
        # Tìm project
        project = None
        if hasattr(self.current_user, 'get_project_by_id'):
            project = self.current_user.get_project_by_id(project_identifier)
            if not project:
                project = self.current_user.get_project_by_name(str(project_identifier))
        else:
            project = self.current_user.get_project_by_name(str(project_identifier))
        
        if not project:
            QMessageBox.warning(self, "Error", "Project not found!")
            return
        
        # Sử dụng task dialog với project đã chọn sẵn
        dialog = TaskDialog(self, self.current_user.projects)
        
        # Pre-select the project
        try:
            project_index = self.current_user.projects.index(project)
            dialog.project_combo.setCurrentIndex(project_index)
        except ValueError:
            pass
        
        if dialog.exec_() == TaskDialog.Accepted:
            task_data = dialog.get_task_data()
            
            # Kiểm tra tên task trùng
            if not project.validate_task_title(task_data['title']):
                reply = QMessageBox.question(self, "Duplicate Title", 
                    f"Task title '{task_data['title']}' already exists in this project. Do you want to create it anyway?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            # Invalidate cache trước khi thêm
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tìm lại project
            if hasattr(project, 'id'):
                current_project = current_user.get_project_by_id(project.id)
            else:
                current_project = current_user.get_project_by_name(project.name)
            
            if current_project:
                # Tạo task mới với UUID
                new_task = Task(
                    task_data['title'],
                    task_data['description'],
                    task_data['deadline'],
                    task_data['status']
                )
                new_task.project_id = current_project.id if hasattr(current_project, 'id') else None
                
                current_project.tasks.append(new_task)
                transaction.commit()
                
                # Cập nhật current_user
                self.current_user = current_user
                
                self.refresh_tree()
                QMessageBox.information(self, "Success", 
                    f"Task '{task_data['title']}' added to project '{current_project.name}'!\nTask ID: {new_task.id[:8]}...")

    def confirm_and_delete_task(self, project_identifier, task_identifier):
        """Xác nhận và xóa task"""
        # Confirm delete
        reply = QMessageBox.question(
            self, 
            "Confirm Delete Task", 
            f"Are you sure you want to delete task '{task_identifier}'?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.delete_task_by_identifiers(project_identifier, task_identifier)

    def delete_project(self, project_identifier):
        """Xóa project bằng ID hoặc name với enhanced error handling"""
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
        
        # Tìm project
        project = None
        if hasattr(self.current_user, 'get_project_by_id'):
            project = self.current_user.get_project_by_id(project_identifier)
            if not project:
                # Fallback to name search
                project = self.current_user.get_project_by_name(str(project_identifier))
        else:
            project = self.current_user.get_project_by_name(str(project_identifier))
        
        if not project:
            QMessageBox.warning(self, "Error", f"Project '{project_identifier}' not found!")
            return
        
        # Xác nhận xóa
        task_count = len(project.tasks)
        message = f"Are you sure you want to delete project '{project.name}'?"
        if task_count > 0:
            message += f"\n\nThis will also delete {task_count} tasks in this project."
        message += "\n\nThis action cannot be undone!"
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete Project", 
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Invalidate cache trước khi delete
                db_connection.invalidate_cache()
                
                # Lấy lại user mới nhất từ server
                root = db_connection.get_root()
                current_user = root['users'][self.current_user.username]
                
                # Tìm và xóa project
                project_to_remove = None
                if hasattr(project, 'id'):
                    # Tìm bằng ID
                    for p in current_user.projects:
                        if hasattr(p, 'id') and p.id == project.id:
                            project_to_remove = p
                            break
                else:
                    # Tìm bằng name
                    for p in current_user.projects:
                        if p.name == project.name:
                            project_to_remove = p
                            break
                
                if project_to_remove:
                    project_name = project_to_remove.name  # Store name before deletion
                    current_user.projects.remove(project_to_remove)
                    transaction.commit()
                    
                    # Cập nhật current_user
                    self.current_user = current_user
                    
                    # 🔄 REFRESH TREE NGAY SAU KHI DELETE
                    self.refresh_tree()
                    
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Project '{project_name}' and {task_count} tasks have been deleted successfully!"
                    )
                else:
                    QMessageBox.warning(self, "Error", "Project not found in database!")
                
            except Exception as e:
                transaction.abort()
                QMessageBox.critical(self, "Error", f"Failed to delete project: {str(e)}")
                print(f"Delete project error: {e}")  # Debug log

    def delete_task_by_identifiers(self, project_identifier, task_identifier):
        """Xóa task bằng identifiers"""
        if not self.current_user:
            return
        
        # Tìm project
        project = None
        if hasattr(self.current_user, 'get_project_by_id'):
            project = self.current_user.get_project_by_id(project_identifier)
            if not project:
                project = self.current_user.get_project_by_name(str(project_identifier))
        else:
            project = self.current_user.get_project_by_name(str(project_identifier))
        
        if not project:
            QMessageBox.warning(self, "Error", "Project not found!")
            return
        
        # Tìm task
        task = None
        if hasattr(project, 'get_task_by_id'):
            task = project.get_task_by_id(task_identifier)
            if not task:
                task = project.get_task_by_title(str(task_identifier))
        else:
            task = project.get_task_by_title(str(task_identifier))
        
        if not task:
            QMessageBox.warning(self, "Error", "Task not found!")
            return
        
        try:
            # Invalidate cache
            db_connection.invalidate_cache()
            
            # Get fresh user data
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Find and remove task
            if hasattr(project, 'id'):
                current_project = current_user.get_project_by_id(project.id)
            else:
                current_project = current_user.get_project_by_name(project.name)
            
            if current_project:
                if hasattr(task, 'id'):
                    task_to_remove = current_project.get_task_by_id(task.id)
                else:
                    task_to_remove = current_project.get_task_by_title(task.title)
            
                if task_to_remove:
                    current_project.tasks.remove(task_to_remove)
                    transaction.commit()
                    
                    self.current_user = current_user
                    self.refresh_tree()
                    QMessageBox.information(self, "Success", f"Task '{task.title}' deleted successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Task not found in database!")
            else:
                QMessageBox.warning(self, "Error", "Project not found!")
                
        except Exception as e:
            transaction.abort()
            QMessageBox.critical(self, "Error", f"Failed to delete task: {str(e)}")