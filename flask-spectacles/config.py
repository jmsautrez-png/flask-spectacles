import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    INSTANCE_PATH = os.environ.get("INSTANCE_PATH", None)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

    BASE_DIR = Path(__file__).resolve().parent
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


 

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "artemisiacompagnie@gmail.com"
    MAIL_PASSWORD = "gdgg hdat auqu adyq"
    MAIL_DEFAULT_SENDER = "artemisiacompagnie@gmail.com"