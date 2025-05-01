# 1_Gestao_cliente.py

import streamlit as st
from firebase_config import db

st.set_page_config(page_title="Gestão de Clientes", page_icon="👥", layout="centered")

st.title("👥 Gestão de Clientes")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

oficina_id = st.session_state.usuario

# 🔍 Busca
busca = st.text_input("Buscar por nome, CPF ou telefone").strip().lower()

# 📥 Cargar clientes
clientes_ref = db.collection("clientes").where("oficina_id", "==", oficina_id)
clientes_docs = clientes_ref.stream()

clientes = []
for doc in clientes_docs:
    data = doc.to_dict()
    data["id"] = doc.id
    if not busca or busca in data.get("nome", "").lower() or busca in data.get("cpf", "").lower() or busca in data.get("telefone", "").lower():
        clientes.append(data)

if not clientes:
    st.info("Nenhum cliente encontrado.")
    st.stop()

# 📋 Lista de clientes
cliente_opcoes = [f"{c['nome']} ({c['cpf']})" for c in clientes]
selecionado = st.selectbox("Selecione um cliente para editar:", range(len(cliente_opcoes)), format_func=lambda i: cliente_opcoes[i])
cliente = clientes[selecionado]

# ✏️ Formulário de edição
with st.form("editar_cliente"):
    st.subheader("✏️ Editar Cliente")
    nome = st.text_input("Nome", value=cliente.get("nome", ""))
    cpf = st.text_input("CPF", value=cliente.get("cpf", ""))
    telefone = st.text_input("Telefone", value=cliente.get("telefone", ""))
    endereco = st.text_input("Endereço", value=cliente.get("endereco", ""))

    salvar = st.form_submit_button("Salvar alterações")
    if salvar:
        # Verificar CPF/telefone duplicado em outro cliente
        duplicado = False
        cpf_dup = db.collection("clientes").where("cpf", "==", cpf).where("oficina_id", "==", oficina_id).stream()
        for d in cpf_dup:
            if d.id != cliente["id"]:
                st.warning("⚠️ Já existe outro cliente com este CPF.")
                duplicado = True
                break

        tel_dup = db.collection("clientes").where("telefone", "==", telefone).where("oficina_id", "==", oficina_id).stream()
        for d in tel_dup:
            if d.id != cliente["id"]:
                st.warning("⚠️ Já existe outro cliente com este telefone.")
                duplicado = True
                break

        if not duplicado:
            try:
                db.collection("clientes").document(cliente["id"]).update({
                    "nome": nome,
                    "cpf": cpf,
                    "telefone": telefone,
                    "endereco": endereco
                })
                st.success("Cliente atualizado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

# 🗑️ Excluir cliente
st.markdown("---")
st.subheader("🗑️ Excluir Cliente")
if st.button("Excluir este cliente"):
    confirmar = st.text_input("Digite CONFIRMAR para excluir permanentemente este cliente:")
    if confirmar == "CONFIRMAR":
        try:
            db.collection("clientes").document(cliente["id"]).delete()
            st.success("Cliente excluído com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao excluir cliente: {e}")
