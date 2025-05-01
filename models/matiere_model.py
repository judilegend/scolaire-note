from config.db import matieres_collection
from bson.objectid import ObjectId

# Ajouter une matière avec niveau et parcours
def ajouter_matiere(nom, coefficient, professeur, niveau, parcours):
    matieres_collection.insert_one({
        "nom": nom,
        "coefficient": float(coefficient),
        "professeur": professeur,
        "niveau": niveau,
        "parcours": parcours
    })

# Récupérer toutes les matières
def get_all_matieres():
    return list(matieres_collection.find())

# Récupérer une matière spécifique
def get_matiere_by_id(matiere_id):
    return matieres_collection.find_one({'_id': ObjectId(matiere_id)})

# Supprimer une matière
def supprimer_matiere(id_matiere):
    from bson.objectid import ObjectId
    matieres_collection.delete_one({"_id": ObjectId(id_matiere)})

# Modifier une matière
def modifier_matiere(matiere_id, nom, coefficient, professeur, niveau, parcours):
    matieres_collection.update_one(
        {"_id": ObjectId(matiere_id)},
        {"$set": {
            "nom": nom,
            "coefficient": float(coefficient),
            "professeur": professeur,
            "niveau": niveau,
            "parcours": parcours
        }}
    )