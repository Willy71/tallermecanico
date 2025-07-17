import streamlit as st
from firebase_config import auth_admin, db
from firebase_admin import auth, firestore
import os
import requests
from datetime import timedelta

st.set_page_config(page_title="Login - Oficinas", page_icon="🔧", layout="centered")

# ——— Verificar session cookie ———
params = st.experimental_get_query_params()
session_cookie = params.get("fb_session", [None])[0]
if session_cookie and not st.session_state.get("usuario"):
    try:
        decoded = auth_admin.verify_session_cookie(session_cookie, check_revoked=True)
        st.session_state.usuario = decoded["uid"]
    except Exception:
        st.experimental_set_query_params()
        st.error("Tu sesión expiró, por favor ingresa de nuevo.")
        st.stop()
# ————————————————————————————

# Inicializar estado
if "usuario" not in st.session_state:
    st.session_state.usuario = None

st.title("🔧 Gestión de Oficinas Mecánicas")
st.subheader("Accede o registra tu oficina")

action = st.radio("Selecciona una acción:", ["Login", "Registrar nueva oficina"])

# Función para login y creación de cookie

def do_login(email, senha):
    API_KEY = os.environ.get("FIREBASE_API_KEY")
    if not API_KEY:
        st.error("Error: falta FIREBASE_API_KEY en el entorno.")
        return False
    # Llamada REST a Firebase Auth
    resp = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
        json={"email": email, "password": senha, "returnSecureToken": True}
    )
    if resp.status_code != 200:
        msg = resp.json().get("error", {}).get("message", "Unknown error")
        st.error(f"Login fallido: {msg}")
        return False
    data = resp.json()
    id_token = data.get("idToken")
    if not id_token:
        st.error("No se recibió idToken de Firebase.")
        return False
    # Crear session cookie de 1 día
    cookie = auth_admin.create_session_cookie(id_token, expires_in=timedelta(days=1))
    st.experimental_set_query_params(fb_session=cookie)
    return True

# ---------------- LOGIN -------------------
if action == "Login":
    email = st.text_input("Email")
    senha = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if do_login(email, senha):
            st.success("Login exitoso.")
            st.experimental_rerun()

# ------------- REGISTRO -------------------
elif action == "Registrar nueva oficina":
    email = st.text_input("Email de la Oficina")
    senha = st.text_input("Contraseña", type="password")
    nombre = st.text_input("Nombre de la Oficina")
    telefono = st.text_input("Teléfono")
    if st.button("Registrar"):
        try:
            user = auth_admin.create_user(email=email, password=senha)
            uid = user.uid
            # Guardar datos en Firestore
            db.collection("usuarios").document(uid).set({
                "email": email,
                "nombre": nombre,
                "telefono": telefono,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            # Auto-login tras registro
            if do_login(email, senha):
                st.success("Registro y login exitosos.")
                st.experimental_rerun()
        except auth.EmailAlreadyExistsError:
            st.error("Este email ya está registrado.")
        except Exception as e:
            st.error(f"Error al registrar: {e}")

# ----------- CONTENIDO PARA USUARIOS LOGUEADOS ---------------
if st.session_state.usuario:
    st.success(f"Oficina logueada: {st.session_state.usuario}")
    if st.button("Cerrar sesión"):
        # Limpiar estado y cookie
        st.session_state.usuario = None
        st.experimental_set_query_params()
        st.experimental_rerun()
