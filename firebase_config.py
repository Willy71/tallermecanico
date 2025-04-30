# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json

if not firebase_admin._apps:
    # Cargar desde variable de entorno
    cred_dict = json.loads(os.environ["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
auth_admin = auth
