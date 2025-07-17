# Home.py

import streamlit as st
from firebase_config import auth_admin, db
from firebase_admin import auth, firestore
#from google.firebase_admin import _auth_utils
import os
import requests
from datetime import timedelta
import uuid

st.set_page_config(page_title="Login - Oficinas", page_icon="🔧", layout="centered")

# ——— Verificar session cookie ———
params = st.experimental_get_query_params()
session_cookie = params.get("fb_session", [None])[0]

if session_cookie and "usuario" not in st.session_state:
    try:
        # decodifica y checa que no esté revocada
        decoded = auth_admin.verify_session_cookie(session_cookie, check_revoked=True)
        st.session_state.usuario = decoded["uid"]
    except Exception:
        # si falla, borramos la cookie para forzar relogin
        st.experimental_set_query_params()  # limpia todos los params
        st.error("Tu sesión expiró, por favor ingresa de nuevo.")
        st.stop()
# ————————————————————————————


# Estado de sesión
if "usuario" not in st.session_state:
    st.session_state.usuario = None

st.title("🔧 Gestão de Oficinas Mecânicas")
st.subheader("Acesse sua conta ou registre sua oficina")

opcao = st.radio("Escolha uma opção:", ["Login", "Registrar nova oficina"])

# ---------------- LOGIN -------------------
if opcao == "Login":
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        try:
            # 1) Hacer sign-in por REST API para obtener idToken
            import requests
            API_KEY = os.environ["FIREBASE_API_KEY"]
            resp = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",
                json={"email": email, "password": senha, "returnSecureToken": True}
            )
            resp.raise_for_status()
            data = resp.json()
            id_token      = data["idToken"]
            refresh_token = data["refreshToken"]
            
            # 2) Generar session cookie que dure hasta 14 días
            expires_in = timedelta(days=7)
            session_cookie = auth_admin.create_session_cookie(id_token, expires_in=expires_in)
            
            # 3) Guardar cookie en la URL (o Set-Cookie si montas un endpoint aparte)
            st.experimental_set_query_params(fb_session=session_cookie)
            
            st.success("Login realizado con éxito!")
            st.rerun()

        except auth.UserNotFoundError:
            st.error("Usuário não encontrado.")
        except Exception as e:
            st.error(f"Erro no login: {e}")

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
            st.rerun()
        except auth.EmailAlreadyExistsError:
            st.error("Esse email já está registrado.")
        except Exception as e:
            st.error(f"Erro ao registrar: {e}")

# ----------- SE ESTÁ LOGADO ---------------
if st.session_state.usuario:
    st.success(f"Oficina logada: {st.session_state.usuario}")
    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
