# 🇮🇳 Sarkari Yojna

> A web application to explore and access Indian government schemes (Sarkari Yojanas) — built with a Django REST backend and a static HTML/CSS/JS frontend.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Running the Application](#running-the-application)
- [Accessing the App](#accessing-the-app)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Sarkari Yojna** is a full-stack web application that provides citizens with easy access to information about government welfare schemes across various categories such as agriculture, education, health, housing, and more.

---

## Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python, Django          |
| Frontend  | HTML, CSS, JavaScript   |
| Database  | SQLite (default)        |
| Dev Server| Django Dev Server + Python HTTP Server |

---

## Project Structure

```
sarkari_yojna/
├── backend/                   # Django backend
│   ├── manage.py              # Django management CLI
│   ├── requirements.txt       # Python dependencies
│   ├── db.sqlite3             # SQLite database (auto-generated)
│   ├── sarkari_yojna/         # Django project config
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── <app_name>/            # Django app(s)
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       └── serializers.py
│
├── frontend/                  # Static frontend
│   ├── index.html             # Main entry point
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── assets/
│       └── images/
│
└── README.md
```

---

## Prerequisites

Make sure the following are installed on your system:

- **Python** >= 3.8 → [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- A terminal / command prompt

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/sarkari_yojna.git
cd sarkari_yojna
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# (Recommended) Create and activate a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# (Optional) Create a superuser for Django Admin
python manage.py createsuperuser
```

### 3. Frontend Setup

The frontend is plain HTML/CSS/JS — **no build step required**.

---

## Running the Application

You will need **two terminals** running simultaneously.

### Terminal 1 — Start the Backend

```bash
cd backend
python manage.py runserver
```

The Django API will be live at: **`http://127.0.0.1:8000`**

---

### Terminal 2 — Start the Frontend

From the project root (or the `frontend/` directory):

```bash
# From the frontend/ folder
cd frontend
python -m http.server 5500
```

> ⚠️ Make sure you run this command from inside the folder that contains `index.html`.

The frontend will be served at: **`http://localhost:5500`**

---

## Accessing the App

| Service         | URL                              |
|-----------------|----------------------------------|
| 🌐 Frontend      | http://localhost:5500/index.html |
| ⚙️ Backend API   | http://127.0.0.1:8000/api/       |
| 🛠️ Django Admin  | http://127.0.0.1:8000/admin/     |

> Open **http://localhost:5500/index.html** in your browser to use the application.

---

## Environment Variables

Create a `.env` file inside the `backend/` directory for sensitive configuration:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> 📝 Never commit your `.env` file. It is already included in `.gitignore`.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add: your feature description"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---


---

<p align="center">Made with ❤️ for the citizens of India</p>
