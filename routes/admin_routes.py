from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models.user_model import get_nom_etudiant, get_students_by_parcours_niveau
from models.user_model import get_all_students, create_user, delete_user_by_id
from bson.objectid import ObjectId
from config.db import infos_collection, notes_collection, matieres_collection
from models.notes_model import ajouter_note, get_toutes_notes, supprimer_note, calculer_moyenne_etudiant, get_notes_etudiant
from models.user_model import get_all_enseignants,get_all_students, envoyer_email_resultat_session, envoyer_email, generate_password_hash
from models.matiere_model import ajouter_matiere, get_all_matieres, supprimer_matiere, get_matiere_by_id, modifier_matiere
from flask import render_template

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboad admin
@admin_bp.route('/dashboard')
def dashboard():
    # Vérifier si l'utilisateur est connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Vérifier si l'utilisateur est un administrateur
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))

    return render_template("admin/admin_dashboard.html", user=user)

# Liste des etudiants
# Modifiez cette route
@admin_bp.route("/etudiants", methods=["GET", "POST"])
def liste_etudiants():  # Renommé de gerer_etudiants à liste_etudiants
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Récupération de tous les étudiants
    recherche = request.form.get("recherche", "").strip().lower()
    selected_niveau = request.form.get("niveau", "")
    selected_parcours = request.form.get("parcours", "")

    # Récupération de tous les étudiants approuvés
    tous = get_all_students()
    etudiants = []
    niveaux_set = set()
    parcours_set = set()

    for e in tous:
        numero = e["numero"]
        nom = e["nom"]
        niveau = e.get("niveau", "")
        parcours = e.get("parcours", "")
        email = e.get("email", "")

        # Ajout des niveaux et parcours dans les ensembles
        niveaux_set.add(niveau)
        parcours_set.add(parcours)

        # Filtrer les étudiants en fonction de la recherche et des filtres
        if recherche and recherche not in nom.lower() and recherche not in numero:
            continue
        if selected_niveau and niveau != selected_niveau:
            continue
        if selected_parcours and parcours != selected_parcours:
            continue

        etudiants.append({
            "numero": numero,
            "nom": nom,
            "niveau": niveau,
            "parcours": parcours,
            "email": email
        })

    return render_template("admin/liste_etudiants.html",
                           etudiants=etudiants,
                           recherche=recherche,
                           niveaux=sorted(niveaux_set),
                           parcours_list=sorted(parcours_set),
                           selected_niveau=selected_niveau,
                           selected_parcours=selected_parcours,
                           nb_etudiants=len(etudiants),
                           user=user)

# Gestion etudiants
@admin_bp.route("/etudiants", methods=["GET", "POST"])
def gerer_etudiants():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
     # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Récupération de tous les étudiants
    recherche = request.form.get("recherche", "").strip().lower() #.lower() pour rendre la recherche insensible à la casse, .strip() pour supprimer les espaces inutiles
    selected_niveau = request.form.get("niveau", "") # request.form.get("niveau", "") pour récupérer la valeur du champ "niveau" du formulaire, si la valeur n'est pas fournie, la valeur par défaut est une chaîne vide ""
    selected_parcours = request.form.get("parcours", "")

    # Récupération de tous les étudiants approuvés
    tous = get_all_students()
    etudiants = []
    niveaux_set = set() # pour éviter les doublons
    parcours_set = set()

    for e in tous:
        numero = e["numero"]
        nom = e["nom"]
        niveau = e.get("niveau", "") # get() pour récupérer la valeur de la clé "niveau" de l'étudiant, si la clé n'existe pas, la valeur par défaut est une chaîne vide ""
        parcours = e.get("parcours", "")
        email = e.get("email", "")

        # Ajout des niveaux et parcours dans les ensembles
        niveaux_set.add(niveau)
        parcours_set.add(parcours)

        # Filtrer les étudiants en fonction de la recherche et des filtres
        if recherche and recherche not in nom.lower() and recherche not in numero:
            continue # Si l'étudiant ne correspond pas à la recherche, passer à l'étudiant suivant
        if selected_niveau and niveau != selected_niveau:
            continue
        if selected_parcours and parcours != selected_parcours:
            continue

        etudiants.append({
            "numero": numero,
            "nom": nom,
            "niveau": niveau,
            "parcours": parcours,
            "email": email
        })

    return render_template("admin/liste_etudiants.html",
                           etudiants=etudiants,
                           recherche=recherche,
                           niveaux=sorted(niveaux_set),
                           parcours_list=sorted(parcours_set),
                           selected_niveau=selected_niveau,
                           selected_parcours=selected_parcours,
                           nb_etudiants=len(etudiants),user=user)

