from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta
from extensions import db

app = Flask(__name__)

# CONFIG
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///codequest.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# =========================
# XP SYSTEM (FIXED)
# =========================
# =========================
# XP SYSTEM
# =========================

def xp_needed(level):
    return int(100 * (1.5 ** (level - 1)))


def add_xp(user, amount):

    user.total_xp = user.total_xp or 0
    user.level_xp = user.level_xp or 0
    user.level = user.level or 1

    # Lifetime XP
    user.total_xp += amount

    # Progress toward next level
    user.level_xp += amount

    while user.level_xp >= xp_needed(user.level):
        user.level_xp -= xp_needed(user.level)
        user.level += 1

    db.session.commit()


# =========================
# MODELS
# =========================
from models.user import User
from models.challenge import Challenge, CompletedChallenge
from models.badge import Badge


# =========================
# DB INIT
# =========================
with app.app_context():
    db.create_all()

    if Badge.query.count() == 0:
        db.session.add(Badge(name="First Steps", description="Complete your first challenge", icon="🚀"))
        db.session.add(Badge(name="Persistent", description="Complete 5 challenges", icon="🔥"))
        db.session.add(Badge(name="Rising Star", description="Reach Level 5", icon="⭐"))
        db.session.commit()

    if Challenge.query.count() == 0:
        db.session.add(Challenge(
            title="Hello World",
            description="Print Hello World in Python",
            difficulty="Easy",
            xp_reward=50,
            coin_reward=10
        ))

        db.session.add(Challenge(
            title="Reverse String",
            description="Reverse a string input",
            difficulty="Easy",
            xp_reward=75,
            coin_reward=15
        ))

        db.session.commit()


# =========================
# DAILY REWARD
# =========================
@app.route("/daily")
@login_required
def daily_reward():

    today = date.today()

    if current_user.last_daily == today:
        flash("You already claimed today's reward! 🎁", "warning")
        return redirect(url_for("dashboard"))

    if current_user.last_daily is None:
        current_user.streak = 1
    elif current_user.last_daily == today - timedelta(days=1):
        current_user.streak += 1
    else:
        current_user.streak = 1

    current_user.last_daily = today

    base_xp = 25
    base_coins = 20
    multiplier = 1 + (current_user.streak * 0.1)

    earned_xp = int(base_xp * multiplier)
    earned_coins = int(base_coins * multiplier)

    add_xp(current_user, earned_xp)
    current_user.coins += earned_coins

    db.session.commit()

    flash(f"You earned {earned_xp} XP and {earned_coins} coins! 🔥 Streak: {current_user.streak}", "success")
    return redirect(url_for("dashboard"))


# =========================
# AUTH
# =========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Password must be at least 8 characters
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("register"))

        if not any(c.isalpha() for c in password):
            flash("Password must contain at least one letter.", "error")
            return redirect(url_for("register"))

        if not any(c.isdigit() for c in password):
            flash("Password must contain at least one number.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.", "error")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            total_xp=0,
            level_xp=0,
            level=1,
            coins=0,
            streak=0
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! 🎉", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.total_xp.desc()).all()
    return render_template("leaderboard.html", users=users)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# =========================
# CHALLENGES
# =========================
@app.route("/challenges")
@login_required
def challenges():

    challenges = Challenge.query.all()

    completed = CompletedChallenge.query.filter_by(
        user_id=current_user.id
    ).all()

    completed_ids = [c.challenge_id for c in completed]

    return render_template(
        "challenges.html",
        challenges=challenges,
        completed_ids=completed_ids
    )


@app.route("/complete/<int:challenge_id>", methods=["POST"])
@login_required
def complete_challenge(challenge_id):

    challenge = Challenge.query.get_or_404(challenge_id)

    already_done = CompletedChallenge.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).first()

    if already_done:
        flash("You already completed this challenge!", "warning")
        return redirect(url_for("challenges"))

    add_xp(current_user, challenge.xp_reward)
    current_user.coins += challenge.coin_reward

    first_badge = Badge.query.filter_by(name="First Steps").first()
    if first_badge and first_badge not in current_user.badges:
        current_user.badges.append(first_badge)

    db.session.add(CompletedChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id
    ))

    db.session.commit()

    flash(f"+{challenge.xp_reward} XP, +{challenge.coin_reward} coins! ⭐", "success")
    return redirect(url_for("challenges"))


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
