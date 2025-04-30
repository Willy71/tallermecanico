# cadastro_cliente.py

import streamlit as st
from firebase_config import db
from firebase_admin import firestore
from datetime import datetime

st.set_page_config(page_title="Cadastro de Cliente", page_icon="👤", layout="centered")

st.title("👤 Cadastro de Cliente")

# Verifica se está logado
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para cadastrar clientes.")
    st.stop()

# Formulário
with st.form("form_cliente"):
    nome = st.text_input("Nome completo")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Salvar cliente")

    if submitted:
        if not nome or not cpf:
            st.error("Nome e CPF são obrigatórios.")
        else:
            try:
                db.collection("clientes").add({
                    "nome": nome,
                    "cpf": cpf,
                    "telefone": telefone,
                    "email": email,
                    "oficina_id": st.session_state.usuario,
                    "criado_em": firestore.SERVER_TIMESTAMP
                })
                st.success("Cliente salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar cliente: {e}")