# Ajouter un étudiant
@admin_bp.route('/etudiants/ajouter', methods=['GET', 'POST'])
def ajouter_etudiant():
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

    if request.method == 'POST':
        numero = request.form['numero']
        nom = request.form['nom']
        parcours = request.form['parcours']
        niveau = request.form['niveau']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        # Vérifie si l'étudiant existe déjà
        if infos_collection.find_one({'email': email}):
            return "<script>alert('❌ Email déjà utilisé'); window.location.href='/admin/ajouter_etudiant';</script>"

        mot_de_passe_hash = generate_password_hash(mot_de_passe)
        create_user(numero, nom, parcours, niveau, email, mot_de_passe_hash)
        return redirect(url_for('admin.liste_etudiants'))

    return render_template('admin/ajouter_etudiant.html')

'''
# Supprimer un étudiant
@admin_bp.route('/etudiants/supprimer/<id>')
def supprimer_etudiant(id):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

    delete_user_by_id(id)
    return redirect(url_for('admin.liste_etudiants'))

# Modifier un étudiant
@admin_bp.route('/modifier_etudiant/<email>', methods=['GET', 'POST'])
def modifier_etudiant(email):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

    etudiant = infos_collection.find_one({'email': email, 'aprouve': True})
    if not etudiant:
        return "<script>alert('Étudiant introuvable'); window.location.href='/admin/etudiants';</script>"

    if request.method == 'POST':
        numero = request.form['numero']
        nom = request.form['nom']
        parcours = request.form['parcours']
        niveau = request.form['niveau']
        
        infos_collection.update_one(
            {'email': email},
            {'$set': {
                'numero': numero,
                'nom': nom,
                'parcours': parcours,
                'niveau': niveau
            }}
        )
        return redirect(url_for('admin.liste_etudiants'))
    return render_template("admin/modifier_etudiant.html", etudiant=etudiant) # etudiant=etudiant pour passer les informations de l'étudiant à la template
'''

#Gestion des matières

@admin_bp.route('/matieres', methods=['GET', 'POST'])
def gestion_matieres():

    # Vérifier si l'utilisateur est connecté et est un admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})
    # Récupérer tous les enseignants pour la liste déroulante

    professeurs = get_all_enseignants()
    
    # Récupérer toutes les matières existantes
    matieres = list(matieres_collection.find())
    
    # Définir les niveaux et parcours disponibles
    niveaux = ["L1", "L2", "L3", "M1", "M2"]
    parcours_list = ["GB", "ASR", "GID", "OCC", "MDI","IG"]
    
    # Traitement du formulaire d'ajout
    if request.method == 'POST':
        nouvelle_matiere = {
            "nom": request.form.get('nom'),
            "coefficient": int(request.form.get('coefficient')),
            "professeur": request.form.get('professeur'),
            "niveau": request.form.get('niveau'),
            "parcours": request.form.get('parcours')
        }
        
        # Insérer la nouvelle matière
        matieres_collection.insert_one(nouvelle_matiere)
        flash("Matière ajoutée avec succès!", "success")
        return redirect(url_for('admin.gestion_matieres'))
    
    return render_template('admin/matieres.html', 
                          matieres=matieres, 
                          professeurs=professeurs, 
                          niveaux=niveaux, 
                          parcours_list=parcours_list ,user=user)

