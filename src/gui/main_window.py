from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QLabel, QMenuBar, 
                           QAction, QMessageBox, QTreeWidget, QTreeWidgetItem,
                           QStackedWidget)
from PyQt5.QtCore import Qt, QTimer
from .login_dialog import LoginDialog
from .register_dialog import RegisterDialog
from .project_dialog import ProjectDialog
from .task_dialog import TaskDialog
from database.connection import db_connection
from database.models import User, Project, Task, CompletedTask
import transaction
from PyQt5.QtGui import QColor
from persistent.list import PersistentList
from .edit_task_dialog import EditTaskDialog
from .completed_tasks_dialog import CompletedTasksDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.refresh_timer = None
        self.init_ui()
        self.connect_to_database()
        
        # Bắt đầu auto-refresh ngay khi khởi tạo
        self.start_auto_refresh()
        
        # Hiển thị login dialog ngay khi khởi động
        self.show_login_at_startup()
        
    def connect_to_database(self):
        """Kết nối tới database"""
        if not db_connection.connect():
            QMessageBox.critical(self, "Database Error", 
                               "Cannot connect to ZEO server. Please make sure ZEO server is running.")
            self.close()
    
    def start_auto_refresh(self):
        """Bắt đầu auto-refresh mỗi 3 giây (luôn chạy)"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(3000)  # Refresh mỗi 3 giây
    
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
        
        self.stacked_widget.addWidget(main_widget)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Projects menu
        projects_menu = menubar.addMenu('Projects')
        
        new_project_action = QAction('New Project', self)
        new_project_action.triggered.connect(self.create_new_project)
        projects_menu.addAction(new_project_action)
        
        # Tasks menu
        tasks_menu = menubar.addMenu('Tasks')
        
        new_task_action = QAction('New Task', self)
        new_task_action.triggered.connect(self.create_new_task)
        tasks_menu.addAction(new_task_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        completed_tasks_action = QAction('Show Completed Tasks', self)
        completed_tasks_action.triggered.connect(self.show_completed_tasks)
        view_menu.addAction(completed_tasks_action)
        
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
        completed_btn.clicked.connect(self.show_completed_tasks)
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
        
    def create_new_project(self):
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
            
        dialog = ProjectDialog(self)
        if dialog.exec_() == ProjectDialog.Accepted:
            project_name = dialog.get_project_name()
            project_description = dialog.get_project_description()
            
            # Invalidate cache trước khi thêm
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tạo project mới
            new_project = Project(project_name, project_description)
            current_user.projects.append(new_project)
            transaction.commit()
            
            # Cập nhật current_user
            self.current_user = current_user
            
            self.refresh_tree()
            QMessageBox.information(self, "Success", f"Project '{project_name}' created!")
            
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
            
            # Invalidate cache trước khi thêm
            db_connection.invalidate_cache()
            
            # Lấy lại user mới nhất từ server
            root = db_connection.get_root()
            current_user = root['users'][self.current_user.username]
            
            # Tạo task mới
            new_task = Task(
                task_data['title'],
                task_data['description'],
                task_data['deadline'],
                task_data['status']
            )
            
            current_user.projects[project_index].tasks.append(new_task)
            transaction.commit()
            
            # Cập nhật current_user
            self.current_user = current_user
            
            self.refresh_tree()
            QMessageBox.information(self, "Success", f"Task '{task_data['title']}' created!")
            
    def on_item_double_clicked(self, item, column):
        """Xử lý khi double click trên item"""
        if item.parent() is None:  # Project item
            project_name = item.text(0)
            print(f"Double clicked on project: {project_name}")
        else:  # Task item
            project_item = item.parent()
            project_name = project_item.text(0)
            task_title = item.text(0)
            self.edit_task(project_name, task_title)

    def edit_task(self, project_name, task_title):
        """Edit task"""
        if not self.current_user:
            return
            
        # Ensure completed_tasks exists
        if not hasattr(self.current_user, 'completed_tasks'):
            self.current_user.completed_tasks = PersistentList()
            
        # Tìm project và task
        project = None
        task = None
        
        for p in self.current_user.projects:
            if p.name == project_name:
                project = p
                task = p.get_task_by_title(task_title)
                break
        
        if not task:
            QMessageBox.warning(self, "Error", "Task not found!")
            return
        
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
            
            # Tìm lại project và task từ user mới
            for p in current_user.projects:
                if p.name == project_name:
                    current_task = p.get_task_by_title(task_title)
                    if current_task:
                        current_task.title = task_data['title']
                        current_task.description = task_data['description']
                        current_task.status = task_data['status']
                        current_task.deadline = task_data['deadline']
                        
                        # Nếu status chuyển thành "Done", di chuyển task
                        if old_status != "Done" and task_data['status'] == "Done":
                            self.move_task_to_completed(p, current_task, current_user)
                        
                        break
            
            transaction.commit()
            self.current_user = current_user
            self.refresh_tree()
            QMessageBox.information(self, "Success", "Task updated successfully!")
            
        elif result == 2:  # Delete task
            self.delete_task(project, task)

    def move_task_to_completed(self, project, task, user):
        """Di chuyển task đã hoàn thành sang danh sách completed"""
        # Tạo completed task
        completed_task = CompletedTask(task, project.name)
        
        # Ensure completed_tasks exists
        if not hasattr(user, 'completed_tasks'):
            user.completed_tasks = PersistentList()
            
        user.completed_tasks.append(completed_task)
        
        # Xóa task khỏi project
        project.remove_task(task)

    def delete_task(self, project, task):
        """Xóa task"""
        # Invalidate cache trước khi delete
        db_connection.invalidate_cache()
        
        # Lấy lại user mới nhất từ server
        root = db_connection.get_root()
        current_user = root['users'][self.current_user.username]
        
        # Tìm lại project và xóa task
        for p in current_user.projects:
            if p.name == project.name:
                current_task = p.get_task_by_title(task.title)
                if current_task:
                    p.remove_task(current_task)
                break
        
        transaction.commit()
        self.current_user = current_user
        self.refresh_tree()
        QMessageBox.information(self, "Success", "Task deleted successfully!")

    def show_completed_tasks(self):
        """Hiển thị danh sách tasks đã hoàn thành"""
        if not self.current_user:
            QMessageBox.warning(self, "Warning", "Please login first!")
            return
        
        # Ensure completed_tasks exists
        if not hasattr(self.current_user, 'completed_tasks'):
            self.current_user.completed_tasks = PersistentList()
            transaction.commit()
        
        dialog = CompletedTasksDialog(self.current_user.completed_tasks, self)
        result = dialog.exec_()
        
        # Refresh nếu có thay đổi
        if result == CompletedTasksDialog.Accepted:
            transaction.commit()
            
    def refresh_tree(self):
        """Refresh tree widget với data từ database"""
        self.tree_widget.clear()
        
        if self.current_user and self.current_user.projects:
            for project in self.current_user.projects:
                project_item = QTreeWidgetItem(self.tree_widget)
                project_item.setText(0, project.name)
                project_item.setText(1, "Active")
                
                # Đếm tasks theo status
                todo_count = sum(1 for task in project.tasks if task.status == "To Do")
                doing_count = sum(1 for task in project.tasks if task.status == "Doing") 
                done_count = sum(1 for task in project.tasks if task.status == "Done")
                
                project_item.setText(2, f"Tasks: {len(project.tasks)} (Todo: {todo_count}, Doing: {doing_count}, Done: {done_count})")
                
                for task in project.tasks:
                    task_item = QTreeWidgetItem(project_item)
                    task_item.setText(0, task.title)
                    task_item.setText(1, task.status)
                    task_item.setText(2, task.deadline)
                    
                    # Màu sắc theo status
                    if task.status == "Done":
                        task_item.setBackground(0, QColor(200, 255, 200))  # Xanh lá nhạt
                        task_item.setBackground(1, QColor(200, 255, 200))
                        task_item.setBackground(2, QColor(200, 255, 200))
                    elif task.status == "Doing":
                        task_item.setBackground(0, QColor(255, 255, 200))  # Vàng nhạt
                        task_item.setBackground(1, QColor(255, 255, 200))
                        task_item.setBackground(2, QColor(255, 255, 200))
                    else:  # To Do
                        task_item.setBackground(0, QColor(255, 230, 230))  # Đỏ nhạt
                        task_item.setBackground(1, QColor(255, 230, 230))
                        task_item.setBackground(2, QColor(255, 230, 230))
                        
            self.tree_widget.expandAll()
        else:
            # Hiển thị thông báo nếu chưa có projects
            info_item = QTreeWidgetItem(self.tree_widget)
            info_item.setText(0, "No projects yet. Create your first project!")
            info_item.setText(1, "")
            info_item.setText(2, "Use 'New Project' button to get started")
            info_item.setBackground(0, QColor(240, 240, 240))
            info_item.setBackground(1, QColor(240, 240, 240))
            info_item.setBackground(2, QColor(240, 240, 240))
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        if self.refresh_timer:
            self.refresh_timer.stop()
        db_connection.close()
        event.accept()