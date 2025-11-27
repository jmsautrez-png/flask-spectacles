import os
from flask import Flask, request, render_template, redirect, url_for, flash

# Création de l'app Flask
app = Flask(__name__)
app.secret_key = "change-moi-en-chaine-secrete"  # nécessaire pour flash()

# Dossier où est monté ton disque Render
DATA_DIR = "/data/cards"
os.makedirs(DATA_DIR, exist_ok=True)

# Limite : 400 Ko
MAX_IMAGE_SIZE = 200 * 1024  # en octets


@app.route("/", methods=["GET"])
def index():
    # Affiche simplement le formulaire
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    # Récupération des champs du formulaire
    user_id = request.form.get("user_id", "").strip()
    texte = request.form.get("texte", "").strip()
    image = request.files.get("image")

    # Vérifications simples
    if not user_id:
        flash("Veuillez entrer un identifiant utilisateur.")
        return redirect(url_for("index"))

    if not image:
        flash("Veuillez sélectionner une image.")
        return redirect(url_for("index"))

    # Vérifier la taille de l'image
    content = image.read()
    if len(content) > MAX_IMAGE_SIZE:
        flash("Image trop grande (maximum 200 Ko).")
        return redirect(url_for("index"))

    # Revenir au début du fichier pour pouvoir le sauvegarder
    image.stream.seek(0)

    # Créer un dossier pour cet utilisateur sur le disque
    user_dir = os.path.join(DATA_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    # Sauvegarder l'image
    image_path = os.path.join(user_dir, "image.jpg")
    image.save(image_path)

    # Sauvegarder le texte
    texte_path = os.path.join(user_dir, "texte.txt")
    with open(texte_path, "w", encoding="utf-8") as f:
        f.write(texte)

    flash("Carte enregistrée avec succès !")
    return redirect(url_for("index"))


@app.route("/list")
def list_cards():
    """
    Petite page pour lister les utilisateurs qui ont une carte.
    (optionnel mais pratique pour tester)
    """
    users = []
    if os.path.exists(DATA_DIR):
        for uid in os.listdir(DATA_DIR):
            users.append(uid)
    return "<br>".join(f"Utilisateur : {u}" for u in users) or "Aucune carte pour le moment."


# Point d'entrée local (optionnel pour tester en local)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