@admin_bp.route('/matieres/modifier/<id_matiere>', methods=['GET', 'POST'])
def modifier_matiere_route(id_matiere):
       # Vérifier si l'utilisateur est connecté et est un admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})
    
    # Récupérer la matière à modifier
    matiere = matieres_collection.find_one({"_id": ObjectId(id_matiere)})
    if not matiere:
        flash("Matière introuvable", "error")
        return redirect(url_for('admin.gestion_matieres'))
    
    # Récupérer tous les enseignants pour la liste déroulante
    professeurs = get_all_enseignants()
    
    # Définir les niveaux et parcours disponibles
    niveaux = ["L1", "L2", "L3", "M1", "M2"]
    parcours_list = ["GB", "ASR", "GID", "OCC", "MDI","IG"]
    
    # Traitement du formulaire de modification
    if request.method == 'POST':
        matiere_modifiee = {
            "nom": request.form.get('nom'),
            "coefficient": int(request.form.get('coefficient')),
            "professeur": request.form.get('professeur'),
            "niveau": request.form.get('niveau'),
            "parcours": request.form.get('parcours')
        }
        
        # Mettre à jour la matière
        matieres_collection.update_one(
            {"_id": ObjectId(id_matiere)},
            {"$set": matiere_modifiee}
        )
        
        flash("Matière modifiée avec succès!", "success")
        return redirect(url_for('admin.gestion_matieres'))
    
    return render_template('admin/modifier_matiere.html', 
                          matiere=matiere, 
                          professeurs=professeurs, 
                          niveaux=niveaux, 
                          parcours_list=parcours_list,user=user)

# @admin_bp.route('/matieres/supprimer/<id_matiere>')
# def supprimer_matiere_route(id_matiere):
#     # Supprimer la matière
#     matieres_collection.delete_one({"_id": ObjectId(id_matiere)})
#     flash("Matière supprimée avec succès!", "success")
#     return redirect(url_for('admin.gestion_matieres'))

@admin_bp.route('/matieres', methods=['GET', 'POST'])
def matieres():
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

    niveaux = ["L1", "L2", "L3", "M1", "M2"]
    parcours_list = ["IG", "ASR", "GB", "GID", "OCC", "MDI"]

    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Récupérer tous les professeurs (utilisateurs avec role="enseignant") approuvé
    professeurs = infos_collection.find({"role": "enseignant", "aprouve": True})
    professeurs = list(professeurs)  # Convertir en liste pour l'utiliser dans le template

    if request.method == 'POST':
        nom = request.form['nom']
        coefficient = float(request.form['coefficient'])
        professeur = request.form['professeur']
        niveau = request.form['niveau']
        parcours = request.form['parcours']
        ajouter_matiere(nom, coefficient, professeur, niveau, parcours)
        return redirect(url_for('admin.matieres'))
    toutes_les_matieres = get_all_matieres()
    return render_template("admin/matieres.html", matieres=toutes_les_matieres, niveaux=niveaux, parcours_list=parcours_list, professeurs=professeurs,user=user)


#Suprimer un matieres
@admin_bp.route('/supprimer_matiere/<id_matiere>')
def supprimer_matiere_route(id_matiere):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

    supprimer_matiere(id_matiere)
    return redirect(url_for('admin.matieres'))

#Modifier un matiere
# @admin_bp.route('/modifier_matiere/<id_matiere>', methods=['GET', 'POST'])
# def modifier_matiere_route(id_matiere):
#     if 'user_email' not in session or session.get('role') != 'admin':
#         return redirect(url_for('admin.connexion'))
    
#       # Récupérer les informations de l'utilisateur connecté
#     user_id = session.get('user_id')
#     user = infos_collection.find_one({"_id": ObjectId(user_id)})
    
#     matiere = get_matiere_by_id(id_matiere)
#     niveaux = ["L1", "L2", "L3", "M1", "M2"]
#     parcours_list = ["IG", "SR", "GB", "GID", "OCC"]

#     # Récupérer les enseignants apprové
#     professeurs = infos_collection.find({"role": "enseignant", 'aprouve': True})
#     professeurs = list(professeurs)

#     if request.method == 'POST':
#         nom = request.form['nom']
#         coefficient = float(request.form['coefficient'])
#         professeur = request.form['professeur']
#         niveau = request.form['niveau']
#         parcours = request.form['parcours']

