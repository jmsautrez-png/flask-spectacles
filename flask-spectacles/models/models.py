# models/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # par défaut: utilisateur normal

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    category = db.Column(db.String(80), nullable=True)
    date = db.Column(db.Date, nullable=True)
    age_range = db.Column(db.String(50), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_mimetype = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    approved = db.Column(db.Boolean, default=False)
    contact_email = db.Column(db.String(255), nullable=True)

    # ⬇⬇⬇ Association au propriétaire (compagnie)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref="shows")

    def is_pdf(self) -> bool:
        return (self.file_mimetype or "").lower().startswith("application/pdf")

    def has_image(self) -> bool:
        return (self.file_mimetype or "").lower().startswith("image/")
