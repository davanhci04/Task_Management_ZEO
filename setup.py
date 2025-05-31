from setuptools import setup, find_packages

setup(
    name='task-manager-gui',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'PyQt5',  # GUI framework
        'SQLAlchemy',  # Database ORM
        # Add other dependencies as needed
    ],
    entry_points={
        'console_scripts': [
            'task-manager-gui=main:main',  # Entry point for the application
        ],
    },
    include_package_data=True,
    description='A task management application with a graphical user interface.',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/task-manager-gui',  # Update with your repository URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)