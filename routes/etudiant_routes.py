from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from config.db import infos_collection, matieres_collection, notes_collection, reclamation_collection
from bson.objectid import ObjectId
import pdfkit  # wkhtmltopdf doit être installé
import os
from datetime import datetime

student_bp = Blueprint("student", __name__)


# Dashboard étudiant (exemple temporaire)
# Dashboard étudiant
@student_bp.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return redirect(url_for('auth.connexion'))
    
    return render_template("etudiant/etudiant_dashboard.html", user=user)

# Info pour la matière
@student_bp.route('/etudiant/matieres')
def voir_matieres():
    email = session.get('user_email')

    if not email:
        return redirect(url_for('auth.connexion'))

    user = infos_collection.find_one({"email": email, "role": "etudiant", "approuve": True})

    if not user:
        return "Étudiant introuvable ou session invalide", 404

    parcours = user.get("parcours")
    niveau = user.get("niveau")
    matieres = matieres_collection.find({
        "parcours": parcours,
        "niveau": niveau
    })

    return render_template("etudiant/etudiant_matieres.html", user=user, matieres=matieres)

# Liste des etudiants
@student_bp.route('/etudiant/etudiants')
def liste_etudiants():
    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "etudiant", "approuve": True})

    if not user:
        return redirect(url_for('auth.connexion'))

    parcours = user.get("parcours")
    niveau = user.get("niveau")
    etudiants = list(infos_collection.find({
        "role": "etudiant",
        "parcours": parcours,
        "niveau": niveau
    }).sort("nom", 1))  # Tri alphabétique

    return render_template("etudiant/liste_etudiants.etudiants.html", etudiants=etudiants, user=user)

# Afficher le profil
@student_bp.route('/profil/<id>', methods=["GET"])
def profil(id):
    if not session.get('user_email'):
        return redirect(url_for('auth.connexion'))
    
    etudiants = infos_collection.find_one({"_id": ObjectId(id), "approuve": True})
    user = infos_collection.find_one({"email": session.get('user_email')})
    return render_template("etudiant/profil.html", etudiants=etudiants, user=user)

# Pour les notes détaillées
@student_bp.route('/etudiant/mes-notes')
def mes_notes():
    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "etudiant"})
    if not user:
        return redirect(url_for("auth.connexion"))

    parcours = user.get("parcours")
    niveau = user.get("niveau")  
    matieres = matieres_collection.find({
        "parcours": parcours,
        "niveau": niveau
    })

    matieres_list = list(matieres)
 
    notes = notes_collection.find({"numero_etudiant": user["numero"]})
    notes_dict = {note["id_matiere"]: note["note"] for note in notes}

    # Calcul de la moyenne pondérée
    total = 0
    total_coeff = 0
    for matiere in matieres_list:
        note = notes_dict.get(matiere["_id"], 0)  # Utiliser 0 si la note est absente
        coeff = matiere.get("coefficient", 1)
        total += note * coeff
        total_coeff += coeff

    moyenne = round(total / total_coeff, 2) if total_coeff > 0 else "Non disponible"

    # Passer l'ID de l'utilisateur au template
    user_id = str(user["_id"])

    return render_template("etudiant/mes_notes.html", user=user, matieres=matieres_list, 
                          notes_dict=notes_dict, moyenne=moyenne, user_id=user_id)


# Réclamation
@student_bp.route('/etudiant/reclamation/<matiere_id>', methods=['GET', 'POST'])
def reclamation(matiere_id):
    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "etudiant"})
    
    if not user:
        return redirect(url_for("auth.connexion"))
    
    matiere = matieres_collection.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        return redirect(url_for('student.mes_notes'))

    if request.method == 'POST':
        commentaire = request.form.get('commentaire')

        if commentaire:
            reclamation_data = {
                "numero_etudiant": user["numero"],
                "nom_etudiant": user["nom"],
                "matiere_id": matiere_id,
                "nom_matiere": matiere["nom"],
                "commentaire": commentaire,
                "enseignant_nom": matiere["professeur"],
                "status": "En attente"
            }
            reclamation_collection.insert_one(reclamation_data)

            # Confirmation de soumission
            flash("Réclamation soumise avec succès.", "success")
            return redirect(url_for('student.mes_notes'))
        else:
            flash("Veuillez remplir le champ de réclamation.", "error")
            return redirect(url_for('student.reclamation', matiere_id=matiere_id))
        
    return render_template("etudiant/etudiant_reclamation.html", user=user, matiere=matiere, matiere_id=matiere_id)
    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "etudiant"})
    
    if not user:
        return redirect(url_for("auth.connexion"))
    
    matiere = matieres_collection.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        return redirect(url_for('student.mes_notes'))

    if request.method == 'POST':
        commentaire = request.form.get('commentaire')

        if commentaire:
            reclamation_data = {
                "numero_etudiant": user["numero"],
                "nom_etudiant": user["nom"],
                "matiere_id": matiere_id,
                "nom_matiere": matiere["nom"],
                "commentaire": commentaire,
                "enseignant_nom": matiere["professeur"],
                "status": "En attente"
            }
            reclamation_collection.insert_one(reclamation_data)

            # Confirmation de soumission
            flash("Réclamation soumise avec succès.", "success")
            return redirect(url_for('student.mes_notes'))
        else:
            flash("Veuillez remplir le champ de réclamation.", "error")
            return redirect(url_for('student.reclamation', matiere_id=matiere_id))
        
    return render_template("etudiant/etudiant_reclamation.html", user=user, matiere=matiere, matiere_id=matiere_id)

