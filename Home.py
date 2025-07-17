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
        st.experimental_set_query_params()  # limpia todos los params
        st.error("Tu sesión expiró, por favor ingresa de nuevo.")
        st.stop()
# ————————————————————————————

# Estado inicial de sesión
st.session_state.setdefault("usuario", None)

st.title("🔧 Gestão de Oficinas Mecânicas")
st.subheader("Acesse sua conta ou registre sua oficina")

opcao = st.radio("Escolha uma opção:", ["Login", "Registrar nova oficina"])

# ---------------- LOGIN -------------------
if opcao == "Login":
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        # 1) Sign-in por REST API para obtener idToken
        API_KEY = os.environ.get("FIREBASE_API_KEY")
        if not API_KEY:
            st.error("Error: no se encontró la variable FIREBASE_API_KEY en el entorno.")
        else:
            resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
                json={"email": email, "password": senha, "returnSecureToken": True}
            )
            if resp.status_code != 200:
                error_info = resp.json().get("error", {}).get("message", "Unknown error")
                st.error(f"Login fallido: {error_info}")
            else:
                data = resp.json()
                id_token = data.get("idToken")
                if not id_token:
                    st.error("No se recibió idToken de Firebase.")
                else:
                    # 2) Generar session cookie que dure al menos un día
                    expires_in = timedelta(days=1)
                    session_cookie = auth_admin.create_session_cookie(id_token, expires_in=expires_in)
                    # 3) Guardar cookie en la URL
                    st.experimental_set_query_params(fb_session=session_cookie)
                    st.success("Login realizado con éxito!")
                    st.experimental_rerun()

# ------------- REGISTRO -------------------
elif opcao == "Registrar nova oficina":
    email = st.text_input("Email da Oficina")
    senha = st.text_input("Senha", type="password")
    nome_oficina = st.text_input("Nome da Oficina")
    telefone = st.text_input("Telefone")

    if st.button("Registrar"):
        try:
            user = auth_admin.create_user(email=email, password=senha)
            oficina_id = user.uid

            db.collection("usuarios").document(oficina_id).set({
                "email": email,
                "nome_oficina": nome_oficina,
                "telefone": telefone,
                "oficina_id": oficina_id,
                "criado_em": firestore.SERVER_TIMESTAMP
            })

            st.success("Oficina registrada com sucesso!")
            st.session_state.usuario = oficina_id
            st.experimental_rerun()
        except auth.EmailAlreadyExistsError:
            st.error("Esse email já está registrado.")
        except Exception as e:
            st.error(f"Erro ao registrar: {e}")

# ----------- SE ESTÁ LOGADO ---------------
if st.session_state.usuario:
    st.success(f"Oficina logada: {st.session_state.usuario}")
    if st.button("Sair"):
        st.session_state.usuario = None
        st.experimental_rerun()