#         modifier_matiere(id_matiere, nom, coefficient, professeur, niveau, parcours)
#         return redirect(url_for('admin.matieres'))

#     return render_template(
#         "admin/modifier_matiere.html",
#         matiere=matiere,
#         niveaux=niveaux,
#         parcours_list=parcours_list,
#         professeurs=professeurs,user=user
#     )

#Gestion notes
@admin_bp.route('/notes', methods=['GET', 'POST'])
def gestion_notes():
    from models.matiere_model import get_all_matieres, get_matiere_by_id
    from models.user_model import get_students_by_parcours_niveau
    from models.notes_model import ajouter_note
    from config.db import notes_collection
    
    # Vérifier si l'utilisateur est connecté et est un admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})
    
    matieres = get_all_matieres()
    matiere_selectionnee = None
    etudiants = []
    notes = {}
    erreurs = []
    
    if request.method == 'POST':
        matiere_id = request.form.get('matiere_id')
        
        # Si on a des notes à enregistrer (formulaire avec les notes)
        if any(key.startswith('note_') for key in request.form.keys()):
            matiere = get_matiere_by_id(matiere_id)
            
            # Traitement des notes
            for key, value in request.form.items():
                if key.startswith('note_') and value.strip():
                    etudiant_id = key.replace('note_', '')
                    etudiant = infos_collection.find_one({"_id": ObjectId(etudiant_id)})
                    
                    try:
                        ajouter_note(etudiant['numero'], matiere_id, value)
                    except ValueError as e:
                        erreurs.append(f"Erreur pour {etudiant['nom']}: {str(e)}")
            
            if not erreurs:
                flash("Notes enregistrées avec succès", "success")
                return redirect(url_for('admin.voir_moyennes'))
        
        # Si on a juste sélectionné une matière
        if matiere_id:
            matiere_selectionnee = get_matiere_by_id(matiere_id)
            if matiere_selectionnee:
                etudiants = list(get_students_by_parcours_niveau(
                    matiere_selectionnee['parcours'], 
                    matiere_selectionnee['niveau']
                ))
                
                # Récupérer les notes existantes pour les afficher
                for etudiant in etudiants:
                    note = notes_collection.find_one({
                        "numero_etudiant": etudiant['numero'],
                        "id_matiere": ObjectId(matiere_id)
                    })
                    if note:
                        notes[str(etudiant['_id'])] = note['note']
    
    return render_template(
        'admin/gestion_notes.html',
        matieres=matieres,
        matiere_selectionnee=matiere_selectionnee,
        etudiants=etudiants,
        notes=notes,
        erreurs=erreurs,
        user=user
    )
#Supprimer note
@admin_bp.route('/notes/supprimer/<note_id>')
def supprimer_note_route(note_id):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    supprimer_note(note_id)
    return redirect(url_for('admin.notes'))

#Gestion moyenne
@admin_bp.route('/moyennes', methods=["GET", "POST"])
def voir_moyennes():
    from models.notes_model import calculer_moyennes_tous_etudiants
    
    recherche = ""
    selected_niveau = ""
    selected_parcours = ""
    
    # Calculer les moyennes de tous les étudiants avec la fonction standardisée
    tableau = calculer_moyennes_tous_etudiants()
    
    # Extraire les niveaux et parcours uniques
    niveaux = sorted(list(set(e["niveau"] for e in tableau if e["niveau"])))
    parcours_list = sorted(list(set(e["parcours"] for e in tableau if e["parcours"])))
    
    # Trier par moyenne décroissante
    tableau = sorted(tableau, key=lambda x: x["moyenne"], reverse=True)
    
    # Ajouter le rang
    for i, etud in enumerate(tableau):
        etud["rang"] = i + 1
    
    # Filtrer selon les critères
    if request.method == 'POST':
        recherche = request.form.get('recherche', '')
        selected_niveau = request.form.get('niveau', '')
        selected_parcours = request.form.get('parcours', '')
        
        if recherche:
            tableau = [e for e in tableau if recherche.lower() in e["nom"].lower() or recherche in e["numero"]]
        
        if selected_niveau:
            tableau = [e for e in tableau if e["niveau"] == selected_niveau]
        
        if selected_parcours:
            tableau = [e for e in tableau if e["parcours"] == selected_parcours]
    
    # Calculer les statistiques
    nb_etudiants = len(tableau)
    nb_admis = sum(1 for e in tableau if e["recommandation"] == "Admis")
    nb_non_admis = sum(1 for e in tableau if e["recommandation"] == "Redouble")
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})
    
    return render_template(
        'admin/moyennes.html',
        tableau=tableau,
        recherche=recherche,
        selected_niveau=selected_niveau,
        selected_parcours=selected_parcours,
        niveaux=niveaux,
        parcours_list=parcours_list,
        nb_etudiants=nb_etudiants,
        etudiants=tableau,
        nb_admis=nb_admis,
        nb_non_admis=nb_non_admis,
        user=user
    )
