"""
leaderboard_routes.py
──────────────────────
Blueprint for leaderboard, profile, and score-persistence logic.
Register in app.py:
    from leaderboard_routes import leaderboard_bp
    app.register_blueprint(leaderboard_bp)
"""

from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request, g
)
import sqlite3, math
from datetime import datetime
from functools import wraps

leaderboard_bp = Blueprint("leaderboard_bp", __name__)

DB = "quiz_app.db"

# Helpers

CATEGORY_META = {
    "gaming":   {"icon": "🎮", "color": "#8b5cf6"},
    "tech":     {"icon": "💻", "color": "#22d3ee"},
    "records":  {"icon": "📜", "color": "#f59e0b"},
    "riddles":  {"icon": "🧩", "color": "#ec4899"},
    "coding":   {"icon": "⌨️", "color": "#22c55e"},
    "space":    {"icon": "🚀", "color": "#3b82f6"},
    "science":  {"icon": "🔬", "color": "#06b6d4"},
    "champion": {"icon": "👑", "color": "#f97316"},
}

AVATAR_PALETTES = [
    ("#f97316", "#ea580c"),
    ("#8b5cf6", "#7c3aed"),
    ("#22d3ee", "#0891b2"),
    ("#22c55e", "#16a34a"),
    ("#ec4899", "#db2777"),
    ("#f59e0b", "#d97706"),
    ("#3b82f6", "#2563eb"),
    ("#ef4444", "#dc2626"),
]

BADGES = [
    {"id": "first_game",   "icon": "🎮", "name": "First Game",    "desc": "Play your first quiz"},
    {"id": "perfect",      "icon": "💯", "name": "Perfect 10",    "desc": "Score 10/10"},
    {"id": "streak_5",     "icon": "🔥", "name": "On Fire",       "desc": "5-game win streak (≥8/10)"},
    {"id": "champion",     "icon": "👑", "name": "Champion",      "desc": "Complete Champion mode"},
    {"id": "veteran",      "icon": "🏅", "name": "Veteran",       "desc": "Play 25+ games"},
    {"id": "all_cats",     "icon": "🌐", "name": "Globe Trotter", "desc": "Play all 8 categories"},
    {"id": "hard_master",  "icon": "💎", "name": "Hard Master",   "desc": "Score 9+ on Hard mode"},
    {"id": "speed_demon",  "icon": "⚡", "name": "Speed Demon",   "desc": "Finish a quiz in <90 sec"},
]


def get_db():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def avatar_colors(user_id: int):
    pair = AVATAR_PALETTES[user_id % len(AVATAR_PALETTES)]
    return pair[0], pair[1]

# Score saving  (call this after a quiz finishes)

