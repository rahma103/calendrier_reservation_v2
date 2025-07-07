from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete_a_changer'  # Nécessaire pour les sessions

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
    mois_int = int(mois)
    jour_int = int(jour)
    return f"{jour_int} {mois_nom[mois_int]} 2025 - {niveau} - {maison}"

# -------------------- ROUTES LOGIN --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('accueil'))
        else:
            return render_template("login.html", error="Identifiants incorrects.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -------------------- ROUTES PRINCIPALES --------------------

@app.route("/")
def accueil():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("accueil.html")

@app.route("/rez")
def rez_de_chaussee():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("rez.html")

@app.route("/etage1")
def etage1():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("etage1.html")

@app.route("/etage2")
def etage2():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("etage2.html")

@app.route("/liste")
def liste_reservations():
    if 'user' not in session:
        return redirect(url_for('login'))
    reservations = load_reservations()
    formatted = {}
    for date, info in reservations.items():
        formatted[traduire_date_id(date)] = {
            "nom": info.get("nom", ""),
            "prenom": info.get("prenom", ""),
            "telephone": info.get("telephone", "")
        }
    return render_template("liste.html", reservations=formatted)

@app.route("/telecharger")
def telecharger_reservations():
    if 'user' not in session:
        return redirect(url_for('login'))
    if os.path.exists(FICHIER_RESERVATIONS):
        return send_file(FICHIER_RESERVATIONS, as_attachment=True)
    else:
        return "Aucun fichier de réservation disponible.", 404

@app.route("/reserver", methods=["POST"])
def reserver():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Données manquantes")

    reservations = load_reservations()

    start_str = data.get("startDate")
    end_str = data.get("endDate", start_str)
    maison = data.get("maison", "maison1")
    niveau = data.get("niveau", "rez")
    nom_prenom = data.get("nomPrenom", "").strip()
    telephone = data.get("telephone", "").strip()

    if not (start_str and nom_prenom and telephone):
        return jsonify(success=False, message="Champs obligatoires manquants")

    nom, prenom = "", ""
    parts = nom_prenom.split()
    if len(parts) == 1:
        nom = parts[0]
    elif len(parts) >= 2:
        nom = parts[-1]
        prenom = " ".join(parts[:-1])

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(success=False, message="Format date invalide")

    if end_date < start_date:
        return jsonify(success=False, message="Date de fin antérieure à la date de début")

    delta = (end_date - start_date).days
    dates_ids = []
    for i in range(delta + 1):
        current_date = start_date + timedelta(days=i)
        mois = current_date.month
        jour = current_date.day
        date_id = f"{maison}-{niveau}-{mois}-{jour}"
        dates_ids.append(date_id)

    for date_id in dates_ids:
        if date_id in reservations:
            return jsonify(success=False, message=f"Date déjà réservée : {traduire_date_id(date_id)}")

    for date_id in dates_ids:
        reservations[date_id] = {
            "prenom": prenom,
            "nom": nom,
            "telephone": telephone
        }
    save_reservations(reservations)
    return jsonify(success=True)

# -------------------- DÉMARRAGE --------------------



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
