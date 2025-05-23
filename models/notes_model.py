from config.db import notes_collection
from bson.objectid import ObjectId

def ajouter_note(numero_etudiant, id_matiere, note):
    note = float(note)
    if not (0 <= note <= 20):
        raise ValueError("La note doit être un nombre entre 0 et 20")

    # Vérifier si une note existe déjà pour cet étudiant et cette matière
    existante = notes_collection.find_one({
        "numero_etudiant": numero_etudiant,
        "id_matiere": ObjectId(id_matiere)
    })
    
    if existante:
        # Mettre à jour la note existante au lieu de lever une erreur
        notes_collection.update_one(
            {"_id": existante["_id"]},
            {"$set": {"note": note}}
        )
        return {"success": "Note mise à jour"}

    note_data = {
        "numero_etudiant": numero_etudiant,
        "id_matiere": ObjectId(id_matiere),
        "note": note
    }
    notes_collection.insert_one(note_data)
    return {"success": "Note ajoutée"}

def get_notes_etudiant(numero_etudiant):
    return list(notes_collection.find({"numero_etudiant": numero_etudiant}))

def get_toutes_notes():
    return list(notes_collection.find())

def supprimer_note(note_id):
    notes_collection.delete_one({"_id": ObjectId(note_id)})

def supprimer_notes_par_etudiant(numero_etudiant):
    notes_collection.delete_many({"numero_etudiant": numero_etudiant})


def modifier_note(note_id, nouvelle_note):
    notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": {"note": float(nouvelle_note)}}
    )

# def calculer_moyenne_etudiant(notes_etudiant):
#             if not notes_etudiant:
#                 return 0
            
#             total_coefficient = sum(note['coefficient'] for note in notes_etudiant)
#             total_notes = sum(note['note'] * note['coefficient'] for note in notes_etudiant)
#             return total_notes / total_coefficient if total_coefficient > 0 else 0

def calculer_moyenne_etudiant(notes_etudiant):
    """Calcule la moyenne d'un étudiant en fonction de ses notes et des coefficients des matières"""
    if not notes_etudiant:
        return 0
    
    total_coefficient = sum(note['coefficient'] for note in notes_etudiant)
    total_notes = sum(note['note'] * note['coefficient'] for note in notes_etudiant)
    return total_notes / total_coefficient if total_coefficient > 0 else 0
def calculer_moyennes_tous_etudiants():
    """Calcule les moyennes de tous les étudiants et retourne un tableau trié par moyenne décroissante"""
    from models.user_model import get_all_students
    from config.db import matieres_collection
    
    etudiants = get_all_students()
    tableau = []
    
    for etudiant in etudiants:
        notes_etudiant = []
        for note_doc in notes_collection.find({"numero_etudiant": etudiant.get("numero", "")}):
            matiere = matieres_collection.find_one({"_id": note_doc["id_matiere"]})
            if matiere:
                notes_etudiant.append({
                    "note": note_doc["note"],
                    "coefficient": matiere.get("coefficient", 1)
                })
        
        moyenne = calculer_moyenne_etudiant(notes_etudiant)
        
        # Déterminer la recommandation
        recommandation = "Non évalué"
        if notes_etudiant:  # Si l'étudiant a des notes
            if moyenne >= 10:
                recommandation = "Admis"
            else:
                recommandation = "Redouble"
        
        tableau.append({
            "_id": etudiant["_id"],
            "numero": etudiant.get("numero", ""),
            "nom": etudiant.get("nom", ""),
            "email": etudiant.get("email", ""),
            "niveau": etudiant.get("niveau", ""),
            "parcours": etudiant.get("parcours", ""),
            "moyenne": moyenne,
            "recommandation": recommandation
        })
    
    # Trier par moyenne décroissante
    tableau_trie = sorted(tableau, key=lambda x: x["moyenne"], reverse=True)
    
    # Ajouter le rang
    for i, etud in enumerate(tableau_trie):
        etud["rang"] = i + 1
    
    return tableau_trie


    """Calcule les moyennes de tous les étudiants et retourne un tableau trié par moyenne décroissante"""
    from models.etudiants_model import get_tous_etudiants
    from models.matieres_model import get_matiere_by_id
    
    etudiants = get_tous_etudiants()
    tableau = []
    
    for etudiant in etudiants:
        notes_etudiant = []
        for note_doc in notes_collection.find({"numero_etudiant": etudiant["numero"]}):
            matiere = get_matiere_by_id(str(note_doc["id_matiere"]))
            if matiere:
                notes_etudiant.append({
                    "note": note_doc["note"],
                    "coefficient": matiere.get("coefficient", 1)
                })
        
        moyenne = calculer_moyenne_etudiant(notes_etudiant)
        
        # Déterminer la recommandation
        recommandation = "Non évalué"
        if moyenne > 0:
            if moyenne >= 10:
                recommandation = "Admis"
            else:
                recommandation = "Redouble"
        
        tableau.append({
            "_id": etudiant["_id"],
            "numero": etudiant["numero"],
            "nom": etudiant["nom"],
            "email": etudiant.get("email", ""),
            "niveau": etudiant["niveau"],
            "parcours": etudiant["parcours"],
            "moyenne": moyenne,
            "recommandation": recommandation
        })
    
    # Trier par moyenne décroissante
    tableau_trie = sorted(tableau, key=lambda x: x["moyenne"], reverse=True)
    
    # Ajouter le rang
    for i, etud in enumerate(tableau_trie):
        etud["rang"] = i + 1
    
    return tableau_trie