def save_score(user_id: int, category: str, difficulty: str,
               score: int, total: int, time_taken: int = 0):
    """
    Persist a quiz result.  Called from the quiz result route in app.py.

    Parameters
    ----------
    user_id    : logged-in user's ID
    category   : e.g. 'gaming', 'champion'
    difficulty : 'easy' | 'hard'
    score      : number of correct answers (0-10)
    total      : total questions (usually 10)
    time_taken : seconds taken to finish
    """
    accuracy = round((score / total) * 100) if total else 0
    db = get_db()
    try:
        db.execute("""
            INSERT INTO scores
                (user_id, category, difficulty, score, total, accuracy, time_taken, played_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, category, difficulty, score, total, accuracy,
              time_taken, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        _update_badges(db, user_id)
    finally:
        db.close()


def _update_badges(db, user_id: int):
    """Evaluate and award badges after each game."""
    rows = db.execute(
        "SELECT * FROM scores WHERE user_id = ?", (user_id,)
    ).fetchall()

    earned_ids = {r["badge_id"] for r in
                  db.execute("SELECT badge_id FROM user_badges WHERE user_id=?",
                             (user_id,)).fetchall()}

    def award(badge_id):
        if badge_id not in earned_ids:
            db.execute(
                "INSERT OR IGNORE INTO user_badges (user_id, badge_id, earned_at) VALUES (?,?,?)",
                (user_id, badge_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            )
            db.commit()

    games  = len(rows)
    scores = [r["score"] for r in rows]
    cats   = {r["category"] for r in rows}

    if games >= 1:                                       award("first_game")
    if any(s == 10 for s in scores):                    award("perfect")
    if games >= 25:                                      award("veteran")
    if "champion" in cats:                               award("champion")
    if len(cats) >= 8:                                   award("all_cats")
    if any(r["score"] >= 9 and r["difficulty"] == "hard" for r in rows):
                                                         award("hard_master")

    # Win streak: last N games all ≥ 8
    recent = sorted(rows, key=lambda r: r["played_at"], reverse=True)[:5]
    if len(recent) >= 5 and all(r["score"] >= 8 for r in recent):
        award("streak_5")

# Routes

@leaderboard_bp.route("/leaderboard")
@leaderboard_bp.route("/leaderboard/<category>")
def leaderboard(category="all"):
    db = get_db()

    # Build query
    if category == "all":
        rows = db.execute("""
            SELECT s.id, s.user_id, u.username, s.category, s.score,
                   s.accuracy, s.difficulty, s.played_at
            FROM scores s
            JOIN users u ON u.id = s.user_id
            ORDER BY s.score DESC, s.accuracy DESC, s.played_at ASC
            LIMIT 50
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT s.id, s.user_id, u.username, s.category, s.score,
                   s.accuracy, s.difficulty, s.played_at
            FROM scores s
            JOIN users u ON u.id = s.user_id
            WHERE s.category = ?
            ORDER BY s.score DESC, s.accuracy DESC, s.played_at ASC
            LIMIT 50
        """, (category,)).fetchall()

    entries = []
    for row in rows:
        c1, c2 = avatar_colors(row["user_id"])
        meta = CATEGORY_META.get(row["category"], {"icon": "❓"})
        entries.append({
            "user_id":       row["user_id"],
            "username":      row["username"],
            "category":      row["category"],
            "category_icon": meta["icon"],
            "score":         row["score"],
            "accuracy":      row["accuracy"],
            "avatar_color":  c1,
            "avatar_color2": c2,
        })

    # Current user's rank in this view
    user_rank = None
    uid = session.get("user_id")
    if uid:
        for i, e in enumerate(entries):
            if e["user_id"] == uid:
                user_rank = {
                    "rank":     i + 1,
                    "score":    e["score"],
                    "accuracy": e["accuracy"],
                    "games":    db.execute(
                        "SELECT COUNT(*) FROM scores WHERE user_id=?", (uid,)
                    ).fetchone()[0],
                }
                break

    db.close()
    return render_template(
        "leaderboard.html",
        entries=entries,
        selected=category,
        user_rank=user_rank,
    )


@leaderboard_bp.route("/profile")
@leaderboard_bp.route("/profile/<int:uid>")
@login_required
def profile(uid=None):
    current_uid = session["user_id"]
    target_uid  = uid if uid else current_uid

    db = get_db()

    # User info
    user_row = db.execute(
        "SELECT id, username, created_at FROM users WHERE id=?", (target_uid,)
    ).fetchone()
    if not user_row:
        db.close()
        return redirect(url_for("home"))

    user = {
        "id":       user_row["id"],
        "username": user_row["username"],
        "joined":   user_row["created_at"][:10] if user_row["created_at"] else "—",
    }

    # Aggregate stats
    agg = db.execute("""
        SELECT COUNT(*) as games,
               MAX(score) as best,
               ROUND(AVG(score), 1) as avg,
               ROUND(AVG(accuracy), 1) as accuracy
        FROM scores WHERE user_id=?
    """, (target_uid,)).fetchone()

    # Streak: consecutive games with score >= 7
    all_scores = db.execute(
        "SELECT score FROM scores WHERE user_id=? ORDER BY played_at DESC",
        (target_uid,)
    ).fetchall()
    streak = 0
    for r in all_scores:
        if r["score"] >= 7:
            streak += 1
        else:
            break

    stats = {
        "total_games": agg["games"] or 0,
        "best_score":  agg["best"]  or 0,
        "avg_score":   agg["avg"]   or 0,
        "accuracy":    agg["accuracy"] or 0,
        "streak":      streak,
    }

    # Per-category bests
    cat_rows = db.execute("""
        SELECT category, MAX(score) as best
        FROM scores WHERE user_id=?
        GROUP BY category
    """, (target_uid,)).fetchall()
    cat_map = {r["category"]: r["best"] for r in cat_rows}

    category_stats = []
    for key, meta in CATEGORY_META.items():
        best = cat_map.get(key, 0)
        category_stats.append({
            "name": key.title(),
            "icon": meta["icon"],
            "best": best,
            "pct":  best * 10,
        })

    # Recent games (last 10)
    recent_rows = db.execute("""
        SELECT category, difficulty, score, played_at
        FROM scores WHERE user_id=?
        ORDER BY played_at DESC LIMIT 10
    """, (target_uid,)).fetchall()

    recent_games = [{
        "category":      r["category"],
        "category_icon": CATEGORY_META.get(r["category"], {"icon": "❓"})["icon"],
        "difficulty":    r["difficulty"],
        "score":         r["score"],
        "played_at":     r["played_at"][:10] if r["played_at"] else "—",
    } for r in recent_rows]

    # Badges
    earned_ids = {r["badge_id"] for r in
                  db.execute("SELECT badge_id FROM user_badges WHERE user_id=?",
                             (target_uid,)).fetchall()}
    badges = [{
        **b,
        "earned": b["id"] in earned_ids,
    } for b in BADGES]

    db.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        category_stats=category_stats,
        recent_games=recent_games,
        badges=badges,
        is_own=target_uid == current_uid,
    )
