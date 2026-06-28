# 🏆 QuizArena

A full-stack quiz web application built with **Flask**, **Bootstrap 5**, and **SQLite**.

---

## ✨ Features

- 🔐 User Authentication (Register / Login / Logout)
- 🎮 8 Quiz Categories — Gaming, Tech, Records, Riddles, Coding, Space, Science, Champion Mode
- ⚡ Easy & Hard difficulty modes
- ⏱️ 20-second countdown timer per question
- ✅ Instant answer feedback (correct / wrong highlighted immediately)
- 🏅 XP system & level progression
- 🏆 Real-time Leaderboard
- 📊 Personal Dashboard with stats
- 🛡️ Admin Panel (add / delete questions, view stats)
- 📱 Fully responsive design

---

## 🗂️ Project Structure

```
QuizArena/
├── app.py                  # Main Flask application
├── create_db.py            # Database initializer (run once)
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── static/
│   ├── css/
│   │   └── style.css       # Global styles
│   ├── js/
│   │   └── main.js         # Global JavaScript
│   └── images/             # Category images + logo
│       ├── logo.png
│       ├── home.jpg
│       ├── gaming.jpg
│       ├── tech.jpg
│       ├── records.jpg
│       ├── riddles.jpg
│       ├── coding.jpg
│       ├── space.jpg
│       ├── science.jpg
│       ├── champion.jpg
│       ├── easy.jpg
│       ├── hard.jpg
│       └── select.jpg
│
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── home.html
    ├── select.html
    ├── quiz.html
    ├── result.html
    ├── dashboard.html
    ├── leaderboard.html
    ├── admin.html
    ├── profile.html
    ├── 404.html
    └── 500.html
```

---


## 🔑 Default Admin Account

| Username | Password  |
|----------|-----------|
| admin    | admin123  |

> ⚠️ Change the admin password after first login.

---

## 🛠️ Tech Stack

| Layer     | Technology          |
|-----------|---------------------|
| Backend   | Python 3, Flask     |
| Frontend  | HTML5, CSS3, Bootstrap 5 |
| Database  | SQLite              |
| Auth      | Werkzeug (bcrypt)   |

---

## 📄 License

This project is for educational purposes.
