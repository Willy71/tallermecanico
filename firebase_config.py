# firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore, auth

# Solo inicializar si aún no fue hecho
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
auth_admin = auth  # acceso al módulo de autenticación
