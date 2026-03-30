import os
import sqlite3
from functools import wraps
from flask import (Flask, render_template, request,
                   redirect, session, flash, url_for, abort)
from models.db import init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "exam_secret_dev_key_change_in_prod")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

init_db()


# ── DB helper ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("exam.db")
    conn.row_factory = sqlite3.Row
    return conn


# ── Auth decorators ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "student":
            flash("Access denied.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Home (Landing Page) ───────────────────────────────────────────────────────
@app.route("/")
def home():
    # If already logged in, send to their dashboard
    if "user_id" in session:
        return redirect(url_for("admin_panel") if session.get("role") == "admin" else url_for("dashboard"))
    return render_template("index.html")


# ── Register ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    # Already logged in → no need to register
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username  = request.form.get("username", "").strip()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()

        # ── Validation ──
        if not all([username, password, confirm, full_name]):
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        conn = get_db()
        try:
            # Check if username already taken
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()

            if existing:
                flash("That username is already taken. Please choose another.", "error")
                return render_template("register.html")

            # Insert new student account
            conn.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, 'student', ?)",
                (username, password, full_name)
            )
            conn.commit()

            # Auto-login after registration
            new_user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        finally:
            conn.close()

        session["user_id"]  = new_user["id"]
        session["username"] = new_user["username"]
        session["role"]     = "student"
        flash(f"Account created! Welcome to ExamPro, {full_name}! 🎉", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in → redirect appropriately
    if "user_id" in session:
        return redirect(url_for("admin_panel") if session.get("role") == "admin" else url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        conn = get_db()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password)
            ).fetchone()
        finally:
            conn.close()

        if user:
            session["user_id"]   = user["id"]
            session["username"]  = user["username"]
            session["role"]      = user["role"]
            session["full_name"] = user["full_name"] or user["username"]
            flash(f"Welcome back, {session['full_name']}! 👋", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_panel"))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "error")

    return render_template("login.html")


# ── Student Dashboard ─────────────────────────────────────────────────────────
@app.route("/dashboard")
@student_required
def dashboard():
    conn = get_db()
    try:
        past = conn.execute(
            "SELECT score, total_questions, percentage FROM results WHERE user_id = ? ORDER BY submitted_at DESC",
            (session["user_id"],)
        ).fetchall()
    finally:
        conn.close()

    best_score   = max((r["percentage"] for r in past), default=0)
    total_exams  = len(past)
    avg_score    = (sum(r["percentage"] for r in past) / total_exams) if total_exams else 0

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_exams=total_exams,
        best_score=round(best_score, 1),
        avg_score=round(avg_score, 1)
    )


# ── Exam ──────────────────────────────────────────────────────────────────────
@app.route("/exam")
@student_required
def exam():
    conn = get_db()
    try:
        questions = conn.execute("SELECT * FROM questions").fetchall()
    finally:
        conn.close()

    if not questions:
        flash("No questions available right now. Please check back later.", "error")
        return redirect(url_for("dashboard"))

    return render_template("exam.html", questions=questions)


# ── Submit Exam ───────────────────────────────────────────────────────────────
@app.route("/submit_exam", methods=["POST"])
@student_required
def submit_exam():
    conn = get_db()
    try:
        questions = conn.execute("SELECT * FROM questions").fetchall()

        score  = 0
        review = []

        for q in questions:
            student_answer = request.form.get(f"q{q['id']}", "")
            correct        = q["correct_answer"]
            is_correct     = (student_answer.strip() == correct.strip())

            if is_correct:
                score += 1

            review.append({
                "question":       q["question"],
                "your_answer":    student_answer if student_answer else "(not answered)",
                "correct_answer": correct,
                "is_correct":     is_correct
            })

        total      = len(questions)
        percentage = round((score / total) * 100, 1) if total > 0 else 0

        conn.execute(
            "INSERT INTO results (user_id, score, total_questions, percentage) VALUES (?, ?, ?, ?)",
            (session["user_id"], score, total, percentage)
        )
        conn.commit()
    finally:
        conn.close()

    return render_template("result.html",
                           score=score,
                           total=total,
                           percentage=percentage,
                           review=review,
                           username=session["username"])


# ── View Past Results ─────────────────────────────────────────────────────────
@app.route("/results")
@student_required
def results():
    conn = get_db()
    try:
        past = conn.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY submitted_at DESC",
            (session["user_id"],)
        ).fetchall()
    finally:
        conn.close()

    best_score = max((r["percentage"] for r in past), default=0)
    avg_score  = (sum(r["percentage"] for r in past) / len(past)) if past else 0

    return render_template("results.html",
                           results=past,
                           best_score=round(best_score, 1),
                           avg_score=round(avg_score, 1))


# ── Admin Panel ───────────────────────────────────────────────────────────────
@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_panel():
    conn = get_db()
    try:
        if request.method == "POST":
            question = request.form.get("question", "").strip()
            o1       = request.form.get("o1", "").strip()
            o2       = request.form.get("o2", "").strip()
            o3       = request.form.get("o3", "").strip()
            o4       = request.form.get("o4", "").strip()
            correct  = request.form.get("correct", "").strip()

            if not all([question, o1, o2, o3, o4, correct]):
                flash("All fields are required.", "error")
            elif correct not in [o1, o2, o3, o4]:
                flash("Correct answer must match one of the options.", "error")
            else:
                conn.execute(
                    "INSERT INTO questions (question, option1, option2, option3, option4, correct_answer) VALUES (?,?,?,?,?,?)",
                    (question, o1, o2, o3, o4, correct)
                )
                conn.commit()
                flash("Question added successfully! ✓", "success")

        questions = conn.execute("SELECT * FROM questions ORDER BY id DESC").fetchall()
        results   = conn.execute(
            "SELECT r.*, u.username FROM results r JOIN users u ON r.user_id = u.id ORDER BY r.submitted_at DESC"
        ).fetchall()
    finally:
        conn.close()

    return render_template("admin.html", results=results, questions=questions)


# ── Delete Question ───────────────────────────────────────────────────────────
@app.route("/admin/delete_question/<int:qid>", methods=["POST"])
@admin_required
def delete_question(qid):
    conn = get_db()
    try:
        conn.execute("DELETE FROM questions WHERE id = ?", (qid,))
        conn.commit()
    finally:
        conn.close()
    flash("Question deleted.", "success")
    return redirect(url_for("admin_panel"))


# ── Logout ────────────────────────────────────────────────────────────────────
@app.route("/logout")
@login_required
def logout():
    username = session.get("username", "")
    session.clear()
    flash(f"Goodbye, {username}! You have been logged out.", "success")
    return redirect(url_for("login"))


# ── Error Handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page Not Found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal Server Error"), 500


if __name__ == "__main__":
    app.run(debug=True)