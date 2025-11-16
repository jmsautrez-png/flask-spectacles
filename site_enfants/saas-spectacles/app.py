from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
import json, os

app = Flask(__name__)
app.secret_key = "change-moi"  # pour les messages flash
DATA_FILE = "shows.json"

# ---------- utilitaires ----------
def load_shows():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_shows(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

# ---------- routes ----------
@app.route("/")
def home():
    shows = load_shows()

    # valeurs pour filtres
    villes_all = sorted({(s.get("lieu") or "").strip() for s in shows if (s.get("lieu") or "").strip()})
    ages_all   = sorted({(s.get("age") or "").strip()  for s in shows if (s.get("age") or "").strip()})

    # paramètres
    q         = (request.args.get("q") or "").strip().lower()
    ville_sel = (request.args.get("ville") or "").strip()
    age_sel   = (request.args.get("age") or "").strip()
    date_from = (request.args.get("date_from") or "").strip()
    date_to   = (request.args.get("date_to") or "").strip()
    sort      = (request.args.get("sort") or "date_asc").strip()  # date_asc | date_desc

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to)   if date_to   else None

    # filtrage
    def match(s):
        if q:
            blob = " ".join([
                s.get("titre",""), s.get("compagnie",""),
                s.get("lieu",""),  s.get("description","")
            ]).lower()
            if q not in blob:
                return False
        if ville_sel and s.get("lieu","").strip() != ville_sel:
            return False
        if age_sel and s.get("age","").strip() != age_sel:
            return False
        d = parse_date(s.get("date") or "")
        if df and (not d or d < df): return False
        if dt and (not d or d > dt): return False
        return True

    filtered = [s for s in shows if match(s)]

    # tri par date
    def sort_key(s):
        d = parse_date(s.get("date") or "")
        return (d is None, d or date.max)

    filtered.sort(key=sort_key, reverse=(sort == "date_desc"))

    return render_template(
        "home.html",
        spectacles=filtered,
        villes=villes_all,
        ages=ages_all,
        q=q, ville_sel=ville_sel, age_sel=age_sel,
        date_from=date_from, date_to=date_to, sort=sort
    )

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    shows = load_shows()
    villes_all = sorted({(s.get("lieu") or "").strip() for s in shows if (s.get("lieu") or "").strip()})
    ages_all   = sorted({(s.get("age") or "").strip()  for s in shows if (s.get("age") or "").strip()})

    if request.method == "POST":
        data = {
            "titre":       request.form.get("titre","").strip(),
            "compagnie":   request.form.get("compagnie","").strip(),
            "date":        request.form.get("date","").strip(),
            "lieu":        request.form.get("lieu","").strip(),
            "age":         request.form.get("age","").strip(),
            "prix":        request.form.get("prix","").strip(),
            "site":        request.form.get("site","").strip(),
            "image":       request.form.get("image","").strip(),
            "description": request.form.get("description","").strip(),
        }
        if not data["titre"] or not data["lieu"]:
            flash("Titre et Lieu sont obligatoires.", "error")
            return redirect(url_for("ajouter"))

        shows.append(data)
        save_shows(shows)
        flash("Spectacle ajouté 🎉", "success")
        return redirect(url_for("home"))

    # on réutilise ajouter.html pour créer
    return render_template("ajouter.html", mode="create", villes=villes_all, ages=ages_all)

@app.route("/modifier/<int:index>", methods=["GET", "POST"])
def modifier(index):
    shows = load_shows()
    if not (0 <= index < len(shows)):
        flash("Annonce introuvable.", "error")
        return redirect(url_for("home"))

    villes_all = sorted({(s.get("lieu") or "").strip() for s in shows if (s.get("lieu") or "").strip()})
    ages_all   = sorted({(s.get("age") or "").strip()  for s in shows if (s.get("age") or "").strip()})

    if request.method == "POST":
        s = shows[index]
        s["titre"]       = request.form.get("titre","").strip()
        s["compagnie"]   = request.form.get("compagnie","").strip()
        s["date"]        = request.form.get("date","").strip()
        s["lieu"]        = request.form.get("lieu","").strip()
        s["age"]         = request.form.get("age","").strip()
        s["prix"]        = request.form.get("prix","").strip()
        s["site"]        = request.form.get("site","").strip()
        s["image"]       = request.form.get("image","").strip()
        s["description"] = request.form.get("description","").strip()

        if not s["titre"] or not s["lieu"]:
            flash("Titre et Lieu sont obligatoires.", "error")
            return redirect(url_for("modifier", index=index))

        save_shows(shows)
        flash("Annonce mise à jour ✅", "success")
        return redirect(url_for("home"))

    # GET : formulaire pré-rempli
    return render_template("ajouter.html", mode="edit", i=index, show=shows[index],
                           villes=villes_all, ages=ages_all)

@app.route("/supprimer/<int:index>", methods=["POST"])
def supprimer(index):
    shows = load_shows()
    if 0 <= index < len(shows):
        titre = shows[index].get("titre","(sans titre)")
        shows.pop(index)
        save_shows(shows)
        flash(f"Spectacle supprimé : {titre}", "success")
    else:
        flash("Index invalide.", "error")
    return redirect(url_for("home"))

if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        save_shows([])
    app.run(debug=True)
