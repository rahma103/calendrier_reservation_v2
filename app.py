from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = '568df7afbab7ea26d1cf8e4ffdd5164ff6e18f57db6f83d68ba3d367b6a14d8c'  # à personnaliser !

FICHIER_RESERVATIONS = "static/reservations.json"

# --- Données utilisateurs
USERS = {
    "rafraf": "projet2023",
    "rahma": "motdepasse"
}

# -------------------- UTILITAIRES --------------------

def load_reservations():
    if not os.path.exists(FICHIER_RESERVATIONS):
        return {}
    with open(FICHIER_RESERVATIONS, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reservations(data):
    with open(FICHIER_RESERVATIONS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def traduire_date_id(date_id):
    parts = date_id.split("-")
    if len(parts) < 4:
        return date_id
    maison, niveau, mois, jour = parts
    mois_nom = ["", "janvier", "février", "mars", "avril", "mai", "juin",
                "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{int(jour)} {mois_nom[int(mois)]} 2025 - {niveau} - {maison}"

# -------------------- ROUTES AUTH --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('accueil'))
        return render_template("login.html", error="Identifiants incorrects.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -------------------- ROUTES PAGES --------------------

@app.route('/')
def accueil():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('accueil.html')

@app.route('/rez')
def rez_de_chaussee():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('rez.html')

@app.route('/etage1')
def etage1():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('etage1.html')

@app.route('/etage2')
def etage2():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('etage2.html')

@app.route('/liste')
def liste_reservations():
    if 'user' not in session:
        return redirect(url_for('login'))
    reservations = load_reservations()
    formatted = {
        traduire_date_id(date): info for date, info in reservations.items()
    }
    return render_template('liste.html', reservations=formatted)

@app.route('/telecharger')
def telecharger_reservations():
    if 'user' not in session:
        return redirect(url_for('login'))
    if os.path.exists(FICHIER_RESERVATIONS):
        return send_file(FICHIER_RESERVATIONS, as_attachment=True)
    return "Fichier non trouvé", 404

# -------------------- ROUTE POST RESERVATION --------------------

@app.route('/reserver', methods=['POST'])
def reserver():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Données manquantes")

    start_str = data.get("startDate")
    end_str = data.get("endDate", start_str)
    maison = data.get("maison", "maison1")
    niveau = data.get("niveau", "rez")
    nom_prenom = data.get("nomPrenom", "").strip()
    telephone = data.get("telephone", "").strip()

    if not (start_str and nom_prenom and telephone):
        return jsonify(success=False, message="Champs requis manquants")

    nom, prenom = "", ""
    parts = nom_prenom.split()
    if len(parts) >= 2:
        prenom = " ".join(parts[:-1])
        nom = parts[-1]
    else:
        nom = nom_prenom

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(success=False, message="Format de date invalide")

    if end_date < start_date:
        return jsonify(success=False, message="Date de fin antérieure à la date de début")

    reservations = load_reservations()
    delta = (end_date - start_date).days
    dates_ids = []

    for i in range(delta + 1):
        current_date = start_date + timedelta(days=i)
        date_id = f"{maison}-{niveau}-{current_date.month}-{current_date.day}"
        if date_id in reservations:
            return jsonify(success=False, message=f"Date déjà réservée : {traduire_date_id(date_id)}")
        dates_ids.append(date_id)

    for date_id in dates_ids:
        reservations[date_id] = {
            "prenom": prenom,
            "nom": nom,
            "telephone": telephone
        }

    save_reservations(reservations)
    return jsonify(success=True)

# -------------------- DEMARRAGE LOCAL --------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
