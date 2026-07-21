from extensions import db
from flask_login import UserMixin
from datetime import date

user_badges = db.Table(
    "user_badges",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("badge_id", db.Integer, db.ForeignKey("badge.id"))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    level = db.Column(db.Integer, default=1)

    coins = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)

    badges = db.relationship("Badge", secondary=user_badges, backref="users")
    
    total_xp = db.Column(db.Integer, default=0)

    level_xp = db.Column(db.Integer, default=0)

    last_daily = db.Column(db.Date, nullable=True)

    verified = db.Column(db.Boolean, default=False)