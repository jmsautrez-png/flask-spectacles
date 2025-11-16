from sqlalchemy import or_
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    current_app,
)

# Mail (optionnel)
try:
    from flask_mail import Mail, Message  # type: ignore
except Exception:  # pragma: no cover
    Mail = None  # type: ignore
    Message = None  # type: ignore

from config import Config
from models import db
from models.models import User, Show

# -----------------------------------------------------
# Factory
# -----------------------------------------------------
def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Dossiers nécessaires
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    # DB
    db.init_app(app)

    # Mail (optionnel)
    if Mail:
        try:
            app.mail = Mail(app)  # type: ignore[attr-defined]
        except Exception as e:  # pragma: no cover
            app.mail = None  # type: ignore[attr-defined]
            print("[MAIL] non initialisé:", e)
    else:
        app.mail = None  # type: ignore[attr-defined]

    with app.app_context():
        db.create_all()
        _bootstrap_admin(app)

    register_routes(app)
    return app

# -----------------------------------------------------
# Utilitaires
# -----------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def current_user() -> Optional[User]:
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
    import string, secrets
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def _bootstrap_admin(app: Flask) -> None:
    # Crée un admin au premier démarrage si la table users est vide
    if User.query.count() == 0:
        admin = User(username=app.config["ADMIN_USERNAME"], is_admin=True)
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        print(f"[BOOTSTRAP] Admin créé: {admin.username} / (mot de passe défini via env)")

