from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
import json
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = FastAPI()

# Configuración del servidor SMTP (ejemplo con Gmail)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "evaristoj108@gmail.com"
SMTP_PASSWORD = "qwev hawj elja gcub"

# Configuración de Google OAuth2
GOOGLE_CLIENT_SECRETS_FILE = "client_secret_696587366927-h9c1slem5ggocbv8v23vgrup6uaug5sj.apps.googleusercontent.com.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
REDIRECT_URI = 'http://localhost:8000/callback'
CREDENTIALS_FILE = 'stored_credentials.json'

class NotificationRequest(BaseModel):
    email: EmailStr
    subject: str
    message: str

def load_google_credentials():
    """Carga las credenciales de Google desde el archivo JSON"""
    if os.path.exists(GOOGLE_CLIENT_SECRETS_FILE):
        with open(GOOGLE_CLIENT_SECRETS_FILE, 'r') as f:
            return json.load(f)
    return None

def save_user_credentials(credentials):
    """Guarda las credenciales del usuario"""
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds_data, f)

def load_user_credentials():
    """Carga las credenciales guardadas del usuario"""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
            credentials = Credentials(**creds_data)
            
            # Refrescar token si es necesario
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                save_user_credentials(credentials)
            
            return credentials
    return None

def send_email(to_email: str, subject: str, message: str):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())

def send_email_with_gmail_api(to_email: str, subject: str, message: str, credentials):
    """Envía email usando la API de Gmail"""
    try:
        service = build('gmail', 'v1', credentials=credentials)
        
        # Crear el mensaje correctamente
        email_msg = f"To: {to_email}\nSubject: {subject}\n\n{message}"
        raw_message = base64.urlsafe_b64encode(email_msg.encode('utf-8')).decode('utf-8')
        
        sent_message = service.users().messages().send(
            userId='me', 
            body={'raw': raw_message}
        ).execute()
        
        return sent_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")

@app.get("/")
def root():
    return {"message": "API de Notificaciones funcionando correctamente"}

@app.get("/auth")
def google_auth():
    """Inicia el flujo de autenticación de Google"""
    credentials_info = load_google_credentials()
    if not credentials_info:
        raise HTTPException(status_code=500, detail="Archivo de credenciales no encontrado")
    
    flow = Flow.from_client_config(
        credentials_info,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    return {"auth_url": authorization_url, "state": state}

@app.get("/callback")
def google_callback(code: str, state: str):
    """Maneja el callback de Google OAuth2"""
    credentials_info = load_google_credentials()
    
    flow = Flow.from_client_config(
        credentials_info,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = REDIRECT_URI
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Guardar las credenciales
    save_user_credentials(credentials)
    
    return {"detail": "Autenticación exitosa - Credenciales guardadas"}

@app.post("/test-email")
def test_email():
    """Endpoint de prueba que envía un email a princs2112@gmail.com"""
    test_request = NotificationRequest(
        email="princs2112@gmail.com",
        subject="Prueba de tu proyecto",
        message="¡Hola! Soy tu proyecto y estoy funcionando correctamente. 🚀\n\nEste mensaje confirma que el sistema de notificaciones está operativo."
    )
    
    try:
        send_email(test_request.email, test_request.subject, test_request.message)
        return {"detail": "Email de prueba enviado correctamente a princs2112@gmail.com"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando email de prueba: {str(e)}")

@app.post("/test-email-gmail")
def test_email_gmail():
    """Endpoint de prueba que envía email usando Gmail API"""
    credentials = load_user_credentials()
    if not credentials:
        raise HTTPException(
            status_code=401, 
            detail="No hay credenciales guardadas. Primero autentica en /auth"
        )
    
    try:
        send_email_with_gmail_api(
            "princs2112@gmail.com",
            "Prueba Gmail API - Tu proyecto funciona!",
            "¡Hola! Soy tu proyecto y estoy funcionando correctamente usando Gmail API. 🚀\n\nEste mensaje confirma que la autenticación OAuth2 y el envío via Gmail API están funcionando.",
            credentials
        )
        return {"detail": "Email de prueba enviado correctamente via Gmail API a princs2112@gmail.com"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando email via Gmail API: {str(e)}")

@app.post("/send-notification/")
def send_notification(request: NotificationRequest):
    try:
        send_email(request.email, request.subject, request.message)
        return {"detail": "Notificación enviada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-notification-gmail/")
def send_notification_gmail(request: NotificationRequest):
    """Envía notificación usando Gmail API"""
    credentials = load_user_credentials()
    if not credentials:
        raise HTTPException(
            status_code=401, 
            detail="No hay credenciales guardadas. Primero autentica en /auth"
        )
    
    try:
        send_email_with_gmail_api(request.email, request.subject, request.message, credentials)
        return {"detail": "Notificación enviada correctamente via Gmail API"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)