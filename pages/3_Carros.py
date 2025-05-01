# 3_Carros.py

import streamlit as st
from firebase_config import db
from firebase_admin import firestore

st.set_page_config(page_title="Cadastro de Carro", page_icon="🚗", layout="centered")

st.title("🚗 Cadastro de Carro")

# Verifica login
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para cadastrar carros.")
    st.stop()

# Busca clientes da oficina
clientes_ref = db.collection("clientes").where("oficina_id", "==", st.session_state.usuario)
clientes_docs = clientes_ref.stream()

clientes = []
cliente_options = []

for doc in clientes_docs:
    data = doc.to_dict()
    clientes.append((doc.id, data.get("nome"), data.get("cpf")))
    cliente_options.append(f"{data.get('nome')} ({data.get('cpf')})")

if not clientes:
    st.info("Você precisa cadastrar um cliente antes de cadastrar um carro.")
    st.stop()

# Formulário
with st.form("form_carro"):
    cliente_index = st.selectbox("Selecione o cliente", range(len(cliente_options)), format_func=lambda i: cliente_options[i])
    placa = st.text_input("Placa")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    cor = st.text_input("Cor")
    ano = st.text_input("Ano")
    km = st.text_input("Km")
    enviado = st.form_submit_button("Salvar carro")

    if enviado:
        if not placa:
            st.error("A placa é obrigatória.")
        else:
            try:
                cliente_id = clientes[cliente_index][0]

                db.collection("carros").add({
                    "cliente_id": cliente_id,
                    "oficina_id": st.session_state.usuario,
                    "placa": placa.upper(),
                    "marca": marca,
                    "modelo": modelo,
                    "cor": cor,
                    "ano": ano,
                    "km": km,
                    "criado_em": firestore.SERVER_TIMESTAMP
                })
                st.success("Carro salvo com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar carro: {e}")