#Affichage note par etudiant
'''@admin_bp.route('/notes/detail/<numero_etudiant>', methods=['GET', 'POST'])
def detail_notes(numero_etudiant):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    etudiant = get_nom_etudiant()
    matieres = get_all_matieres()
    notes = get_notes_etudiant(numero_etudiant)
    details = []
    for matiere in matieres:
        note_matiere = next((n for n in notes if str(n['id_matiere']) == str(matiere['_id'])), None)
        details.append({
            "matiere": matiere['nom'],
            "coefficient": matiere['coefficient'],
            " note": note_matiere['note'] if note_matiere else '—',
            "id_matiere": matiere['_id']
        return render_template('admin/detail_notes.html', etudiant=etudiant, details=details)
'''

@admin_bp.route('/notes/<numero_etudiant>')
def detail_notes(numero_etudiant):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))

   # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    etudiant = get_nom_etudiant()
    matieres = get_all_matieres()
    notes = get_notes_etudiant(numero_etudiant)

    # Associer les notes avec les matières
    details = []
    for matiere in matieres:
        note_matiere = next((n for n in notes if str(n['id_matiere']) == str(matiere['_id'])), None)
        details.append({
            "matiere": matiere['nom'],
            "coefficient": matiere['coefficient'],
            "note": note_matiere['note'] if note_matiere else '—',
            "id_note": str(note_matiere['_id']) if note_matiere else None
        })

    return render_template("admin/detail_notes.html", etudiant=etudiant, details=details,user=user)

# Modifier note
@admin_bp.route("/modifier_note/<note_id>", methods=["GET", "POST"])
def modifier_note(note_id):
    # Vérifier si l'utilisateur est connecté et est un admin
    if session.get('role') != 'admin':
        return redirect(url_for('auth.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Récupérer la note à modifier
    note_doc = notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note_doc:
        flash("Note introuvable", "error")
        return redirect(url_for("admin.voir_moyennes"))
    
    # Récupérer les informations de l'étudiant et de la matière
    numero_etudiant = note_doc["numero_etudiant"]
    etudiant = infos_collection.find_one({"numero": numero_etudiant})
    matiere = matieres_collection.find_one({"_id": note_doc["id_matiere"]})
    
    # Préparer les données pour le template
    note = {
        "etudiant_nom": etudiant.get("nom", "Inconnu"),
        "etudiant_numero": numero_etudiant,
        "matiere_nom": matiere.get("nom", "Inconnue") if matiere else "Inconnue",
        "coefficient": matiere.get("coefficient", 1) if matiere else 1,
        "note": note_doc["note"]
    }

    if request.method == "POST":
        nouvelle_note = float(request.form["note"])
        notes_collection.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {"note": nouvelle_note}}
        )
        
        # Recalculer la moyenne de l'étudiant et mettre à jour dans la base de données
        from models.notes_model import calculer_moyenne_complete
        moyenne, _ = calculer_moyenne_complete(numero_etudiant)
        infos_collection.update_one(
            {"numero": numero_etudiant},
            {"$set": {"moyenne": moyenne}}
        )
        
        flash("Note mise à jour avec succès ✅", "success")
        return redirect(url_for("admin.detail_notes", numero_etudiant=numero_etudiant))

    # Retourner le template avec les données
    return render_template("admin/modifier_note.html", note=note, user=user)
