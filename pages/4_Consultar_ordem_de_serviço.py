# 4_Consultar_ordem_de_servico.py (corrigido com totais e porcentagem adicional de peças)

import streamlit as st
from firebase_config import db
from firebase_admin import firestore
from jinja2 import Environment, FileSystemLoader
import pdfkit
import os
import tempfile

st.set_page_config(page_title="Consultar Ordens de Serviço", page_icon="📄", layout="centered")

st.title("📄 Consultar Ordens de Serviço")

@st.cache_data
def gerar_pdf(template_name, cliente, carro, ordem):
    # Calcular subtotais e total no Python
    total_servicos = sum(s.get("valor", 0) for s in ordem.get("servicos", []))
    total_pecas = sum(p.get("valor", 0) for p in ordem.get("pecas", []))
    total_geral = total_servicos + total_pecas

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)

    html = template.render(
        cliente=cliente,
        carro=carro,
        ordem=ordem,
        total_servicos=total_servicos,
        total_pecas=total_pecas,
        total_geral=total_geral,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdfkit.from_string(html, tmp.name)
        tmp.seek(0)
        return tmp.read()



if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado.")
    st.stop()

oficina_id = st.session_state.usuario

# 🔍 Busca
st.subheader("🔍 Buscar")
tipo = st.radio("Buscar por:", ["Cliente", "Carro"], horizontal=True)
busca = st.text_input("Digite nome, CPF, telefone, placa, marca ou modelo").strip().lower()

cliente = None
carro = None
ordens = []

if busca:
    if tipo == "Cliente":
        ref = db.collection("clientes").where("oficina_id", "==", oficina_id).stream()
        for doc in ref:
            c = doc.to_dict()
            if any(busca in c.get(campo, "").lower() for campo in ["nome", "cpf", "telefone"]):
                cliente = c
                cliente["id"] = doc.id
                break
        if cliente:
            carros = db.collection("carros").where("cliente_id", "==", cliente["id"]).stream()
            for car_doc in carros:
                carro = car_doc.to_dict()
                carro["id"] = car_doc.id
                ordens_ref = db.collection("ordens_servico").where("carro_id", "==", carro["id"]).stream()
                ordens.extend([doc.to_dict() | {"id": doc.id} for doc in ordens_ref])
    else:
        carros = db.collection("carros").where("oficina_id", "==", oficina_id).stream()
        for doc in carros:
            c = doc.to_dict()
            if any(busca in c.get(campo, "").lower() for campo in ["placa", "marca", "modelo"]):
                carro = c
                carro["id"] = doc.id
                break
        if carro:
            cliente_doc = db.collection("clientes").document(carro["cliente_id"]).get()
            cliente = cliente_doc.to_dict() if cliente_doc.exists else None
            if cliente:
                cliente["id"] = cliente_doc.id
            ordens_ref = db.collection("ordens_servico").where("carro_id", "==", carro["id"]).stream()
            ordens = [doc.to_dict() | {"id": doc.id} for doc in ordens_ref]

# Mostrar dados encontrados
if cliente:
    st.subheader("👤 Cliente")
    st.text(f"Nome: {cliente.get('nome')}")
    st.text(f"CPF: {cliente.get('cpf')}")
    st.text(f"Telefone: {cliente.get('telefone')}")
    st.text(f"Endereço: {cliente.get('endereco')}")

if carro:
    st.subheader("🚗 Carro")
    st.text(f"Placa: {carro.get('placa')}")
    st.text(f"Marca: {carro.get('marca')} | Modelo: {carro.get('modelo')} | Cor: {carro.get('cor')} | Ano: {carro.get('ano')} | KM: {carro.get('km')}")

if ordens:
    st.subheader(f"📋 Ordens encontradas: {len(ordens)}")
    for ordem in ordens:
        st.markdown("---")
        st.markdown(f"**Estado:** {ordem.get('estado')}")
        st.markdown(f"**Mecânico:** {ordem.get('mecanico')}")
        st.markdown(f"**Previsão de entrega:** {ordem.get('previsao')}")

        st.markdown("**Serviços:**")
        total_servico = 0.0
        for s in ordem.get("servicos", []):
            valor = float(s.get("valor", 0))
            st.write(f"- {s.get('descricao')} - R$ {valor:.2f}")
            total_servico += valor

        st.markdown("**Peças:**")
        total_peca = 0.0
        for p in ordem.get("pecas", []):
            quant = float(p.get("quant", 1)) if p.get("quant") else 1
            valor_unit = float(p.get("valor", 0))
            valor_total = quant * valor_unit
            st.write(f"- {p.get('descricao')} - R$ {valor_total:.2f}")
            total_peca += valor_total

        total = total_servico + total_peca
        st.markdown(f"**Total:** R$ {total:.2f}")

        # Gerar PDF
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📄 PDF Cliente "):
                pdf = gerar_pdf("template.html", cliente, carro, ordem)
                name_cliente = f"{carro.get('placa')}_{carro.get('marca')}_{carro.get('modelo')} - CLIENTE.pdf"
                st.download_button("Download PDF Cliente", pdf, file_name=name_cliente)
        with col2:
            if st.button(f"📄 PDF Oficina "):
                pdf = gerar_pdf("template_2.html", cliente, carro, ordem)
                name_cliente_2 = f"{carro.get('placa')}_{carro.get('marca')}_{carro.get('modelo')} - OFICINA.pdf"
                st.download_button("Download PDF Oficina", pdf, file_name=name_cliente_2)
else:
    if busca:
        st.warning("Nenhuma ordem encontrada.")