# -----------------------------------------------------
# Routes
# -----------------------------------------------------
def register_routes(app: Flask) -> None:
    # ---------------------------
    # Auth
    # ---------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                flash("Veuillez remplir tous les champs.", "danger")
                return render_template("register.html")

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Ce nom d'utilisateur existe déjà.", "warning")
                return render_template("register.html")

            try:
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Compte créé ! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for("login"))
            except Exception:
                db.session.rollback()
                flash("Erreur lors de la création du compte.", "danger")

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "username" in session:
            u = current_user()
            return redirect(url_for("admin_dashboard" if (u and u.is_admin) else "company_dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["username"] = user.username
                flash("Connecté.", "success")
                next_url = request.args.get("next")
                if next_url:
                    return redirect(next_url)
                return redirect(url_for("admin_dashboard" if user.is_admin else "company_dashboard"))

            flash("Identifiants invalides.", "danger")

        return render_template("login.html", user=current_user())

    @app.route("/logout")
    def logout():
        if session.get("username"):
            session.pop("username", None)
            flash("Déconnecté.", "success")
        return redirect(url_for("home"))

    @app.route("/forgot", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            if not username:
                flash("Merci d’entrer votre nom d’utilisateur.", "warning")
                return redirect(url_for("forgot_password"))

            user = User.query.filter_by(username=username).first()
            if not user:
                flash("Si l’utilisateur existe, un nouveau mot de passe a été généré.", "info")
                return redirect(url_for("login"))

            new_pwd = _generate_password(10)
            user.set_password(new_pwd)
            db.session.commit()

            return render_template(
                "forgot_password.html",
                user=current_user(),
                new_password=new_pwd,
                reset_user=user.username,
            )

        return render_template("forgot_password.html", user=current_user())

    # ---------------------------
    # Accueil & listing (recherche)
    # ---------------------------
    @app.route("/", endpoint="home")
    def home():
        q = request.args.get("q", "", type=str).strip()
        category = request.args.get("category", "", type=str).strip()
        location = request.args.get("location", "", type=str).strip()
        type_filter = request.args.get("type", "all", type=str)
        sort = request.args.get("sort", "asc", type=str)
        date_from = request.args.get("date_from", "", type=str)
        date_to = request.args.get("date_to", "", type=str)

        shows = Show.query

        # Visibilité publique : non-admin -> seulement approuvés
        u = current_user()
        if not u or not u.is_admin:
            shows = shows.filter(Show.approved.is_(True))

        # Recherche texte + âges (6, 6 ans, 6-10, 6/10, 6 à 10, etc.)
        if q:
            like = f"%{q}%"

            variants = {q}
            if any(c.isdigit() for c in q):
                cleaned = q.lower().replace("ans", "").strip()
                seps = [" - ", "-", "—", "–", "à", "a", "/", " "]
                norm = cleaned
                for sep in seps:
                    norm = norm.replace(sep, "/")

                variants.update({
                    cleaned,
                    cleaned.replace(" ", ""),
                    cleaned.replace("-", "/"),
                    cleaned.replace("/", "-"),
                    cleaned.replace(" ", "-"),
                    cleaned.replace(" ", "/"),
                    norm,
                    norm.replace("/", "-"),
                    norm.replace("/", ""),
                })

            conditions = [
                Show.title.ilike(like),
                Show.description.ilike(like),
                Show.location.ilike(like),
                Show.category.ilike(like),
            ]

            # Facultatif si le champ existe
            try:
                Show.contact_email  # type: ignore[attr-defined]
                conditions.append(Show.contact_email.ilike(like))  # type: ignore[attr-defined]
            except Exception:
                pass

            for v in {v for v in variants if v}:
                v_like = f"%{v}%"
                try:
                    conditions.append(Show.age_range.ilike(v_like))
                except Exception:
                    pass
                conditions.append(Show.description.ilike(v_like))

            shows = shows.filter(or_(*conditions))

        # Filtres simples
        if category:
            shows = shows.filter(Show.category == category)
        if location:
            shows = shows.filter(Show.location == location)

        # Type de fichier
        if type_filter == "image":
            shows = shows.filter(Show.file_mimetype.ilike("image/%"))
        elif type_filter == "pdf":
            shows = shows.filter(Show.file_mimetype.ilike("application/pdf"))

        # Filtres de dates
        def parse_date(s: str):
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

        # Exécution + filet de sécurité
        try:
            shows = shows.all()
        except Exception as e:
            current_app.logger.exception("Erreur lors de la requête /home: %s", e)
            flash("Une erreur est survenue lors de la recherche.", "danger")
            shows = []

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
    @app.route("/informations-legales")
    def legal():
     return render_template("legal.html")
    # ---------------------------
    # Publication & fichiers
    # ---------------------------
    @app.route("/publish")
    @login_required
    def publish():
        return render_template("publish.html", user=current_user())

    @app.route("/submit", methods=["GET", "POST"])
    @login_required
    def submit_show():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            location = request.form.get("location", "").strip()
            category = request.form.get("category", "").strip()
            date_str = request.form.get("date", "").strip()
            age_range = request.form.get("age_range", "").strip()
            contact_email = request.form.get("contact_email", "").strip()

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
                from pathlib import Path as _Path
                stem = _Path(file.filename).stem
                ext = _Path(file.filename).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())
                file_name = unique
                file_mimetype = file.mimetype

            show = Show(
                title=title,
                description=description,
                location=location,
                category=category,
                age_range=age_range or None,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                contact_email=contact_email or None,
                approved=False,
                user_id=current_user().id,   # associer l’auteur
            )
            db.session.add(show)
            db.session.commit()

            if getattr(current_app, "mail", None) and current_app.config.get("MAIL_USERNAME"):
                try:
                    to_addr = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                    body = (
                        "Nouvelle annonce à valider\n\n"
                        f"Titre: {title}\nLieu: {location}\nCatégorie: {category}\n"
                        f"Date: {date_val}\nEmail contact: {contact_email}"
                    )
                    msg = Message(subject="Nouvelle annonce à valider", recipients=[to_addr])  # type: ignore[arg-type]
                    msg.body = body  # type: ignore[assignment]
                    current_app.mail.send(msg)  # type: ignore[attr-defined]
                except Exception as e:  # pragma: no cover
                    print("[MAIL] envoi impossible:", e)

            flash("Annonce envoyée ! Elle sera visible après validation.", "success")
            return redirect(url_for("company_dashboard"))

        return render_template("submit_form.html", user=current_user())

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

    # ---------------------------
    # Espace Compagnie
    # ---------------------------
    @app.route("/dashboard", endpoint="company_dashboard")
    @login_required
    def company_dashboard():
        u = current_user()
        if u.is_admin:
            return redirect(url_for("admin_dashboard"))
        my_shows = Show.query.filter_by(user_id=u.id).order_by(Show.created_at.desc()).all()
        return render_template("company_dashboard.html", user=u, shows=my_shows)

    @app.route("/my/shows/<int:show_id>/edit", methods=["GET","POST"], endpoint="show_edit_self")
    @login_required
    def show_edit_self(show_id: int):
        s = Show.query.get_or_404(show_id)
        u = current_user()
        if not (u.is_admin or s.user_id == u.id):
            flash("Accès refusé.", "danger")
            return redirect(url_for("company_dashboard"))

        if request.method == "POST":
            s.title = request.form.get("title","").strip()
            s.description = request.form.get("description","").strip()
            s.location = request.form.get("location","").strip()
            s.category = request.form.get("category","").strip()
            s.age_range = (request.form.get("age_range","") or None)

            date_str = request.form.get("date","").strip()
            if date_str:
                try:
                    s.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")
            else:
                s.date = None

            file = request.files.get("file")
            if file and file.filename and allowed_file(file.filename):
                from pathlib import Path as _Path
                stem = _Path(file.filename).stem
                ext = _Path(file.filename).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())
                if s.file_name:
                    old = _Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name
                    if old.exists():
                        try:
                            old.unlink()
                        except Exception:
                            pass
                s.file_name = unique
                s.file_mimetype = file.mimetype

            db.session.commit()
            flash("Spectacle mis à jour.", "success")
            return redirect(url_for("company_dashboard"))

        return render_template("show_form_edit.html", show=s, user=u)

    @app.route("/my/shows/<int:show_id>/delete", methods=["POST"], endpoint="show_delete_self")
    @login_required
    def show_delete_self(show_id: int):
        s = Show.query.get_or_404(show_id)
        u = current_user()

        if not (u.is_admin or s.user_id == u.id):
            flash("Accès refusé.", "danger")
            return redirect(url_for("company_dashboard"))

        if s.file_name:
            p = Path(current_app.config["UPLOAD_FOLDER"]) / s.file_name
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        db.session.delete(s)
        db.session.commit()
        flash("Spectacle supprimé.", "success")
        return redirect(url_for("company_dashboard"))

    # ---------------------------
    # Espace Admin
    # ---------------------------
    @app.route("/admin", endpoint="admin_dashboard")
    @login_required
    @admin_required
    def admin_dashboard():
        shows = Show.query.order_by(Show.created_at.desc()).all()
        pending = [s for s in shows if not s.approved]
        return render_template("admin_dashboard.html", user=current_user(), shows=shows, pending=pending)

    @app.route("/admin/shows/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_new():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            location = request.form.get("location", "").strip()
            category = request.form.get("category", "").strip()
            age_range = request.form.get("age_range", "").strip()
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
                from pathlib import Path as _Path
                stem = _Path(file.filename).stem
                ext = _Path(file.filename).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())
                file_name = unique
                file_mimetype = file.mimetype

            show = Show(
                title=title,
                description=description,
                location=location,
                category=category,
                age_range=age_range or None,
                date=date_val,
                file_name=file_name,
                file_mimetype=file_mimetype,
                approved=False,
            )
            db.session.add(show)
            db.session.commit()
            flash("Annonce créée (en attente).", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_new.html", user=current_user())

    @app.route("/admin/shows/<int:show_id>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def show_edit(show_id: int):
        show = Show.query.get_or_404(show_id)

        if request.method == "POST":
            show.title = request.form.get("title", "").strip()
            show.description = request.form.get("description", "").strip()
            show.location = request.form.get("location", "").strip()
            show.category = request.form.get("category", "").strip()
            show.company_name = request.form.get("company_name", "").strip() or None
            date_str = request.form.get("date", "").strip()
            if date_str:
                try:
                    show.date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    flash("Format de date invalide (AAAA-MM-JJ).", "warning")
            else:
                show.date = None

            # Upload fichier principal (affiche/PDF)
            file = request.files.get("file")
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash("Type de fichier non autorisé (png/jpg/jpeg/gif/webp/pdf).", "danger")
                    return redirect(request.url)
                from pathlib import Path as _Path
                stem = _Path(file.filename).stem
                ext = _Path(file.filename).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique
                file.save(save_path.as_posix())

                if show.file_name:
                    old_path = _Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name
                    if old_path.exists():
                        try:
                            old_path.unlink()
                        except Exception:
                            pass

                show.file_name = unique
                show.file_mimetype = file.mimetype

            # 🆕 Upload photo de compagnie
            company_photo = request.files.get("company_photo")
            if company_photo and company_photo.filename:
                if not allowed_file(company_photo.filename):
                    flash("Type de fichier non autorisé pour la photo (png/jpg/jpeg/gif/webp).", "danger")
                    return redirect(request.url)
                from pathlib import Path as _Path
                stem = _Path(company_photo.filename).stem
                ext = _Path(company_photo.filename).suffix
                unique = f"{stem}-{int(datetime.utcnow().timestamp())}{ext}"
                save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique
                company_photo.save(save_path.as_posix())

                if show.company_photo:
                    old_path = _Path(current_app.config["UPLOAD_FOLDER"]) / show.company_photo
                    if old_path.exists():
                        try:
                            old_path.unlink()
                        except Exception:
                            pass

                show.company_photo = unique

            db.session.commit()
            flash("Annonce mise à jour.", "success")
            return redirect(url_for("admin_dashboard"))

        return render_template("show_form_edit.html", show=show, user=current_user())

    @app.route("/admin/shows/<int:show_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def show_delete(show_id: int):
        show = Show.query.get_or_404(show_id)

        if show.file_name:
            p = Path(current_app.config["UPLOAD_FOLDER"]) / show.file_name
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        db.session.delete(show)
        db.session.commit()
        flash("Annonce supprimée.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/shows/<int:show_id>/approve", methods=["POST"])
    @login_required
    @admin_required
    def show_approve(show_id: int):
        show = Show.query.get_or_404(show_id)
        show.approved = True
        db.session.commit()
        flash("Annonce validée ✅", "success")
        return redirect(url_for("admin_dashboard"))

    # ---------------------------
    # Pages diverses
    # ---------------------------
    @app.route("/demande_animation")
    def demande_animation():
        return render_template("demande_animation.html", user=current_user())

    # ---------------------------
    # Recherche géolocalisée (optionnelle)
    # ---------------------------
    from math import radians, sin, cos, asin

    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * R * asin(a ** 0.5)

    try:
        from geopy.geocoders import Nominatim  # type: ignore
    except Exception:  # pragma: no cover
        Nominatim = None  # type: ignore

    def geocode(addr: str) -> Tuple[Optional[float], Optional[float]]:
        if not Nominatim:
            return None, None
        geo = Nominatim(user_agent="artemisia")
        try:
            loc = geo.geocode(addr)
            if loc:
                return float(loc.latitude), float(loc.longitude)
        except Exception:
            pass
        return None, None

    @app.route("/search", methods=["GET"])
    def search():
        q = request.args.get("q", "").strip()
        addr = request.args.get("address", "").strip()
        rad = request.args.get("radius", "20").strip()
        try:
            radius = float(rad)
        except Exception:
            radius = 20.0

        lat = request.args.get("lat")
        lng = request.args.get("lng")

        # 1) centre GPS
        if lat and lng:
            try:
                center = (float(lat), float(lng))
            except Exception:
                center = (None, None)
        else:
            center = geocode(addr)

        # 2) recherche textuelle
        base = Show.query
        if q:
            like = f"%{q}%"
            base = base.filter(Show.title.ilike(like) | Show.description.ilike(like))

        shows = base.all()
        results = []

        # 3) filtrage par distance
        if center and center[0] and center[1]:
            c_lat, c_lng = center
            for s in shows:
                if getattr(s, "latitude", None) and getattr(s, "longitude", None):
                    d = distance_km(c_lat, c_lng, float(s.latitude), float(s.longitude))
                    if d <= radius:
                        results.append((s, round(d, 1)))
            results.sort(key=lambda x: x[1])
        else:
            results = [(s, None) for s in shows]

        return render_template("search.html", results=results, q=q, address=addr, radius=radius)

# -----------------------------------------------------
# Entrée
# -----------------------------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
