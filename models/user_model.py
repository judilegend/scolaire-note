from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from config.db import infos_collection, matieres_collection, notes_collection
from werkzeug.security import check_password_hash

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.matiere_model import get_all_matieres

# Charger les variables d'environnement
load_dotenv()

def get_nom_etudiant():
    return list(infos_collection.find())

# Trouver un utilisateur par son nom et mot de passe
def trouver_utilisateur_par_email_et_mdp(email, mot_de_passe):
    utilisateur = infos_collection.find_one({'email': email})
    if utilisateur and check_password_hash(utilisateur['mot_de_passe'], mot_de_passe):
        return utilisateur
    return None
# Trouver un utilisateur par email
def trouver_utilisateur_par_email(email):
    return infos_collection.find_one({'email': email})

# Trouver un utilisateur par ID
def trouver_utilisateur_par_id(id):
    return infos_collection.find_one({'_id': ObjectId(id)})

# Créer un nouvel utilisateur
def creer_utilisateur(data):
    # Hash du mot de passe
    data['mot_de_passe'] = generate_password_hash(data['mot_de_passe'])
    infos_collection.insert_one(data)

# Mettre à jour le mot de passe
def mettre_a_jour_mot_de_passe(email, nouveau_mot_de_passe):
    hash_mdp = generate_password_hash(nouveau_mot_de_passe)
    infos_collection.update_one({'email': email}, {'$set': {'mot_de_passe': hash_mdp}})

#Creer Utilisateur
def create_user(numero, nom, parcours, niveau, email, mot_de_passe_hash, role):
    user = {
        "numero": numero,
        "nom": nom,
        "parcours": parcours,
        "niveau": niveau,
        "email": email,
        "mot_de_passe": mot_de_passe_hash,
        "role": role
    }
    infos_collection.insert_one(user)


def get_user_by_email(email):
    return infos_collection.find_one({"email": email})

def get_all_students():
    return list(infos_collection.find({'role': 'etudiant', 'approuve': True}))

def update_user(id, data):
    infos_collection.update_one({'_id': ObjectId(id)}, {'$set': data})

def delete_user_by_id(id):
    infos_collection.delete_one({'_id': ObjectId(id)})

def delete_user_by_id(id):
    infos_collection.delete_one({'_id': ObjectId(id)})

def get_students_by_parcours_niveau(parcours, niveau):
    return infos_collection.find({"parcours": parcours, "niveau": niveau})

def get_student_by_parcours_niveau(parcours, niveau):
    return infos_collection.find({
        "parcours": parcours,
        "niveau": niveau
    })

'''def get_students_by_parcours_niveau(parcours, niveau):
    return infos_collection.find({
        "parcours": parcours,
        "niveau": niveau,
        "role": "etudiant",  # Facultatif si tu veux filtrer uniquement les étudiants
        "statut": "accepte"  # Si tu veux afficher uniquement ceux validés par l'admin
    })'''


def get_all_students_sorted_by_moyenne(parcours, niveau):
    return list(infos_collection.find({
        "parcours": parcours,
        "niveau": niveau
        }).sort("moyenne", -1))

def update_student_results(etudiant_id, moyenne, rang):
    infos_collection.update_one(
        {"_id": ObjectId(etudiant_id)},
        {"$set": {
            "moyenne": round(moyenne, 2),
            "rang": rang
        }}
    )

def get_etudiant_by_id(etudiant_id):
    return infos_collection.find_one({"_id": ObjectId(etudiant_id)})

def get_notes_etudiant(numero_etudiant):
    return list(notes_collection.find({"numero_etudiant": numero_etudiant}))

def envoyer_email_resultat_session(etudiant, moyenne, rang):
    email_destinataire = etudiant["email"]
    nom = etudiant["nom"]
    parcours = etudiant["parcours"]
    niveau = etudiant["niveau"]

    # Construction du message
    if moyenne >= 10:
        sujet = "🎓 Résultat de la session - Félicitations"
        message = f"""
        Bonjour {nom},

        Nous avons le plaisir de vous informer que vous avez réussi votre session d'examen avec succès.

        ➤ Moyenne générale : {moyenne:.2f}/20  
        ➤ Rang dans la classe : {rang}

        Félicitations pour vos efforts et votre travail. Continuez sur cette voie pour atteindre l'excellence !

        Cordialement,  
        L'administration pédagogique.
        """
    else:
        sujet = "📘 Résultat de la session - Courage et persévérance"
        message = f"""
        Bonjour {nom},

        Voici les résultats de votre session d'examen.

        ➤ Moyenne générale : {moyenne:.2f}/20  
        ➤ Rang dans la classe : {rang}

        Ne vous découragez pas. Vous avez encore le temps et le potentiel pour progresser.  
        Apprenez de vos erreurs et continuez à travailler dur.

        Courage et bonne continuation.

        Cordialement,  
        L'administration pédagogique.
        """

    # Envoi d'email
    msg = MIMEMultipart()
    msg['From'] = "olivandry.777@gmail.com"
    msg['To'] = email_destinataire
    msg['Subject'] = sujet

    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("olivandry.777@gmail.com", "zzlr wcsw rdmg hzzu")  # Utilise un mot de passe d'application
            server.send_message(msg)
            print(f"Email envoyé à {email_destinataire}")
    except Exception as e:
        print(f"Erreur d’envoi à {email_destinataire} : {e}")

#Envoyer email
def envoyer_email(destinataire, sujet, message):
    email_expediteur = "olivandry.777@gmail.com"
    mot_de_passe = "zzlr wcsw rdmg hzzu"

    msg = MIMEText(message)
    msg['Subject'] = sujet
    msg['From'] = email_expediteur
    msg['To'] = destinataire

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as serveur:
        serveur.login(email_expediteur, mot_de_passe)
        serveur.send_message(msg)

