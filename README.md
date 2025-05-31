# Task Manager GUI

This project is a graphical user interface (GUI) for a task management application. It allows users to manage projects and tasks efficiently through a user-friendly interface.

## Project Structure

```
task-manager-gui
├── src
│   ├── main.py                # Entry point for the application
│   ├── gui                    # Contains all GUI-related files
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── login_dialog.py     # User login dialog
│   │   ├── register_dialog.py  # User registration dialog
│   │   ├── project_dialog.py   # Project creation/editing dialog
│   │   ├── task_dialog.py      # Task creation/editing dialog
│   │   └── components          # Contains reusable GUI components
│   │       ├── __init__.py
│   │       ├── project_widget.py # Widget for displaying project info
│   │       └── task_widget.py    # Widget for displaying task info
│   ├── database                # Database management files
│   │   ├── __init__.py
│   │   ├── connection.py       # Database connection management
│   │   └── models.py          # Data models for projects and tasks
│   ├── utils                   # Utility functions
│   │   ├── __init__.py
│   │   └── helpers.py          # Helper functions
│   └── config                  # Configuration settings
│       ├── __init__.py
│       └── settings.py         # Application settings
├── assets                      # Assets for the application
│   ├── icons                   # Icon files
│   │   ├── app.ico             # Application icon
│   │   ├── project.svg         # Project icon
│   │   └── task.svg            # Task icon
│   └── styles                  # Stylesheets
│       └── main.qss            # Main stylesheet
├── requirements.txt            # Project dependencies
├── setup.py                    # Packaging information
└── README.md                   # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd task-manager-gui
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

## Features

- User registration and login
- Create and manage projects
- Create and manage tasks within projects
- Intuitive GUI for easy navigation

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.