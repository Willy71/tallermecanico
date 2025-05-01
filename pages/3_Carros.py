# 2_Gestao_carro.py

import streamlit as st
from firebase_config import db

st.set_page_config(page_title="Gestão de Carros", page_icon="🚗", layout="centered")

st.title("🚗 Gestão de Carros")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

oficina_id = st.session_state.usuario

# 🔍 Busca
busca = st.text_input("Buscar por placa, marca ou modelo").strip().lower()

# 📥 Carregar carros
carros_ref = db.collection("carros").where("oficina_id", "==", oficina_id)
carros_docs = carros_ref.stream()

carros = []
for doc in carros_docs:
    data = doc.to_dict()
    data["id"] = doc.id
    if not busca or busca in data.get("placa", "").lower() or busca in data.get("marca", "").lower() or busca in data.get("modelo", "").lower():
        carros.append(data)

if not carros:
    st.info("Nenhum carro encontrado.")
    st.stop()

# 📋 Lista de carros
carro_opcoes = [f"{c['placa']} - {c['marca']} {c['modelo']}" for c in carros]
selecionado = st.selectbox("Selecione um carro para editar:", range(len(carro_opcoes)), format_func=lambda i: carro_opcoes[i])
carro = carros[selecionado]

# ✏️ Formulário de edição
with st.form("editar_carro"):
    st.subheader("✏️ Editar Carro")
    placa = st.text_input("Placa", value=carro.get("placa", "")).upper()
    marca = st.text_input("Marca", value=carro.get("marca", ""))
    modelo = st.text_input("Modelo", value=carro.get("modelo", ""))
    ano = st.text_input("Ano", value=carro.get("ano", ""))
    cor = st.text_input("Cor", value=carro.get("cor", ""))
    km = st.text_input("KM", value=carro.get("km", ""))

    salvar = st.form_submit_button("Salvar alterações")
    if salvar:
        # Verificar se outra carro tem mesma placa
        duplicado = False
        placa_dup = db.collection("carros").where("placa", "==", placa).where("oficina_id", "==", oficina_id).stream()
        for d in placa_dup:
            if d.id != carro["id"]:
                st.warning("⚠️ Já existe outro carro com esta placa.")
                duplicado = True
                break

        if not duplicado:
            try:
                db.collection("carros").document(carro["id"]).update({
                    "placa": placa,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "cor": cor,
                    "km": km
                })
                st.success("Carro atualizado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

# 🗑️ Excluir carro
st.markdown("---")
st.subheader("🗑️ Excluir Carro")
if st.button("Excluir este carro"):
    confirmar = st.text_input("Digite CONFIRMAR para excluir permanentemente este carro:")
    if confirmar == "CONFIRMAR":
        try:
            db.collection("carros").document(carro["id"]).delete()
            st.success("Carro excluído com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao excluir carro: {e}")
