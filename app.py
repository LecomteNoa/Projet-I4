from flask import Flask, session, request, jsonify, render_template, redirect, url_for, request, flash
from flask_socketio import SocketIO, emit
import logging
from functools import wraps
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.users import Users
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.exception import AppwriteException
from appwrite.query import Query
from functools import wraps
import os
from dotenv import load_dotenv
from appwrite.services.databases import Databases
import json
import threading
import lora
import time
import base64
import binascii
import random

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Configuration de Appwrite
client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))



databases = Databases(client)
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
DATABASE_ID = os.getenv("DATABASE_ID")

code_secret = os.getenv("CODE_SECRET")
code_secret = int(code_secret)

logging.basicConfig(level=logging.INFO)

def promote_to_admin(user_id, user_email, user_password, isAdmin):
    try:
        databases.create_document(
            database_id=os.getenv("DATABASE_ID"),
            collection_id=os.getenv("USERS_COLLECTION_ID"),
            document_id=ID.unique(),
            data={
                'userID': user_id,
                'email': user_email,
                'password': user_password,
                'isAdmin': isAdmin
            }
        )
        print(f"Utilisateur {user_email} promu admin")
    except AppwriteException as e:
        print(f"Erreur: {e.message}")
        
def add_user(user_email, user_password, badgeUID):
    try:
        databases.create_document(
            database_id=os.getenv("DATABASE_ID"),
            collection_id=os.getenv("USERS_COLLECTION_USER_ID"),
            document_id=ID.unique(),
            data={
                'email': user_email,
                'password': user_password,
                'Badge_UID': badgeUID
            }
        )
        print(f"Utilisateur {user_email} ajouté")
    except AppwriteException as e:
        print(f"Erreur: {e.message}")
    
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/data', methods=['GET'])
def data():
    return jsonify(mqtt_messages)
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            admins = databases.list_documents(
                DATABASE_ID,
                USERS_COLLECTION_ID,
                queries=[Query.equal('email', email)]
            )

            if admins['total'] == 0:
                flash('Identifiants invalides', 'error')
                return redirect(url_for('login'))

            admin = admins['documents'][0]

            if admin['password'] != password:
                flash('Identifiants invalides', 'error')
                return redirect(url_for('login'))
            
            if admin['isAdmin'] == False:
                flash('Identifiants invalides', 'error')
                return redirect(url_for('login'))
            
            
            session['admin_logged_in'] = True
            session['admin_email'] = email
            
            return redirect(url_for('menu'))

        except AppwriteException as e:
            flash(f"Erreur système: {e.message}", 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    if request.method == 'POST':
        if 'add' in request.form:
            return redirect(url_for('add'))
        elif 'act' in request.form:
            return redirect(url_for('activity'))
        elif 'dash' in request.form:
            return redirect(url_for('dashboard'))
    return render_template('menu.html', admin_email=session.get('admin_email'))
    

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add(): 
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        BadgeUID = request.form['BadgeUID']

        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('add.html')
        else:
            add_user(email, password, BadgeUID)
            flash("Ajout réussi", 'success')
            return redirect(url_for('menu'))
        
    return render_template('add.html')
        
        
@app.route('/activity')
@login_required
def activity():
    return render_template('activity.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    return redirect(url_for('login'))

@app.route('/ttn-webhook', methods=['GET', 'POST'])
def ttn_webhook():
    try:
        # Lire les données reçues
        data = request.get_json()
        if data is None:
            return jsonify({"error": "No JSON received"}), 400

        # Extraire uniquement frm_payload
        frm_payload = data.get("uplink_message", {}).get("frm_payload")

        if frm_payload is None:
            return jsonify({"error": "frm_payload not found"}), 400
        
        decoded_bytes = base64.b64decode(frm_payload)  
        hex_payload = decoded_bytes.hex()
        
        filtered_hex = hex_payload[2:10]

        print("UID Badge recu :", filtered_hex)
        
        code()

        # Retourner uniquement frm_payload
        return jsonify({"frm_payload": frm_payload}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500
    
def code():
    random_number = random.randint(10000000, 99999999)
    operate = random_number % code_secret
    operate = str(operate)
    liste = list(operate)
    random.shuffle(liste)
    code = liste[:6]
    chaine = ''.join(map(str, code))
    code = int(chaine)
    print("Code généré :", code)
    return code

def sendCode():
    codeToSend = code()
    print(f"Envoi du code {codeToSend}")
    socketio.emit("code", {"number": codeToSend})

sendCode()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


    
        

         
