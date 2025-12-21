from app import app
from models.models import db

with app.app_context():
    db.create_all()
    print('Tables créées avec succès dans la base de données.')
