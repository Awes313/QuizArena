import os
import sqlite3
import random
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    session, flash, g, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash

#  APP CONFIG

app = Flask(__name__)
app.secret_key        = os.environ.get("SECRET_KEY", "quizarena-dev-secret-2024")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"]       = False
app.config["SESSION_COOKIE_SECURE"]   = False

DATABASE = os.environ.get("DATABASE_PATH", "quiz_app.db")

#  DATABASE HELPERS

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()

#  DECORATORS

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        db  = get_db()
        row = db.execute("SELECT is_admin FROM users WHERE id=?",
                         (session["user_id"],)).fetchone()
        if not row or not row["is_admin"]:
            flash("Admin access only.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrap

#  CONTEXT PROCESSOR

@app.context_processor
def inject_user():
    username = None
    is_admin = False
    if "user_id" in session:
        db  = get_db()
        row = db.execute("SELECT username, is_admin FROM users WHERE id=?",
                         (session["user_id"],)).fetchone()
        if row:
            username = row["username"]
            is_admin = bool(row["is_admin"])
    return dict(current_user=username, is_admin=is_admin)

#  ERROR PAGES

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


#  ROOT

@app.route("/")
def root():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

#  REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not username or not password or not confirm:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))
        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("register"))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        db = get_db()
        if db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            flash("Username already taken.", "danger")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(password),
             datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        )
        db.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

#  LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("home"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")

#  LOGOUT

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

#  HOME

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

#  SELECT DIFFICULTY

@app.route("/select/<category>")
@login_required
def select(category):
    valid = {"gaming","tech","records","riddles","coding","space","science","champion"}
    if category not in valid:
        flash("Invalid category.", "danger")
        return redirect(url_for("home"))
    return render_template("select.html", category=category)

#  QUIZ  —  load questions, store in session

@app.route("/quiz/<category>/<difficulty>")
@login_required
def quiz(category, difficulty):
    db = get_db()

    if category == "champion":
        rows = db.execute("""
            SELECT * FROM questions ORDER BY RANDOM() LIMIT 100
        """).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM questions WHERE category=? AND difficulty=?",
            (category, difficulty)
        ).fetchall()

    if len(rows) < 10:
        flash(f"Not enough questions ({len(rows)}/10). Ask admin to add more.", "warning")
        return redirect(url_for("select", category=category))

    pool = random.sample(list(rows), 10)
    questions = []
    for r in pool:
        q       = dict(r)
        options = [q["option1"], q["option2"], q["option3"], q["option4"]]
        random.shuffle(options)
        questions.append({
            "id":         q["id"],
            "question":   q["question"],
            "options":    options,
            "answer":     q["answer"],
            "category":   q["category"],
            "difficulty": q["difficulty"],
        })

    session["questions"]  = questions
    session["q_index"]    = 0
    session["score"]      = 0
    session["quiz_cat"]   = category
    session["quiz_diff"]  = difficulty
    session["quiz_start"] = datetime.utcnow().isoformat()
    return redirect(url_for("question"))

#  QUESTION

@app.route("/question", methods=["GET", "POST"])
@login_required
def question():
    questions = session.get("questions", [])
    index     = session.get("q_index", 0)

    if not questions or index >= len(questions):
        return redirect(url_for("result"))

    q = questions[index]

    if request.method == "POST":
        selected   = request.form.get("answer", "")
        is_correct = (selected == q["answer"])
        if is_correct:
            session["score"] = session.get("score", 0) + 1
        session["q_index"] = index + 1
        session.modified   = True
        return redirect(url_for("question"))

    return render_template("quiz.html",
                           q=q,
                           index=index + 1,
                           total=len(questions))

#  RESULT

