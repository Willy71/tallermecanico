# pages/4_Consultar_ordem_de_servico.py

import streamlit as st
from firebase_config import db

st.set_page_config(page_title="Consultar Ordem de Serviço", page_icon="📄", layout="centered")

st.title("📄 Consultar Ordem de Serviço")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para consultar ordens.")
    st.stop()

# 🔍 Tipo de busca
busca_por = st.radio("Buscar por:", ["CPF do Cliente", "Placa do Carro"])
busca_valor = st.text_input("Digite o valor para busca").strip().upper()

if busca_valor:
    cliente = None
    carro = None
    ordens = []

    if busca_por == "CPF do Cliente":
        # Buscar cliente
        clientes_ref = db.collection("clientes").where("cpf", "==", busca_valor).where("oficina_id", "==", st.session_state.usuario)
        for doc in clientes_ref.stream():
            cliente = doc.to_dict()
            cliente["id"] = doc.id
            break

        if cliente:
            # Buscar carros do cliente
            carros_ref = db.collection("carros").where("cliente_id", "==", cliente["id"])
            carros = [doc.to_dict() | {"id": doc.id} for doc in carros_ref.stream()]

            # Buscar ordens por cliente
            ordens_ref = db.collection("ordens_servico").where("cliente_id", "==", cliente["id"]).where("oficina_id", "==", st.session_state.usuario)
            ordens = [doc.to_dict() | {"id": doc.id} for doc in ordens_ref.stream()]

    else:
        # Buscar carro por placa
        carros_ref = db.collection("carros").where("placa", "==", busca_valor).where("oficina_id", "==", st.session_state.usuario)
        for doc in carros_ref.stream():
            carro = doc.to_dict()
            carro["id"] = doc.id
            break

        if carro:
            # Buscar cliente do carro
            cliente_ref = db.collection("clientes").document(carro["cliente_id"]).get()
            cliente = cliente_ref.to_dict() if cliente_ref.exists else None
            if cliente:
                cliente["id"] = cliente_ref.id

            # Buscar ordens por carro
            ordens_ref = db.collection("ordens_servico").where("carro_id", "==", carro["id"]).where("oficina_id", "==", st.session_state.usuario)
            ordens = [doc.to_dict() | {"id": doc.id} for doc in ordens_ref.stream()]

    # Mostrar resultados
    if cliente:
        st.subheader("👤 Cliente")
        st.text(f"Nome: {cliente.get('nome')}")
        st.text(f"CPF: {cliente.get('cpf')}")
        st.text(f"Telefone: {cliente.get('telefone')}")

    if carro:
        st.subheader("🚗 Carro")
        st.text(f"Placa: {carro.get('placa')}")
        st.text(f"Modelo: {carro.get('marca')} {carro.get('modelo')}")

    if ordens:
        st.subheader(f"📋 {len(ordens)} Ordem(ns) de Serviço encontrada(s)")

        for ordem in ordens:
            st.markdown("---")
            st.markdown(f"**Estado:** {ordem.get('estado')}")
            st.markdown(f"**Mecânico:** {ordem.get('mecanico')}")
            st.markdown(f"**Previsão de entrega:** {ordem.get('previsao')}")

            # Serviços
            st.markdown("**Serviços:**")
            total_servico = 0
            for serv in ordem.get("servicos", []):
                st.write(f"- {serv['descricao']} - R$ {serv['valor']:.2f}")
                total_servico += serv['valor']

            # Peças
            st.markdown("**Peças:**")
            total_peca = 0
            for peca in ordem.get("pecas", []):
                st.write(f"- {peca['descricao']} - R$ {peca['valor']:.2f}")
                total_peca += peca['valor']

            # Total geral
            st.markdown(f"**Total:** R$ {total_servico + total_peca:.2f}")
    else:
        st.warning("Nenhuma ordem encontrada para essa busca.")
