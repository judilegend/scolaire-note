from flask import Blueprint, render_template, session, Blueprint, request, redirect, url_for, flash
from config.db import infos_collection, matieres_collection, reclamation_collection, notes_collection
from bson import ObjectId
import smtplib
from email.mime.text import MIMEText

# Créer une instance de Blueprint pour les routes de l'enseignant
enseignant_bp = Blueprint('enseignant', __name__)

# Tableau de bord enseignant
# Tableau de bord enseignant
@enseignant_bp.route('/dashboard')
def dashboard():
    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "enseignant", "approuve": True})

    if not user:
        return redirect(url_for("auth.connexion"))

    # Récupérer les matières enseignées par ce professeur
    matieres = list(matieres_collection.find({"professeur": user["nom"]}))
    
    # Compter le nombre total de matières
    total_matieres = len(matieres)
    
    # Récupérer les réclamations en attente
    reclamations = list(reclamation_collection.find({"enseignant_nom": user["nom"], "status": "En attente"}))
    reclamations_count = len(reclamations)
    
    # Calculer le nombre total d'étudiants pour les matières enseignées
    total_etudiants = 0
    parcours_niveaux = set()
    
    for matiere in matieres:
        parcours = matiere.get("parcours")
        niveau = matiere.get("niveau")
        if parcours and niveau:
            parcours_niveaux.add((parcours, niveau))
    
    # Compter les étudiants uniques dans les classes où l'enseignant enseigne
    for parcours, niveau in parcours_niveaux:
        etudiants_count = infos_collection.count_documents({
            "role": "etudiant",
            "approuve": True,
            "parcours": parcours,
            "niveau": niveau
        })
        total_etudiants += etudiants_count
    
    # Compter le nombre total de notes saisies par cet enseignant
    total_notes = 0
    for matiere in matieres:
        notes_count = notes_collection.count_documents({"id_matiere": matiere["_id"]})
        total_notes += notes_count

    return render_template("enseignant/enseignant_dashboard.html", 
                          user=user, 
                          matieres=matieres, 
                          reclamations=reclamations,
                          reclamations_count=reclamations_count,
                          total_matieres=total_matieres,
                          total_etudiants=total_etudiants,
                          total_notes=total_notes)

# ROUTE POUR AFFICHER LES NOTES
@enseignant_bp.route('/matiere/<matiere_id>/notes', methods=['GET'])
def gerer_notes(matiere_id):
    if "user_email" not in session:
        return redirect(url_for("auth.connexion"))

    email = session.get('user_email')
    user = infos_collection.find_one({"email": email, "role": "enseignant", "approuve": True})
    
    matiere_id_obj = ObjectId(matiere_id)
    matiere = matieres_collection.find_one({"_id": matiere_id_obj})
    if not matiere:
        return "Matière introuvable", 404

    # Étudiants concernés par parcours + niveau
    etudiants = list(infos_collection.find({
        "role": "etudiant",
        "approuve": True,
        "parcours": matiere["parcours"],
        "niveau": matiere["niveau"]
    }).sort("nom", 1))

    # Notes existantes pour la matière
    notes_cursor = notes_collection.find({"id_matiere": matiere_id_obj})
    notes = {note["numero_etudiant"]: note["note"] for note in notes_cursor}
    
    # Récupérer les réclamations pour le compteur
    reclamations = list(reclamation_collection.find({"enseignant_nom": user["nom"], "status": "En attente"}))
    reclamations_count = len(reclamations)
    
    # Récupérer les matières pour le menu déroulant
    matieres = matieres_collection.find({"professeur": user["nom"]})

    return render_template("enseignant/enseignant_notes_matiere.html", 
        matiere=matiere,
        etudiants=etudiants,
        notes=notes,  # Changé de note_dict à notes
        user=user,
        reclamations_count=reclamations_count,
        matieres=matieres
    )

