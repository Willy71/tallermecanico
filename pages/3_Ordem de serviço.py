# 3_Ordem de serviço.py

import streamlit as st
from firebase_config import db
from firebase_admin import firestore

st.set_page_config(page_title="Nova Ordem de Serviço", page_icon="🧾", layout="centered")

st.title("🧾 Nova Ordem de Serviço")

# Verifica login
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🔍 Busca por CPF ou Placa
busca = st.radio("Buscar por:", ["CPF do Cliente", "Placa do Carro"])

input_busca = st.text_input("Digite o CPF ou a Placa").strip().upper()
dados_cliente = None
dados_carro = None

if input_busca:
    if busca == "CPF do Cliente":
        clientes = db.collection("clientes").where("cpf", "==", input_busca).where("oficina_id", "==", st.session_state.usuario).stream()
        for doc in clientes:
            dados_cliente = doc.to_dict()
            dados_cliente["id"] = doc.id
    else:
        carros = db.collection("carros").where("placa", "==", input_busca).where("oficina_id", "==", st.session_state.usuario).stream()
        for doc in carros:
            dados_carro = doc.to_dict()
            dados_carro["id"] = doc.id
            # buscar cliente do carro
            cliente = db.collection("clientes").document(dados_carro["cliente_id"]).get()
            dados_cliente = cliente.to_dict() if cliente.exists else None

# Exibir dados se encontrados
if dados_cliente and (busca == "CPF do Cliente" or dados_carro):
    st.subheader("👤 Cliente")
    st.text(f"Nome: {dados_cliente.get('nome')}")
    st.text(f"CPF: {dados_cliente.get('cpf')}")
    st.text(f"Telefone: {dados_cliente.get('telefone')}")

    if dados_carro:
        st.subheader("🚗 Carro")
        st.text(f"Placa: {dados_carro.get('placa')}")
        st.text(f"Marca: {dados_carro.get('marca')} - {dados_carro.get('modelo')}")
        st.text(f"Ano: {dados_carro.get('ano')} | KM: {dados_carro.get('km')}")
    else:
        # buscar todos os carros do cliente
        carros = db.collection("carros").where("cliente_id", "==", dados_cliente["id"]).stream()
        dados_carros = [doc.to_dict() | {"id": doc.id} for doc in carros]
        if dados_carros:
            dados_carro = st.selectbox("Selecione um carro", dados_carros, format_func=lambda x: f"{x['placa']} - {x['marca']} {x['modelo']}")
        else:
            st.error("Este cliente não possui carros cadastrados.")
            st.stop()

    # 📋 Formulário da ordem
    with st.form("form_ordem"):
        estado = st.selectbox("Estado", ["Entrada", "Em andamento", "Finalizado"])
        mecanico = st.text_input("Mecânico responsável")
        previsao = st.date_input("Previsão de entrega")
        descricao_servico = st.text_input("Descrição do serviço")
        valor_servico = st.number_input("Valor do serviço", min_value=0.0, step=10.0)
        descricao_peca = st.text_input("Descrição da peça")
        valor_peca = st.number_input("Valor da peça", min_value=0.0, step=10.0)
        enviado = st.form_submit_button("Salvar ordem de serviço")

        if enviado:
            try:
                db.collection("ordens_servico").add({
                    "oficina_id": st.session_state.usuario,
                    "cliente_id": dados_cliente["id"],
                    "carro_id": dados_carro["id"],
                    "estado": estado,
                    "mecanico": mecanico,
                    "previsao": str(previsao),
                    "servicos": [{
                        "descricao": descricao_servico,
                        "valor": valor_servico
                    }],
                    "pecas": [{
                        "descricao": descricao_peca,
                        "valor": valor_peca
                    }],
                    "valor_total": valor_servico + valor_peca,
                    "criado_em": firestore.SERVER_TIMESTAMP
                })
                st.success("Ordem de serviço salva com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar ordem: {e}")
else:
    if input_busca:
        st.warning("Nenhum cliente ou carro encontrado com esse valor.")