#Publication de resultat
@admin_bp.route('/publier_resultats', methods=['GET', 'POST'])
def publier_resultats():
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})

    # Définir les niveaux et parcours disponibles
    niveaux = ["L1", "L2", "L3", "M1", "M2"]
    parcours_list = ["GB", "ASR", "GID", "OCC", "MDI", "IG"]

    parcours_selectionne = request.form.get('parcours')
    niveau_selectionne = request.form.get('niveau')
    confirmer = request.form.get('confirmer')

    etudiants = []

    if parcours_selectionne and niveau_selectionne:
        # Récupérer les étudiants du parcours et niveau sélectionnés
        resultats = infos_collection.find({
            "parcours": parcours_selectionne,
            "niveau": niveau_selectionne,
            "role": "etudiant",
            "approuve": True
        })

        for e in resultats:
            # Utiliser la moyenne déjà calculée et stockée dans la base de données
            etudiants.append({
                "numero": e.get("numero", ""),
                "nom": e.get("nom", ""),
                "email": e.get("email", ""),
                "parcours": e.get("parcours", ""),
                "niveau": e.get("niveau", ""),
                "moyenne": e.get("moyenne", 0)
            })

        if confirmer:
            # Trier les étudiants par moyenne décroissante
            etudiants.sort(key=lambda x: x["moyenne"], reverse=True)
            
            # Calcul du rang et envoi d'email
            for rang, etudiant in enumerate(etudiants, start=1):
                envoyer_email_resultat_session(etudiant, etudiant["moyenne"], rang)

            flash("Les résultats ont été publiés et envoyés par email avec succès !", "success")
            return redirect(url_for('admin.publier_resultats'))

    return render_template("admin/publier_resultats.html",
                           etudiants=etudiants,
                           parcours_selectionne=parcours_selectionne,
                           niveau_selectionne=niveau_selectionne,
                           parcours_list=parcours_list,
                           niveaux=niveaux,
                           user=user)
# Voir la liste d’attente
@admin_bp.route('/admin/attente')
def liste_attente():
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    # Récupérer les informations de l'utilisateur connecté
    user_id = session.get('user_id')
    user = infos_collection.find_one({"_id": ObjectId(user_id)})
    
    utilisateurs_en_attente = list(infos_collection.find({'approuve': False}))
    return render_template('admin/liste_attente.html', utilisateurs_en_attente=utilisateurs_en_attente, user=user)
# Voir un profil
@admin_bp.route('/admin/profil/<user_id>')
def consulter_profil(user_id):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    user = infos_collection.find_one({'_id': ObjectId(user_id)})
    return render_template('admin/profil_utilisateur.html', user=user)

# Accepter un utilisateur
@admin_bp.route('/accepter/<user_id>', methods=['POST'])
def accepter_utilisateur(user_id):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    user = infos_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        infos_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'approuve': True}})
        envoyer_email(
            destinataire=user['email'],
            sujet='✅ Votre inscription a été acceptée',
            message=f"Bonjour {user.get('nom', user.get('nom_admin', user.get('nom_enseignant', 'utilisateur')))},\n\n"
                    f"Votre compte en tant que {user['role']} a été approuvé. Vous pouvez maintenant vous connecter."
        )
    return redirect(url_for('admin.liste_attente'))

# Refuser un utilisateur
@admin_bp.route('/refuser/<user_id>', methods=['POST'])
def refuser_utilisateur(user_id):
    if 'user_email' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin.connexion'))
    
    user = infos_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        envoyer_email(
            destinataire=user['email'],
            sujet='❌ Votre inscription a été refusée',
            message=f"Bonjour {user.get('nom', user.get('nom_admin', user.get('nom_enseignant', 'utilisateur')))},\n\n"
                    f"Nous vous informons que votre demande d’inscription en tant que {user['role']} a été refusée.\n"
                    f"Merci de votre compréhension."
        )
        infos_collection.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('admin.liste_attente'))