# ROUTE POUR ENREGISTRER/MODIFIER LES NOTES
@enseignant_bp.route('/matiere/<matiere_id>/notes/update', methods=['POST'])
def enregistrer_notes(matiere_id):
    if "user_email" not in session:
        return redirect(url_for("auth.connexion"))
    
    matiere_id_obj = ObjectId(matiere_id)
    matiere = matieres_collection.find_one({"_id": matiere_id_obj})
    if not matiere:
        return "Matière non trouvée", 404

    for key in request.form:
        if key.startswith('note_'):
            numero = key.split('_')[1]
            try:
                note = float(request.form[key])
            except ValueError:
                continue  # Ignore si la note n'est pas valide

            # Mise à jour ou insertion
            notes_collection.update_one(
                {"numero_etudiant": numero, "id_matiere": matiere_id_obj},
                {"$set": {"note": note}},
                upsert=True
            )
    flash("Les notes ont été enregistrées avec succès.")
    return redirect(url_for('enseignant.gerer_notes', matiere_id=matiere_id))

# Reclamation
@enseignant_bp.route('/reclamations/<matiere_id>', methods=['GET'])
def liste_reclamations(matiere_id):
    email = session.get('user_email')
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})
    
    if not enseignant:
        return redirect(url_for("auth.connexion"))

    nom_enseignant = enseignant.get("nom")
    matiere = matieres_collection.find_one({
        "_id": ObjectId(matiere_id),
        "professeur": nom_enseignant
    })

    if not matiere:
        flash("Matière introuvable ou non autorisée.", "error")
        return redirect(url_for("enseignant.dashboard"))

    reclamations = list(reclamation_collection.find({
        "enseignant_nom": nom_enseignant,
        "matiere_id": matiere_id
    }))
    
    # Récupérer les réclamations en attente pour le compteur
    reclamations_en_attente = list(reclamation_collection.find({"enseignant_nom": nom_enseignant, "status": "En attente"}))
    reclamations_count = len(reclamations_en_attente)
    
    # Récupérer les matières pour le menu déroulant
    matieres = matieres_collection.find({"professeur": nom_enseignant})

    return render_template("enseignant/enseignant_reclamations.html",
                           enseignant=enseignant,
                           user=enseignant,  # Ajout de user pour layout.html
                           matiere=matiere,
                           reclamations=reclamations,
                           reclamations_count=reclamations_count,
                           matieres=matieres)
# Repondre reclamation
def send_email(to_email, subject, body):
    from_email = "olivandry.777@gmail.com"
    password = "zzlr wcsw rdmg hzzu"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, [to_email], msg.as_string())
        print("Email envoyé à", to_email)
    except Exception as e:
        print("Erreur lors de l'envoi de l'email :", e)

# Route pour repondre la reclamation
@enseignant_bp.route('/reclamation/<reclamation_id>/<action>', methods=['GET'])
def repondre_reclamation(reclamation_id, action):
    email = session.get('user_email')
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})

    if not enseignant:
        return redirect(url_for("auth.connexion"))

    reclamation = reclamation_collection.find_one({"_id": ObjectId(reclamation_id)})

    if not reclamation:
        flash("Réclamation introuvable.", "error")
        return redirect(url_for("enseignant.liste_reclamations"))

    # Mise à jour du statut
    if action == "accepter":
        new_status = "Acceptée"
    elif action == "refuser":
        new_status = "Refusée"
    else:
        flash("Action invalide.", "error")
        return redirect(url_for("enseignant.liste_reclamations"))

    # Met à jour la réclamation
    reclamation_collection.update_one(
        {"_id": ObjectId(reclamation_id)},
        {"$set": {"status": new_status}}
    )

    # Récupère les infos de l'étudiant
    etudiant = infos_collection.find_one({"numero": reclamation["numero_etudiant"]})
    if etudiant:
        msg = f"Bonjour {etudiant['nom']},\n\nVotre réclamation pour la matière {reclamation['nom_matiere']} a été {new_status.lower()} par l'enseignant.\n\nMerci."
        send_email(etudiant["email"], "Réclamation - Résultat", msg)

    flash(f"Réclamation {new_status.lower()} avec succès.", "success")

    # Redirection
    if new_status == "Acceptée":
        return redirect(url_for("enseignant.gerer_notes", matiere_id=reclamation["matiere_id"]))
    else:
        return redirect(url_for("enseignant.liste_reclamations", matiere_id=reclamation["matiere_id"]))


