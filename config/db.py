from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connexion à MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client['etudiant']

# Collections
infos_collection = db['infos']
notes_collection = db['note']
matieres_collection = db['matiere']
reclamation_collection = db['reclamation']
