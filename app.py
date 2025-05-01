from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os

from config.db import notes_collection, matieres_collection, infos_collection, reclamation_collection

# Chargement des variables d’environnement
load_dotenv()

# Initialisation de l'app Flask
app = Flask(__name__)
CORS(app)

# Clé secrète pour les sessions
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

# Test de connexion MongoDB
try:
    test = infos_collection.find_one()
    print("✅ Connexion MongoDB réussie !")
except Exception as e:
    print("❌ Erreur de connexion MongoDB :", e)

# Importation des blueprints
from routes.auth_routes import auth_bp
from routes.etudiant_routes import student_bp
from routes.admin_routes import admin_bp
from routes.enseignant_routes import enseignant_bp

# Route d'accueil
@app.route('/')
def accueil():
    return render_template('accueil.html')

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(enseignant_bp, url_prefix='/enseignant')

# infos_collection.delete_many({})
# matieres_collection.delete_many({})
# notes_collection.delete_many({})
# reclamation_collection.delete_many({})

# Lancement de l'application
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
