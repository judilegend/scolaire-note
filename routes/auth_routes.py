import random
import smtplib
from email.mime.text import MIMEText
from os import getenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from models.user_model import trouver_utilisateur_par_email, get_user_by_email, envoyer_email 
from config.db import infos_collection


auth_bp = Blueprint('auth', __name__)

# Inscription
@auth_bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        if get_user_by_email(email):
            return "<script>alert('Email déjà utilisé'); window.location.href='/inscription';</script>"

        # Crypter le mot de passe
        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        user_data = {
            'email': email,
            'mot_de_passe': mot_de_passe_hash,
            'role': role,
            'approuve': False
        }

        if role == 'etudiant':
            user_data.update({
                'numero': request.form['numero'],
                'nom': request.form['nom'],
                'parcours': request.form['parcours'],
                'niveau': request.form['niveau']
            })
        elif role == 'enseignant':
            user_data.update({
                'nom': request.form['nom_enseignant'],
                'matiere': request.form['matiere']
            })
        elif role == 'admin':
            user_data.update({
                'nom': request.form['nom_admin'],
                'identifiant': request.form['identifiant']
            })

        infos_collection.insert_one(user_data)

        # Envoyer un email à l'admin
        envoyer_email(
            destinataire='olivandry.777@gmail.com',
            sujet='📩 Nouvelle demande d’inscription',
            message=f"Un nouveau {role} a demandé une inscription avec l'email : {email}.\nVeuillez vérifier la liste d'attente."
        )

        return "<script>alert('Inscription réussie'); window.location.href='/connection';</script>"
    return render_template("authentification/inscription.html")

# Connexion
@auth_bp.route('/connection', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        user = trouver_utilisateur_par_email(email)

        if user and check_password_hash(user['mot_de_passe'], mot_de_passe):
            # Vérification si approuvé
            if not user.get('approuve', False):
                return "<script>alert('⛔ Votre compte est en attente d’approbation'); window.location.href='/connection';</script>"

            # Si approuvé, on connecte
            session['user_id'] = str(user['_id'])
            session['role'] = user.get('role', '')
            session['user_email'] = user.get('email', '')

            # Redirection en fonction du rôle
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'enseignant':
                return redirect(url_for('enseignant.dashboard'))
            elif user['role'] == 'etudiant':
                return redirect(url_for('student.dashboard'))
            else:
                return "Rôle inconnu"
        else:
            return "<script>alert('❌ Email ou mot de passe incorrect'); window.location.href='/connection';</script>"

    return render_template('authentification/connection.html')

# Mot de passe oublié et envoi le code de confirmation
@auth_bp.route('/mot_de_passe_oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form['email']
        user = infos_collection.find_one({'email': email})

        if user:
            code = str(random.randint(100000, 999999))
            session['reset_email'] = email
            session['reset_code'] = code

            # Contenue de mail à envoyer
            msg = MIMEText(f"Bonjour\n Voici votre code de réinitialisation : {code}")
            msg['Subject'] = "Code de réinitialisation mot de passe"
            msg['From'] = getenv("EMAIL_USER")
            msg['To'] = email

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(getenv("EMAIL_USER"), getenv("EMAIL_PASS"))
                    smtp.send_message(msg)
                return redirect(url_for('auth.verifier_code'))
            except Exception as e:
                return f"Erreur d'envoi d'email : {e}"
            
        return "<script>alert('❌ Email introuvable\n Veillez saisir votre vrais email'); window.location.href='/mot_de_passe_oublie';</script>"
    return render_template('authentification/mot_de_passe_oublie.html')

#Verifcation de code réçu
@auth_bp.route('/verifier_code', methods=['GET', 'POST'])
def verifier_code():
    if request.method == 'POST':
        code_saisi = request.form['code']
        if code_saisi == session.get('reset_code'):
            return redirect(url_for('auth.reinitialiser_mot_de_passe'))
        else:
            return "<script>alert('❌ Code incorrect'); window.location.href='/verifier_code';</script>"
    return render_template('authentification/reset.html')

# Rénitialisation du mot de passe
@auth_bp.route('/reinitialiser_mot_de_passe', methods=['GET', 'POST'])
def reinitialiser_mot_de_passe():
    if request.method == 'POST':
        nouveau_mdp = request.form['mot_de_passe']
        confirm_mdp = request.form['confirm_mot_de_passe']
        email = session.get('reset_email')

        if email:
            if nouveau_mdp == confirm_mdp:  # Vérification que les mots de passe correspondent
                hashed = generate_password_hash(nouveau_mdp)
                infos_collection.update_one({"email": email}, {"$set": {"mot_de_passe": hashed}})
                session.pop('reset_email', None)
                session.pop('reset_code', None)
                return "<script>alert('Mot de passe mis à jour'); window.location.href='/connection';</script>"
            else:
                flash("Les mots de passe ne correspondent pas.", "error")
                return redirect(url_for('auth.reinitialiser_mot_de_passe'))
    return render_template('authentification/nouveau_mot_de_passe.html')

# Deconnexion
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('accueil'))

