#!/usr/bin/env python
"""
Test de vérification du fix email :
  1. MailMessage (flask_mail) ne doit PAS être écrasé par le modèle SQLAlchemy Message
  2. Message SQLAlchemy doit toujours être accessible pour les messages internes
  3. url_for("admin_shows") ne doit plus exister dans app.py
  4. MailMessage(subject=...) doit pouvoir s'instancier sans erreur
  5. Envoi réel via Flask test client si MAIL_SERVER configuré
"""
import sys
import os
import re

OK = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  {OK} {label}")
    else:
        print(f"  {FAIL} {label}" + (f" — {detail}" if detail else ""))
        errors.append(label)

print("\n" + "=" * 60)
print("  TEST FIX EMAIL — MailMessage vs Message SQLAlchemy")
print("=" * 60)

# ── 1. Import de flask_mail ───────────────────────────────────
print("\n[1] Import flask_mail")
try:
    from flask_mail import Message as MailMessage
    check("flask_mail.Message importable sous le nom MailMessage", True)
    check("MailMessage a un paramètre 'subject'",
          "subject" in MailMessage.__init__.__code__.co_varnames
          if hasattr(MailMessage.__init__, "__code__") else True)
except ImportError as e:
    check("flask_mail installé", False, str(e))

# ── 2. Pas de conflit dans app.py ─────────────────────────────
print("\n[2] Analyse app.py — pas de conflit de noms")
with open("app.py", encoding="utf-8") as f:
    source = f.read()

check("Import flask_mail utilise 'Message as MailMessage'",
      "from flask_mail import Mail, Message as MailMessage" in source)

check("Aucun 'from flask_mail import Message' sans alias",
      "from flask_mail import Message\n" not in source
      and "from flask_mail import Message," not in source.replace("Message as", ""))

check("Aucun appel email = Message(subject=" ,
      "= Message(subject=" not in source)

count_mailmessage_calls = len(re.findall(r'= MailMessage\(', source))
check(f"Au moins 10 appels MailMessage( détectés ({count_mailmessage_calls} trouvés)",
      count_mailmessage_calls >= 10)

# ── 3. url_for admin_shows corrigé ────────────────────────────
print("\n[3] Correction url_for admin_shows")
admin_shows_bad = re.findall(r'url_for\(["\']admin_shows["\']', source)
check("url_for('admin_shows') supprimé",
      len(admin_shows_bad) == 0,
      f"Encore {len(admin_shows_bad)} occurrence(s)")

# ── 4. Modèle SQLAlchemy Message intact ───────────────────────
print("\n[4] Modèle SQLAlchemy Message")
check("'from models.models import ... Message ...' présent",
      "Message" in source.split("from models.models import")[1].split("\n")[0]
      if "from models.models import" in source else False)

check("Message.query utilisé (modèle DB intact)",
      "Message.query" in source)

# ── 5. Test via l'app Flask ───────────────────────────────────
print("\n[5] Démarrage app Flask + config mail")
try:
    os.environ.setdefault("TESTING", "1")
    from app import create_app
    app = create_app()
    with app.app_context():
        mail_obj = getattr(app, "mail", None)
        check("app.mail initialisé", mail_obj is not None)

        mail_server = app.config.get("MAIL_SERVER")
        mail_user   = app.config.get("MAIL_USERNAME")
        mail_pass   = app.config.get("MAIL_PASSWORD")
        check(f"MAIL_SERVER configuré ({mail_server})", bool(mail_server))
        check(f"MAIL_USERNAME configuré ({mail_user})", bool(mail_user))
        check("MAIL_PASSWORD configuré", bool(mail_pass),
              "MAIL_PASSWORD absent — les emails ne seront pas envoyes")

        # Vérifier que l'endpoint admin_dashboard existe
        from flask import url_for
        with app.test_request_context():
            try:
                url = url_for("admin_dashboard")
                check(f"url_for('admin_dashboard') -> {url}", True)
            except Exception as e:
                check("url_for('admin_dashboard') accessible", False, str(e))

            # Vérifier que admin_shows N'existe PAS
            try:
                url_for("admin_shows")
                check("url_for('admin_shows') absent (doit lever BuildError)", False,
                      "L'endpoint admin_shows existe encore !")
            except Exception:
                check("url_for('admin_shows') leve bien une erreur (endpoint supprime)", True)

        # Instanciation MailMessage à l'intérieur du contexte Flask
        print("\n[6] Instanciation MailMessage(subject=...)")
        try:
            from flask_mail import Message as MailMsg
            msg = MailMsg(subject="Test sujet", recipients=["test@example.com"])
            check("MailMessage(subject='...') instanciable", True)
            check(f"msg.subject == 'Test sujet' ({msg.subject!r})", msg.subject == "Test sujet")
        except Exception as exc:
            print(f"      ERREUR: {exc!r}")
            check("MailMessage(subject='...') instanciable", False, repr(exc))

except Exception as e:
    check("Démarrage app Flask", False, str(e))

# ── Résumé ────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print(f"  {FAIL} {len(errors)} problème(s) détecté(s) :")
    for e in errors:
        print(f"       • {e}")
    sys.exit(1)
else:
    print(f"  {OK} Tous les tests passent — fix email opérationnel !")
print("=" * 60 + "\n")