def calculer_moyenne_complete(numero_etudiant):
    from config.db import notes_collection, matieres_collection
    
    # Récupérer toutes les notes de l'étudiant
    notes_etudiant = list(notes_collection.find({"numero_etudiant": numero_etudiant}))
    
    # Préparer les données pour le calcul de la moyenne
    notes_avec_details = []
    somme_ponderee = 0
    somme_coefficients = 0
    
    for note_doc in notes_etudiant:
        matiere = matieres_collection.find_one({"_id": note_doc["id_matiere"]})
        if matiere:
            coefficient = matiere.get("coefficient", 1)
            note_valeur = note_doc["note"]
            
            # Ajouter à la somme pondérée
            somme_ponderee += note_valeur * coefficient
            somme_coefficients += coefficient
            
            # Stocker les détails pour référence
            notes_avec_details.append({
                "id_note": note_doc["_id"],
                "matiere": matiere.get("nom", "Inconnue"),
                "coefficient": coefficient,
                "note": note_valeur,
                "note_ponderee": note_valeur * coefficient
            })
    
    # Calculer la moyenne
    moyenne = 0
    if somme_coefficients > 0:
        moyenne = round(somme_ponderee / somme_coefficients, 2)
        
    return (moyenne, notes_avec_details)

def calculer_moyennes_tous_etudiants():
    """
    Calcule les moyennes de tous les étudiants.
    
    Returns:
        list: Liste de dictionnaires contenant les informations des étudiants avec leurs moyennes
    """
    from models.user_model import get_all_students
    from config.db import infos_collection
    
    etudiants = get_all_students()
    resultats = []
    
    for etudiant in etudiants:
        moyenne, _ = calculer_moyenne_complete(etudiant.get("numero", ""))
        
        # Déterminer la recommandation
        recommandation = "Non évalué"
        if moyenne > 0:  # Si l'étudiant a des notes
            if moyenne >= 10:
                recommandation = "Admis"
            else:
                recommandation = "Redouble"
        
        # Mettre à jour la moyenne dans la base de données
        infos_collection.update_one(
            {"_id": etudiant["_id"]},
            {"$set": {"moyenne": moyenne}}
        )
        
        resultats.append({
            "_id": etudiant["_id"],
            "numero": etudiant.get("numero", ""),
            "nom": etudiant.get("nom", ""),
            "email": etudiant.get("email", ""),
            "niveau": etudiant.get("niveau", ""),
            "parcours": etudiant.get("parcours", ""),
            "moyenne": moyenne,
            "recommandation": recommandation
        })
    
    return resultats
