
# Task 3 - Project Management Tool

## About
A full-stack project management web application built with Django.
It helps users organize projects, manage tasks, assign tasks to team
members, track task status, and communicate through comments.

## Features
- User registration and login
- Create and manage projects
- Add project members
- Create, edit, and delete tasks
- Assign tasks to project members
- Task status: To Do, In Progress, Completed
- Task priority: Low, Medium, High
- Optional task due dates
- Comments on tasks
- Django admin panel

## Technologies
- Python
- Django
- SQLite
- HTML
- CSS

## Setup Instructions

1. Clone or download this repository.
2. Open the Task-3 folder in the terminal.
3. Create and activate a virtual environment.
4. Install dependencies:

   `pip install -r requirements.txt`

5. Create database tables:

   `python manage.py migrate`

6. Start the development server:

   `python manage.py runserver`

7. Open `http://127.0.0.1:8000/` in your browser.

## Notes
This project uses Django's built-in authentication system and SQLite
for local development. Real-time WebSocket notifications and
drag-and-drop task movement are not implemented.
