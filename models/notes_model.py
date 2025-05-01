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
        raise ValueError("Note déjà enregistrée pour cet étudiant dans cette matière")

    note_data = {
        "numero_etudiant": numero_etudiant,
        "id_matiere": ObjectId(id_matiere),
        "note": note
    }
    notes_collection.insert_one(note_data)

    note_data = {
        "numero_etudiant": numero_etudiant,
        "id_matiere": ObjectId(id_matiere),
        "note": float(note)
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

def calculer_moyenne_etudiant(notes_etudiant):
            if not notes_etudiant:
                return 0
            
            total_coefficient = sum(note['coefficient'] for note in notes_etudiant)
            total_notes = sum(note['note'] * note['coefficient'] for note in notes_etudiant)
            return total_notes / total_coefficient if total_coefficient > 0 else 0


