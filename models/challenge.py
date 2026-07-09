from extensions import db


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)

    difficulty = db.Column(db.String(20), nullable=False)

    xp_reward = db.Column(db.Integer, default=50)
    coin_reward = db.Column(db.Integer, default=10)

class CompletedChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)
    challenge_id = db.Column(db.Integer, nullable=False)