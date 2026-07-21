import os
import resend
from flask import url_for
from itsdangerous import URLSafeTimedSerializer

resend.api_key = os.getenv("RESEND_API_KEY")


def send_verification_email(app, user):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    token = serializer.dumps(user.email, salt="email-verification")

    verification_url = url_for(
        "verify_email",
        token=token,
        _external=True
    )

    resend.Emails.send({
        "from": "CodeQuest <noreply@doughauth.store>",
        "to": user.email,
        "subject": "Verify your CodeQuest account",
        "html": f"""
        <h2>Welcome to CodeQuest!</h2>

        <p>Thanks for creating an account.</p>

        <p>
            Please verify your email by clicking the button below.
        </p>

        <p>
            <a href="{verification_url}"
               style="
                   background:#4f46e5;
                   color:white;
                   padding:12px 20px;
                   text-decoration:none;
                   border-radius:6px;
               ">
               Verify Email
            </a>
        </p>

        <p>
            If you didn't create this account, you can safely ignore this email.
        </p>
        """
    })