# Generer pdf
'''@student_bp.route('/generer_pdf/<etudiant_id>')
def generer_pdf(etudiant_id):
    etudiant_id = session.get('user_id')

    print(f"Etudiant ID: {etudiant_id}")

    etudiant = infos_collection.find_one({"_id": ObjectId(etudiant_id)})
    if not etudiant:
        return "Étudiant introuvable", 404

    # Récupération des notes
    numero = etudiant["numero"]
    notes_etudiant = notes_collection.find({"numero_etudiant": numero})

    # Construire un dictionnaire : {id_matiere : note}
    notes = {str(note_doc["id_matiere"]): note_doc["note"] for note_doc in notes_etudiant}

    matieres = list(matieres_collection.find({
    "parcours": etudiant["parcours"],
    "niveau": etudiant["niveau"]
    }))

    moyenne = etudiant.get("moyenne", 0)
 
    notes_par_nom = {}
    for matiere in matieres:
        matiere_id = str(matiere["_id"])

        notes_par_nom[matiere["nom"]] = notes.get(matiere_id, "—")

    html = render_template("admin/pdf_template.html",
                           etudiant=etudiant,
                           notes=notes_par_nom,
                           matieres=matieres,
                           moyenne=moyenne,
                           rang=None,
                           current_date=datetime.now().strftime("%d/%m/%Y"))

    # Chemin du fichier PDF à sauvegarder
    dossier_bulletins = "bulletins"
    nom_fichier = f"Bulletin_{etudiant['numero']}.pdf"
    chemin_fichier = os.path.join(dossier_bulletins, nom_fichier)

    # Génére et sauvegarde le PDF dans le dossier
    pdfkit.from_string(html, chemin_fichier)

    # Envoie le fichier PDF en réponse
    return send_file(chemin_fichier, as_attachment=False)
'''
@student_bp.route('/generer_pdf/<etudiant_id>')
def generer_pdf(etudiant_id):
    # if 'user_email' not in session or session.get('role') != 'admin':
    #     return redirect(url_for('auth.connexion'))
    
    etudiant = infos_collection.find_one({"_id": ObjectId(etudiant_id)})
    if not etudiant:
        return "Étudiant introuvable", 404

    # Récupération des notes
    numero = etudiant["numero"]
    notes_etudiant = notes_collection.find({"numero_etudiant": numero})

    # Construire un dictionnaire : {id_matiere : note}
    notes = {str(note_doc["id_matiere"]): note_doc["note"] for note_doc in notes_etudiant}

    matieres = list(matieres_collection.find({
    "parcours": etudiant["parcours"],
    "niveau": etudiant["niveau"]
    }))

    moyenne = etudiant.get("moyenne", 0)
 
    notes_par_nom = {}
    for matiere in matieres:
        matiere_id = str(matiere["_id"])
        notes_par_nom[matiere["nom"]] = notes.get(matiere_id, "—")

    html = render_template("admin/pdf_template.html",
                           etudiant=etudiant,
                           notes=notes_par_nom,
                           matieres=matieres,
                           moyenne=moyenne,
                           rang=None,
                           current_date=datetime.now().strftime("%d/%m/%Y"))

    # Chemin du fichier PDF à sauvegarder
    dossier_bulletins = "bulletins"
    
    # Créer le dossier s'il n'existe pas
    if not os.path.exists(dossier_bulletins):
        os.makedirs(dossier_bulletins)
        
    nom_fichier = f"Bulletin_{etudiant['numero']}.pdf"
    chemin_fichier = os.path.join(dossier_bulletins, nom_fichier)

    # Configuration de pdfkit avec le chemin explicite vers wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')  # Ajustez ce chemin selon votre installation
    
    # Génère et sauvegarde le PDF dans le dossier
    pdfkit.from_string(html, chemin_fichier, configuration=config)

    # Envoie le fichier PDF en réponse
    return send_file(chemin_fichier, as_attachment=False)
