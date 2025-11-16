
import os
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory, current_app
)
from werkzeug.utils import secure_filename

import secrets, string

from config import Config
from models import db
from models.models import User, Show


# ---------------------------
# App factory
# ---------------------------
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Assure les dossiers
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _bootstrap_admin(app)

    register_routes(app)
    return app


# ---------------------------
# Helpers
# ---------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def current_user():
    username = session.get("username")
    if not username:
        return None
    return User.query.filter_by(username=username).first()

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Accès réservé à l’administrateur.", "danger")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper

def _generate_password(n: int = 10) -> str:
    """Génère un mot de passe simple (lettres/chiffres)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def _bootstrap_admin(app):
    """Crée un admin par défaut s’il n’y a aucun utilisateur."""
    if User.query.count() == 0:
        admin = User(username=app.config["ADMIN_USERNAME"], is_admin=True)
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        print(f"[BOOTSTRAP] Admin créé: {admin.username} / (mot de passe défini via env)")


# ---------------------------
# Routes
# ---------------------------
def register_routes(app: Flask):

    @app.route("/")
    def home():
        # Filtres & recherche
        q = request.args.get("q", "", type=str).strip()
        category = request.args.get("category", "", type=str).strip()
        location = request.args.get("location", "", type=str).strip()
        type_filter = request.args.get("type", "all", type=str)  # all|image|pdf
        sort = request.args.get("sort", "asc", type=str)         # asc|desc
        date_from = request.args.get("date_from", "", type=str)
        date_to = request.args.get("date_to", "", type=str)

        shows = Show.query

        # Public : uniquement approuvés
        u = current_user()
        if not u or not u.is_admin:
            shows = shows.filter(Show.approved.is_(True))

        if q:
            like = f"%{q}%"
            shows = shows.filter(
                db.or_(
                    Show.title.ilike(like),
                    Show.description.ilike(like),
                    Show.location.ilike(like),
                    Show.category.ilike(like),
                )
            )

        if category:
            shows = shows.filter(Show.category == category)

        if location:
            shows = shows.filter(Show.location == location)

        if type_filter == "image":
            shows = shows.filter(Show.file_mimetype.ilike("image/%"))
        elif type_filter == "pdf":
            shows = shows.filter(Show.file_mimetype.ilike("application/pdf"))

        # Dates
        def parse_date(s):
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None

        if date_from:
            d1 = parse_date(date_from)
            if d1:
                shows = shows.filter(Show.date >= d1)

        if date_to:
            d2 = parse_date(date_to)
            if d2:
                shows = shows.filter(Show.date <= d2)

        # Tri
        if sort == "desc":
            shows = shows.order_by(Show.date.desc().nullslast(), Show.created_at.desc())
        else:
            shows = shows.order_by(Show.date.asc().nullsfirst(), Show.created_at.asc())

        shows = shows.all()

        # Pour les menus déroulants intelligents
        categories = [c[0] for c in db.session.query(Show.category).distinct().all() if c[0]]
        locations = [l[0] for l in db.session.query(Show.location).distinct().all() if l[0]]

        return render_template(
            "home.html",
            shows=shows,
            q=q,
            category=category,
            location=location,
            categories=sorted(categories),
            locations=sorted(locations),
            type_filter=type_filter,
            sort=sort,
            date_from=date_from,
            date_to=date_to,
            user=current_user(),
        )

    # ---- Auth ----
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["username"] = user.username
                flash("Connecté.", "success")
                next_url = request.args.get("next") or url_for("home")
                return redirect(next_url)
            flash("Identifiants invalides.", "danger")
        return render_template("login.html", user=current_user())

    @app.route("/logout")
    def logout():
        if session.get("username"):
            session.pop("username", None)
            flash("Déconnecté.", "success")
        return redirect(url_for("home"))

    # ---- Mot de passe oublié (simple, sans email) ----
    @app.route("/forgot", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            if not username:
                flash("Merci d’entrer votre nom d’utilisateur.", "warning")
                return redirect(url_for("forgot_password"))

            user = User.query.filter_by(username=username).first()
            if not user:
                # Message neutre
                flash("Si l’utilisateur existe, un nouveau mot de passe a été généré.", "info")
                return redirect(url_for("login"))

            new_pwd = _generate_password(10)
            user.set_password(new_pwd)
            db.session.commit()

            return render_template("forgot_password.html",
                                   user=current_user(),
                                   new_password=new_pwd,
                                   reset_user=user.username)

        return render_template("forgot_password.html", user=current_user())

    # ---- Publication SANS paiement : accès direct au formulaire public ----
    @app.route("/publish")
    def publish():
        return render_template("publish.html", user=current_user())

    @app.route("/submit", methods=["GET", "POST"])
    def submit_show():
        if request.method == "POST":
            title = request.form.get("title","").strip()
            description = request.form.get("description","").strip()
            location = request.form.get("location","").strip()
            category = request.form.get("category","").strip()
            date_str = request.form.get("date","").strip()

            date_val = None
            if date_str:
                try:
                    date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")

            file = request.files.get("file")
            file_name = None
            file_mimetype = None

            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)
                fname = secure_filename(file.filename)
                stem = Path(fname).stem
                ext = Path(fname).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = Path(current_app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())
                file_name = unique
                file_mimetype = file.mimetype

            show = Show(
                title=title,
                description=description,
                location=location,
                category=category,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                approved=False,  # en attente de validation admin
            )
            db.session.add(show)
            db.session.commit()
            flash("Annonce envoyée ! Elle sera visible après validation.", "success")
            return redirect(url_for("home"))

        return render_template("submit_form.html", user=current_user())

    # ---- CRUD admin ----
    @app.route("/admin/shows/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_new():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            location = request.form.get("location", "").strip()
            category = request.form.get("category", "").strip()
            date_str = request.form.get("date", "").strip()

            date_val = None
            if date_str:
                try:
                    date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")

            file = request.files.get("file")
            file_name = None
            file_mimetype = None

            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)
                fname = secure_filename(file.filename)
                # Unicité basique
                stem = Path(fname).stem
                ext = Path(fname).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = Path(app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())
                file_name = unique
                file_mimetype = file.mimetype

            show = Show(
                title=title,
                description=description,
                location=location,
                category=category,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                approved=True,
            )
            db.session.add(show)
            db.session.commit()
            flash("Annonce créée.", "success")
            return redirect(url_for("home"))

        return render_template("show_form_new.html", user=current_user())

    @app.route("/admin/shows/<int:show_id>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_edit(show_id):
        show = Show.query.get_or_404(show_id)

        if request.method == "POST":
            show.title = request.form.get("title", "").strip()
            show.description = request.form.get("description", "").strip()
            show.location = request.form.get("location", "").strip()
            show.category = request.form.get("category", "").strip()
            date_str = request.form.get("date", "").strip()
            if date_str:
                try:
                    show.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")
            else:
                show.date = None

            file = request.files.get("file")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)
                fname = secure_filename(file.filename)
                stem = Path(fname).stem
                ext = Path(fname).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = Path(app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())

                # Supprime éventuellement l’ancien fichier
                if show.file_name:
                    old_path = Path(app.config["UPLOAD_FOLDER"]) / show.file_name
                    if old_path.exists():
                        try:
                            old_path.unlink()
                        except Exception:
                            pass

                show.file_name = unique
                show.file_mimetype = file.mimetype

            db.session.commit()
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("home"))

        return render_template("show_form_edit.html", show=show, user=current_user())

    @app.route("/admin/shows/<int:show_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def show_delete(show_id):
        show = Show.query.get_or_404(show_id)

        # Supprime le fichier associé si présent
        if show.file_name:
            p = Path(app.config["UPLOAD_FOLDER"]) / show.file_name
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        db.session.delete(show)
        db.session.commit()
        flash("Annonce supprimée.", "success")
        return redirect(url_for("home"))

    @app.route("/admin/shows/<int:show_id>/approve", methods=["POST"])
    @login_required
    @admin_required
    def show_approve(show_id):
        show = Show.query.get_or_404(show_id)
        show.approved = True
        db.session.commit()
        flash("Annonce approuvée ✅", "success")
        return redirect(url_for("home"))

    # Servir les uploads
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
