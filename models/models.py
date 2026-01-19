# models/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

# Modèle pour les demandes d'animation
class DemandeAnimation(db.Model):
    __tablename__ = "demande_animation"

    id = db.Column(db.Integer, primary_key=True)
    auto_datetime = db.Column(db.String(50), nullable=True)
    structure = db.Column(db.String(200), nullable=False)
    telephone = db.Column(db.String(50), nullable=False)
    lieu_ville = db.Column(db.String(200), nullable=False)
    nom = db.Column(db.String(150), nullable=False)
    dates_horaires = db.Column(db.String(200), nullable=False)
    type_espace = db.Column(db.String(100), nullable=False)
    genre_recherche = db.Column(db.String(100), nullable=False)
    age_range = db.Column(db.String(50), nullable=False)
    jauge = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.String(100), nullable=False)
    contraintes = db.Column(db.Text, nullable=True)
    accessibilite = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(255), nullable=False)
    is_private = db.Column(db.Boolean, default=False)  # True = visible admin uniquement
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=True)  # Email de l'utilisateur
    password_hash = db.Column(db.String(255), nullable=False)
    raison_sociale = db.Column(db.String(200), nullable=True)  # Nom de la compagnie/structure
    is_admin = db.Column(db.Boolean, default=False)  # par défaut: utilisateur normal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    raison_sociale = db.Column(db.String(200), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(500), nullable=True)  # Augmenté à 500 pour plusieurs villes
    category = db.Column(db.String(500), nullable=True)  # Augmenté à 500 pour plusieurs catégories
    date = db.Column(db.Date, nullable=True)
    age_range = db.Column(db.String(50), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_mimetype = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    approved = db.Column(db.Boolean, default=False)
    is_event = db.Column(db.Boolean, default=False)  # True = événement annoncé, False = catalogue
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    site_internet = db.Column(db.String(255), nullable=True)

    # ⬇⬇⬇ Association au propriétaire (compagnie)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref="shows")

    def is_pdf(self) -> bool:
        return (self.file_mimetype or "").lower().startswith("application/pdf")

    def has_image(self):
        if self.file_name:
            ext = self.file_name.rsplit(".", 1)[-1].lower()
            return ext in {"jpg", "jpeg", "png", "gif", "webp"}
        return False