@app.route("/result")
@login_required
def result():
    score      = session.get("score", 0)
    questions  = session.get("questions", [])
    total      = len(questions) or 10
    percentage = int((score / total) * 100)
    category   = session.get("quiz_cat", "general")
    difficulty = session.get("quiz_diff", "easy")

    db = get_db()

    # Save to results table
    db.execute("""
        INSERT INTO results (user_id, category, difficulty, score, total, percentage, played_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session["user_id"], category, difficulty, score, total, percentage,
          datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    # XP reward
    db.execute("UPDATE users SET xp = xp + ? WHERE id=?",
               (score * 10, session["user_id"]))
    db.commit()

    # Clear quiz session data
    for key in ["questions", "q_index", "score", "quiz_cat", "quiz_diff", "quiz_start"]:
        session.pop(key, None)

    return render_template("result.html",
                           score=score,
                           total=total,
                           percentage=percentage,
                           category=category,
                           difficulty=difficulty)

#  DASHBOARD

@app.route("/dashboard")
@login_required
def dashboard():
    db  = get_db()
    uid = session["user_id"]

    user = db.execute("SELECT username, xp FROM users WHERE id=?", (uid,)).fetchone()

    recent = db.execute("""
        SELECT category, difficulty, score, total, percentage, played_at
        FROM results WHERE user_id=?
        ORDER BY played_at DESC LIMIT 10
    """, (uid,)).fetchall()

    stats = db.execute("""
        SELECT COUNT(*) as total_q,
               ROUND(AVG(percentage),1) as avg_pct,
               MAX(percentage) as best
        FROM results WHERE user_id=?
    """, (uid,)).fetchone()

    cat_stats = db.execute("""
        SELECT category, COUNT(*) as count, ROUND(AVG(percentage),1) as avg_pct
        FROM results WHERE user_id=? GROUP BY category ORDER BY avg_pct DESC
    """, (uid,)).fetchall()

    xp        = user["xp"] or 0
    level     = (xp // 100) + 1
    xp_in_lvl = xp % 100

    return render_template("dashboard.html",
                           username=user["username"],
                           recent=recent,
                           total_quizzes=stats["total_q"],
                           avg_score=stats["avg_pct"] or 0,
                           best_score=stats["best"] or 0,
                           cat_stats=cat_stats,
                           xp=xp,
                           level=level,
                           xp_in_lvl=xp_in_lvl)

#  LEADERBOARD  ← Fixed: pulls from results table


CATEGORY_ICONS = {
    "gaming":   "🎮",
    "tech":     "💻",
    "records":  "🌍",
    "riddles":  "🧩",
    "coding":   "⌨️",
    "space":    "🚀",
    "science":  "🔬",
    "champion": "👑",
}

AVATAR_PALETTES = [
    ("#00ffc8", "#6c63ff"),
    ("#ff6b6b", "#ee0979"),
    ("#f7971e", "#ffd200"),
    ("#56ab2f", "#a8e063"),
    ("#4776e6", "#8e54e9"),
    ("#f953c6", "#b91d73"),
    ("#11998e", "#38ef7d"),
    ("#fc4a1a", "#f7b733"),
]

def avatar_colors(user_id):
    pair = AVATAR_PALETTES[user_id % len(AVATAR_PALETTES)]
    return pair[0], pair[1]

@app.route("/leaderboard")
@app.route("/leaderboard/<category>")
@login_required
def leaderboard(category="all"):
    db = get_db()

    if category == "all":
        rows = db.execute("""
            SELECT r.id, r.user_id, u.username, r.category,
                   r.score, r.total, r.percentage, r.difficulty, r.played_at
            FROM results r
            JOIN users u ON u.id = r.user_id
            ORDER BY r.score DESC, r.percentage DESC, r.played_at ASC
            LIMIT 50
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT r.id, r.user_id, u.username, r.category,
                   r.score, r.total, r.percentage, r.difficulty, r.played_at
            FROM results r
            JOIN users u ON u.id = r.user_id
            WHERE r.category = ?
            ORDER BY r.score DESC, r.percentage DESC, r.played_at ASC
            LIMIT 50
        """, (category,)).fetchall()

    entries = []
    for row in rows:
        c1, c2 = avatar_colors(row["user_id"])
        entries.append({
            "user_id":       row["user_id"],
            "username":      row["username"],
            "category":      row["category"],
            "category_icon": CATEGORY_ICONS.get(row["category"], "❓"),
            "score":         row["score"],
            "total":         row["total"],
            "accuracy":      row["percentage"],
            "avatar_color":  c1,
            "avatar_color2": c2,
        })

    # Current user rank

    user_rank = None
    uid = session.get("user_id")
    if uid:
        for i, e in enumerate(entries):
            if e["user_id"] == uid:
                games = db.execute(
                    "SELECT COUNT(*) FROM results WHERE user_id=?", (uid,)
                ).fetchone()[0]
                user_rank = {
                    "rank":     i + 1,
                    "score":    e["score"],
                    "accuracy": e["accuracy"],
                    "games":    games,
                }
                break

    return render_template("leaderboard.html",
                           entries=entries,
                           selected=category,
                           user_rank=user_rank)

#  ADMIN

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    db = get_db()

    if request.method == "POST":
        action = request.form.get("action", "add")

        if action == "delete":
            db.execute("DELETE FROM questions WHERE id=?",
                       (request.form.get("question_id"),))
            db.commit()
            flash("Question deleted.", "success")
            return redirect(url_for("admin"))

        cat   = request.form.get("category", "").strip()
        diff  = request.form.get("difficulty", "").strip()
        q_txt = request.form.get("question", "").strip()
        o1    = request.form.get("option1", "").strip()
        o2    = request.form.get("option2", "").strip()
        o3    = request.form.get("option3", "").strip()
        o4    = request.form.get("option4", "").strip()
        ans_k = request.form.get("answer", "")
        opt_map = {"A": o1, "B": o2, "C": o3, "D": o4}
        answer  = opt_map.get(ans_k, "")

        if not all([cat, diff, q_txt, o1, o2, o3, o4, answer]):
            flash("All fields are required.", "danger")
            return redirect(url_for("admin"))

        db.execute("""
            INSERT INTO questions
            (category, question, option1, option2, option3, option4, answer, difficulty)
            VALUES (?,?,?,?,?,?,?,?)
        """, (cat, q_txt, o1, o2, o3, o4, answer, diff))
        db.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("admin"))

    f_cat  = request.args.get("cat", "")
    f_diff = request.args.get("diff", "")
    search = request.args.get("q", "")

    sql    = "SELECT * FROM questions WHERE 1=1"
    params = []
    if f_cat:
        sql += " AND category=?";   params.append(f_cat)
    if f_diff:
        sql += " AND difficulty=?"; params.append(f_diff)
    if search:
        sql += " AND question LIKE ?"; params.append(f"%{search}%")
    sql += " ORDER BY id DESC LIMIT 100"

    questions = db.execute(sql, params).fetchall()
    total_q   = db.execute("SELECT COUNT(*) as c FROM questions").fetchone()["c"]
    total_u   = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_r   = db.execute("SELECT COUNT(*) as c FROM results").fetchone()["c"]

    return render_template("admin.html",
                           questions=questions,
                           total_q=total_q,
                           total_u=total_u,
                           total_r=total_r,
                           f_cat=f_cat,
                           f_diff=f_diff,
                           search=search)

#  RUN

if __name__ == "__main__":
    app.run(debug=True)