# Supprimer les reclamations traité par matiere
@enseignant_bp.route('/reclamations/<matiere_id>/supprimer_traitees', methods=['POST'])
def supprimer_reclamations_traitees_matiere(matiere_id):
    email = session.get("user_email")
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})
    if not enseignant:
        flash("Accès non autorisé.", "error")
        return redirect(url_for("auth.connexion"))

    nom_enseignant = enseignant.get("nom")
    matiere = matieres_collection.find_one({
        "_id": ObjectId(matiere_id),
        "professeur": nom_enseignant
    })
    if not matiere:
        flash("Matière introuvable ou non autorisée.", "error")
        return redirect(url_for("enseignant.dashboard"))

    # Supprimer les réclamations traitées (acceptées ou refusées) pour cette matière
    resultat = reclamation_collection.delete_many({
        "matiere_id": matiere_id,
        "enseignant_nom": nom_enseignant,
        "status": {"$ne": "En attente"}
    })

    flash(f"{resultat.deleted_count} réclamation(s) traitée(s) supprimée(s) pour la matière {matiere['nom']}.", "success")
    return redirect(url_for("enseignant.liste_reclamations", matiere_id=matiere_id))

# Supprimer tout les reclamations
@enseignant_bp.route('/reclamations/supprimer_toutes', methods=['POST'])
def supprimer_toutes_reclamations_enseignant():
    email = session.get("user_email")
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})
    if not enseignant:
        flash("Accès non autorisé.", "error")
        return redirect(url_for("auth.logout"))

    nom_enseignant = enseignant.get("nom")
    resultat = reclamation_collection.delete_many({
        "enseignant_nom": nom_enseignant
    })

    flash(f"Toutes les réclamations ({resultat.deleted_count}) ont été supprimées.", "success")
    return redirect(url_for("enseignant.dashboard"))
# supprimer une réclamation
@enseignant_bp.route('/reclamation/<reclamation_id>/supprimer', methods=['POST'])
def supprimer_reclamation(reclamation_id):
    email = session.get('user_email')
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})
    
    if not enseignant:
        flash("Accès non autorisé.", "error")
        return redirect(url_for("auth.connexion"))
    
    # Vérifier si la réclamation existe
    reclamation = reclamation_collection.find_one({"_id": ObjectId(reclamation_id)})
    if not reclamation:
        flash("Réclamation introuvable.", "error")
        return redirect(url_for("enseignant.dashboard"))
    
    # Vérifier si l'enseignant est autorisé à supprimer cette réclamation
    if reclamation.get("enseignant_nom") != enseignant.get("nom"):
        flash("Vous n'êtes pas autorisé à supprimer cette réclamation.", "error")
        return redirect(url_for("enseignant.dashboard"))
    
    # Supprimer la réclamation
    reclamation_collection.delete_one({"_id": ObjectId(reclamation_id)})
    
    flash("La réclamation a été supprimée avec succès.", "success")
    
    # Rediriger vers la page des réclamations de la matière si disponible
    matiere_id = reclamation.get("matiere_id")
    if matiere_id:
        return redirect(url_for("enseignant.liste_reclamations", matiere_id=matiere_id))
    else:
        return redirect(url_for("enseignant.dashboard"))

@enseignant_bp.route('/reclamations/<matiere_id>/supprimer_toutes', methods=['POST'])
def supprimer_reclamations_matiere(matiere_id):
    email = session.get("user_email")
    enseignant = infos_collection.find_one({"email": email, "role": "enseignant"})
    if not enseignant:
        flash("Accès non autorisé.", "error")
        return redirect(url_for("auth.connexion"))

    nom_enseignant = enseignant.get("nom")
    matiere = matieres_collection.find_one({
        "_id": ObjectId(matiere_id),
        "professeur": nom_enseignant
    })
    if not matiere:
        flash("Matière introuvable ou non autorisée.", "error")
        return redirect(url_for("enseignant.dashboard"))

    # Supprimer toutes les réclamations pour cette matière
    resultat = reclamation_collection.delete_many({
        "matiere_id": matiere_id,
        "enseignant_nom": nom_enseignant
    })

    flash(f"{resultat.deleted_count} réclamation(s) supprimée(s) pour la matière {matiere['nom']}.", "success")
    return redirect(url_for("enseignant.liste_reclamations", matiere_id=matiere_id))