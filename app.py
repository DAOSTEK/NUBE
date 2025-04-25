from flask import Flask, render_template, request, redirect, url_for, flash
import os
import dropbox
from datetime import datetime
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
from dotenv import load_dotenv
from dropbox import Dropbox 
from dotenv import load_dotenv
from dotenv import load_dotenv
import os
import pickle
from pathlib import Path



app = Flask(__name__)
app.secret_key = 'mi_secreto'  # Necesario para usar flash()

load_dotenv()  # Carga las variables del .env
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')


# Configuración Dropbox y Google Drive
GOOGLE_CLIENT_SECRETS_FILE = 'client_secrets.json'
PASSWORD = "HERD077"  # Contraseña para ver historial


# Esto debería estar al inicio de tu archivo, junto a otras configuraciones
SCOPES = ['https://www.googleapis.com/auth/drive.file']


dbx: Dropbox = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def authenticate_google_drive():
    creds = None
    token_path = os.path.join(os.path.expanduser('~'), '.config', 'google_token.pickle')
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server()


    return build('drive', 'v3', credentials=creds)

# Subir archivo a Google Drive
def upload_to_drive(file):
    service = authenticate_google_drive()
    media = MediaFileUpload(file, mimetype='application/octet-stream', resumable=True)
    file_metadata = {'name': os.path.basename(file)}
    file = service.files().create(media_body=media, body=file_metadata).execute()
    return file['id']

# Subir archivo a Dropbox
def upload_to_dropbox(file):
    with open(file, "rb") as f:
        response = dbx.files_upload(f.read(), '/' + os.path.basename(file), mute=True)
    return response.id

# Guardar historial de archivos
def save_file_history(file_name, file_id, cloud_service):
    with open("uploads_history.txt", "a") as history_file:
        history_file.write(f"{file_name},{file_id},{cloud_service},{datetime.now()}\n")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        archivo = request.files['archivo']
        destino = request.form['destino']
        filepath = os.path.join('uploads', archivo.filename)
# Desarrollado por DIEGO ARTURO HERNANDEZ REYES - DAOSTEK
        # Crear carpeta si no existe
        os.makedirs('uploads', exist_ok=True)
        
        archivo.save(filepath)
        flash("Cargando archivo, por favor espere...", 'info')

        try:
            if destino == 'drive':
                file_id = upload_to_drive(filepath)
                save_file_history(archivo.filename, file_id, 'Google Drive')
                flash(f"✅ Archivo subido a Google Drive. ID: {file_id}", 'success')
            elif destino == 'dropbox':
                file_id = upload_to_dropbox(filepath)
                save_file_history(archivo.filename, file_id, 'Dropbox')
                flash(f"✅ Archivo subido a Dropbox. ID: {file_id}", 'success')
        except Exception as e:
            flash(f"❌ Error: {str(e)}", 'danger')

        return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/historial', methods=['GET', 'POST'])
def historial():
    if request.method == 'POST':
        contrasena = request.form['contrasena']
        if contrasena == PASSWORD:
            try:
                with open("uploads_history.txt", "r") as history_file:
                    archivos = [line.strip().split(",") for line in history_file.readlines()]
            except FileNotFoundError:
                archivos = []
            return render_template('historial.html', archivos=archivos, contrasena_correcta=True)
        else:
            flash("❌ Acceso Denagado al Historial.", 'danger')
            return render_template('historial.html', contrasena_correcta=False)
    
    return render_template('historial.html', contrasena_correcta=None)

from flask import send_file














if __name__ == '__main__':
    app.run(debug=True)
