# 1_Ordem de serviço.py

import streamlit as st
from firebase_config import db
from firebase_admin import firestore

st.set_page_config(page_title="Nova Ordem de Serviço", page_icon="🛠️", layout="centered")

st.title("🛠️ Nova Ordem de Serviço")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para registrar ordens.")
    st.stop()

oficina_id = st.session_state.usuario

# ---------- CLIENTE ----------
st.subheader("👤 Cliente")
tipo_cliente = st.radio("Tipo de cliente:", ["Existente", "Novo"], horizontal=True)
cliente_data = {}
cliente_id = None

if tipo_cliente == "Novo":
    nome = st.text_input("Nome e sobrenome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_input("Endereço")

    # Verifica duplicados
    cpf_existente = db.collection("clientes").where("cpf", "==", cpf).where("oficina_id", "==", oficina_id).get()
    tel_existente = db.collection("clientes").where("telefone", "==", telefone).where("oficina_id", "==", oficina_id).get()

    if cpf_existente:
        st.warning("⚠️ Já existe um cliente com esse CPF cadastrado.")
    if tel_existente:
        st.warning("⚠️ Já existe um cliente com esse telefone cadastrado.")

    if nome and cpf and telefone:
        doc = db.collection("clientes").add({
            "nome": nome,
            "cpf": cpf,
            "telefone": telefone,
            "endereco": endereco,
            "oficina_id": oficina_id,
            "criado_em": firestore.SERVER_TIMESTAMP
        })
        cliente_id = doc[1].id
        cliente_data = {"nome": nome, "cpf": cpf, "telefone": telefone, "endereco": endereco}
        st.success("Cliente salvo com sucesso!")

else:
    campo = st.selectbox("Buscar cliente por:", ["Nome", "CPF", "Telefone"])
    valor = st.text_input("Valor de busca").strip()
    cliente_ref = db.collection("clientes").where("oficina_id", "==", oficina_id)
    if campo == "Nome":
        cliente_ref = cliente_ref.where("nome", "==", valor)
    elif campo == "CPF":
        cliente_ref = cliente_ref.where("cpf", "==", valor)
    else:
        cliente_ref = cliente_ref.where("telefone", "==", valor)

    resultados = cliente_ref.stream()
    for doc in resultados:
        cliente_data = doc.to_dict()
        cliente_id = doc.id
        break

    if cliente_data:
        st.info(f"Cliente encontrado: {cliente_data.get('nome')} | CPF: {cliente_data.get('cpf')}")
    else:
        st.warning("Cliente não encontrado.")
        st.stop()

# ---------- CARRO ----------
st.subheader("🚗 Carro")
tipo_carro = st.radio("Tipo de carro:", ["Existente", "Novo"], horizontal=True)
carro_data = {}
carro_id = None

if tipo_carro == "Novo":
    placa = st.text_input("Placa").upper()
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    ano = st.text_input("Ano")
    cor = st.text_input("Cor")
    km = st.text_input("Km")

    # Verifica placa existente
    placa_existente = db.collection("carros").where("placa", "==", placa).where("oficina_id", "==", oficina_id).get()
    if placa_existente:
        st.warning("⚠️ Já existe um carro com essa placa cadastrado.")

    if placa and marca and modelo:
        doc = db.collection("carros").add({
            "placa": placa,
            "marca": marca,
            "modelo": modelo,
            "ano": ano,
            "cor": cor,
            "km": km,
            "cliente_id": cliente_id,
            "oficina_id": oficina_id,
            "criado_em": firestore.SERVER_TIMESTAMP
        })
        carro_id = doc[1].id
        carro_data = {"placa": placa, "marca": marca, "modelo": modelo, "ano": ano, "cor": cor, "km": km}
        st.success("Carro salvo com sucesso!")

else:
    placa_busca = st.text_input("Digite a placa do carro existente").upper()
    carro_ref = db.collection("carros").where("placa", "==", placa_busca).where("oficina_id", "==", oficina_id).stream()
    for doc in carro_ref:
        carro_data = doc.to_dict()
        carro_id = doc.id
        break

    if carro_data:
        st.info(f"Carro encontrado: {carro_data.get('marca')} {carro_data.get('modelo')} | Placa: {carro_data.get('placa')}")
    else:
        st.warning("Carro não encontrado.")
        st.stop()

# ---------- ORDEM DE SERVIÇO ----------
st.subheader("📋 Ordem de Serviço")

with st.form("form_ordem"):
    estado = st.selectbox("Estado da ordem", ["Entrada", "Em andamento", "Finalizado"])
    mecanico = st.text_input("Mecânico responsável")
    previsao = st.date_input("Previsão de entrega")

    st.markdown("**Serviço**")
    desc_servico = st.text_input("Descrição do serviço")
    valor_servico = st.number_input("Valor do serviço (R$)", min_value=0.0, step=10.0)

    st.markdown("**Peça**")
    desc_peca = st.text_input("Descrição da peça")
    valor_peca = st.number_input("Valor da peça (R$)", min_value=0.0, step=10.0)

    enviado = st.form_submit_button("Salvar ordem de serviço")

    if enviado:
        try:
            db.collection("ordens_servico").add({
                "cliente_id": cliente_id,
                "carro_id": carro_id,
                "oficina_id": oficina_id,
                "estado": estado,
                "mecanico": mecanico,
                "previsao": str(previsao),
                "servicos": [{"descricao": desc_servico, "valor": valor_servico}],
                "pecas": [{"descricao": desc_peca, "valor": valor_peca}],
                "valor_total": valor_servico + valor_peca,
                "criado_em": firestore.SERVER_TIMESTAMP
            })
            st.success("✅ Ordem de serviço salva com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar ordem: {e}")
