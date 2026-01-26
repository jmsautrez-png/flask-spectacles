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
    intitule = db.Column(db.String(1000), nullable=True)  # Intitulé de la demande (150 mots max)
    code_postal = db.Column(db.String(10), nullable=True)  # Code postal
    region = db.Column(db.String(100), nullable=True)  # Région (déduite du code postal)
    is_private = db.Column(db.Boolean, default=False)  # True = visible admin uniquement
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    raison_sociale = db.Column(db.String(200), nullable=True)  # Nom de la compagnie/structure
    is_admin = db.Column(db.Boolean, default=False)  # par défaut: utilisateur normal
    is_subscribed = db.Column(db.Boolean, default=False)  # abonné ou non
    email = db.Column(db.String(255), nullable=True)  # Email de l'utilisateur
    telephone = db.Column(db.String(50), nullable=True)  # Téléphone de l'utilisateur
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    region = db.Column(db.String(200), nullable=True)  # Région de l'utilisateur

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
    # Photos supplémentaires pour le diaporama (jusqu'à 3 photos)
    file_name2 = db.Column(db.String(255), nullable=True)
    file_mimetype2 = db.Column(db.String(120), nullable=True)
    file_name3 = db.Column(db.String(255), nullable=True)
    file_mimetype3 = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    approved = db.Column(db.Boolean, default=False)
    is_event = db.Column(db.Boolean, default=False)  # True = événement annoncé, False = catalogue
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    site_internet = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0)  # Ordre d'affichage (0 = ordre par défaut, plus petit = plus haut)

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

    def has_image2(self):
        """Vérifie si la deuxième photo existe et est une image."""
        if self.file_name2:
            ext = self.file_name2.rsplit(".", 1)[-1].lower()
            return ext in {"jpg", "jpeg", "png", "gif", "webp"}
        return False

    def has_image3(self):
        """Vérifie si la troisième photo existe et est une image."""
        if self.file_name3:
            ext = self.file_name3.rsplit(".", 1)[-1].lower()
            return ext in {"jpg", "jpeg", "png", "gif", "webp"}
        return False

    def get_all_images(self):
        """Retourne la liste de tous les noms de fichiers images (pour le diaporama)."""
        images = []
        if self.has_image():
            images.append(self.file_name)
        if self.has_image2():
            images.append(self.file_name2)
        if self.has_image3():
            images.append(self.file_name3)
        return images

    def image_count(self):
        """Retourne le nombre d'images disponibles."""
        return len(self.get_all_images())


# Modèle pour les demandes d'écoles (thèmes pédagogiques)
class DemandeEcole(db.Model):
    __tablename__ = "demande_ecole"

    id = db.Column(db.Integer, primary_key=True)
    auto_datetime = db.Column(db.String(50), nullable=True)
    
    # Informations sur l'école
    nom_ecole = db.Column(db.String(200), nullable=False)
    type_etablissement = db.Column(db.String(50), nullable=False)  # Maternelle, Primaire, Les deux
    adresse = db.Column(db.String(300), nullable=True)
    code_postal = db.Column(db.String(10), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=True)
    
    # Contact
    nom_contact = db.Column(db.String(150), nullable=False)
    fonction_contact = db.Column(db.String(100), nullable=True)  # Directeur, Enseignant, etc.
    email = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(50), nullable=False)
    
    # Informations sur les classes
    nombre_classes = db.Column(db.String(20), nullable=True)
    nombre_eleves = db.Column(db.String(20), nullable=True)
    niveaux_concernes = db.Column(db.String(200), nullable=True)  # PS, MS, GS, CP, CE1, CE2, CM1, CM2
    
    # Thème pédagogique
    theme_principal = db.Column(db.String(100), nullable=False)
    sous_themes = db.Column(db.Text, nullable=True)  # JSON ou liste séparée par virgules
    objectifs_pedagogiques = db.Column(db.Text, nullable=False)
    
    # Type d'animation souhaitée
    types_animation = db.Column(db.String(500), nullable=True)  # Spectacle, Atelier, Conférence, etc.
    
    # Contraintes techniques
    salle_disponible = db.Column(db.String(100), nullable=True)  # Salle de classe, Polyvalente, Gymnase
    surface_approximative = db.Column(db.String(50), nullable=True)
    acces_electricite = db.Column(db.Boolean, default=True)
    
    # Période et budget
    periode_souhaitee = db.Column(db.String(100), nullable=True)
    date_precise = db.Column(db.String(100), nullable=True)
    budget = db.Column(db.String(50), nullable=True)
    
    # Informations complémentaires
    informations_complementaires = db.Column(db.Text, nullable=True)
    
    # Statut de la demande
    statut = db.Column(db.String(50), default="nouvelle")  # nouvelle, en_cours, traitee, annulee
    notes_admin = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
