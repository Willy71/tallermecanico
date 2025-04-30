# Home.py

import streamlit as st
from firebase_config import auth_admin, db
from firebase_admin import auth, firestore
#from google.firebase_admin import _auth_utils
import uuid

st.set_page_config(page_title="Login - Oficinas", page_icon="🔧", layout="centered")

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
            user = auth_admin.get_user_by_email(email)
            st.session_state.usuario = user.uid
            st.success("Login realizado com sucesso!")
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
