🍽️ Restaurant Ordering System (Django)

A web-based restaurant management system built with Django, where customers can browse the menu and place food orders, and restaurant owners can track, manage, and update orders in real time.

This project is suitable for small to medium restaurants and demonstrates clean Django architecture, role-based access, and order tracking logic.

🚀 Features
👤 Customer Features

View food menu with prices

Place food orders online

Track order status (Pending, Preparing, Completed)

Simple and user-friendly interface

🧑‍💼 Owner / Admin Features

Manage food menu (Add / Edit / Delete items)

View all customer orders

Track and update order status

Order history and daily order tracking

Secure admin panel

🛠️ Tech Stack

Backend: Django 5.x

Frontend: Django Templates (HTML, CSS)

Database: MySQL

Authentication: Django Auth System

Environment Management: .env variables

Version Control: Git & GitHub

📂 Project Structure
resturent_project/
│
├── menu/                # Menu & order app
├── resturent_project/   # Main project settings
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── media/               # Uploaded images
├── manage.py
├── .env.example
├── .gitignore
└── README.md

⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

2️⃣ Create Virtual Environment
python -m venv env
source env/bin/activate   # Linux / Mac
env\Scripts\activate      # Windows

3️⃣ Install Requirements
pip install -r requirements.txt

4️⃣ Environment Variables

Create a .env file in the same folder as manage.py:

SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=food_db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=localhost
DB_PORT=3306


⚠️ .env is not committed for security reasons.

5️⃣ Database Migration
python manage.py makemigrations
python manage.py migrate

6️⃣ Create Superuser
python manage.py createsuperuser

7️⃣ Run Server
python manage.py runserver


Open browser:

http://127.0.0.1:8000/
