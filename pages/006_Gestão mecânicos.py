# 006_Gestão mecânicos.py

import streamlit as st
import pandas as pd
from datetime import datetime
from firebase_config import db

# --------------------------- CONFIG INICIAL ----------------------------------
st.set_page_config(page_title="Trabalhos por Mecânico", layout="wide", page_icon="🛠️")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main {
    background-color: #00001a;
    color: white;
}
</style>
""", unsafe_allow_html=True)

if "usuario" not in st.session_state or not st.session_state.usuario:
    st.warning("Você precisa estar logado para acessar o painel de controle.")
    st.stop()

@st.cache_data(ttl=600)
def cargar_dados():
    try:
        user_id = st.session_state.usuario
        ordens = db.collection("usuarios").document(user_id).collection("ordens_servico").stream()
        registros = [doc.to_dict() for doc in ordens]
        df = pd.DataFrame(registros)

        df["date_in"] = pd.to_datetime(df["date_in"], errors='coerce', dayfirst=True)
        df["date_out"] = pd.to_datetime(df.get("date_out", None), errors='coerce', dayfirst=True)
        for i in range(1, 13):
            df[f"valor_serv_{i}"] = pd.to_numeric(df.get(f"valor_serv_{i}", 0), errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ordens: {e}")
        return pd.DataFrame()


def formatar_dos(valor):
    try:
        valor_float = float(valor)
        return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"

@st.cache_data(ttl=600)
def cargar_mecanicos():
    try:
        user_id = st.session_state.usuario
        docs = db.collection("usuarios").document(user_id).collection("mecanicos").stream()
        nomes = [doc.to_dict().get("nome", "").strip() for doc in docs if doc.exists]
        return [n for n in nomes if n]
    except Exception as e:
        st.error(f"Erro ao carregar mecânicos: {e}")
        return []

# -------------------------- CONSULTA DE TRABAJOS ------------------------------
st.title("🛠️ Relatório de Trabalhos por Mecânico")

#with st.sidebar:
#    st.header("🔍 Filtros")
#    data_inicial = st.date_input("Data inicial", datetime(datetime.now().year, datetime.now().month, 1))
#    st.caption(f"📅 Início selecionado: {data_inicial.strftime('%d/%m/%Y')}")
    
#    data_final = st.date_input("Data final", datetime.now())
#    st.caption(f"📅 Fim selecionado: {data_final.strftime('%d/%m/%Y')}")

#    comissao_pct = st.slider("% Comissão do mecânico", 0.0, 100.0, 40.0, step=5.0)

#    mecanicos_lista = cargar_mecanicos()
#    mecanico_filtro = st.selectbox("Filtrar por mecânico", options=["Todos"] + mecanicos_lista)

st.markdown("## 🎯 Filtros")

df = cargar_dados()
#df["date_in"] = pd.to_datetime(df["date_in"], dayfirst=True, errors='coerce')
#df = df.dropna(subset=["date_in"])
#df["date_in"] = df["date_in"].dt.date  # apenas a data

if df.empty:
    st.warning("Nenhum dado com datas válidas foi encontrado.")
    st.stop()

data_min = df["date_in"].min()
data_max = df["date_in"].max()

col1, col2 = st.columns(2)
with col1:
    data_inicial = st.date_input("📅 Data inicial", value=data_min, min_value=data_min, max_value=data_max, key="inicio")
with col2:
    data_final = st.date_input("📅 Data final", value=data_max, min_value=data_inicial, max_value=data_max, key="fim")

col3, col4 = st.columns([2, 2])
with col3:
    comissao_pct = st.slider("% Comissão do mecânico", 0.0, 100.0, 40.0, step=5.0)
with col4:
    mecanicos_lista = cargar_mecanicos()
    mecanico_filtro = st.selectbox("👨‍🔧 Filtrar por mecânico", options=["Todos"] + mecanicos_lista)


    #atualizar = st.button("🔄 Atualizar relatório")

# ------------------------ FILTRAR E AGRUPAR ----------------------------------
#if atualizar:
df = cargar_dados()
df_filtrado = df[(df['date_in'] >= pd.to_datetime(data_inicial)) & (df['date_in'] <= pd.to_datetime(data_final))]

# Remover linhas sem mecânico
#df_filtrado = df_filtrado[df_filtrado['mecanico'].notna() & (df_filtrado['mecanico'] != '')]
#if mecanico_filtro != "Todos":
#    df_filtrado = df_filtrado[df_filtrado["mecanico"] == mecanico_filtro]

#colunas_servicos = [f"valor_serv_{i}" for i in range(1, 13)]
#df_filtrado[colunas_servicos] = df_filtrado[colunas_servicos].fillna(0)
#df_filtrado["total_servicos"] = df_filtrado[colunas_servicos].sum(axis=1)
# Remover linhas sem mecânico
df_filtrado = df_filtrado[df_filtrado['mecanico'].notna() & (df_filtrado['mecanico'] != '')]

# Filtrar por mecânico, se selecionado
if mecanico_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["mecanico"] == mecanico_filtro]

# ✅ Filtrar apenas ordens com status Entregado ou Entregado e cobrado
df_filtrado = df_filtrado[df_filtrado["estado"].isin(["Entregado", "Entregado e cobrado"])]

# Calcular total de serviços
colunas_servicos = [f"valor_serv_{i}" for i in range(1, 13)]
df_filtrado[colunas_servicos] = df_filtrado[colunas_servicos].fillna(0)
df_filtrado["total_servicos"] = df_filtrado[colunas_servicos].sum(axis=1)


# Agrupar por mecânico
resultado = df_filtrado.groupby("mecanico")["total_servicos"].sum().reset_index()
st.write(f"🔍 Total de ordens encontradas: {len(df_filtrado)}")
resultado["comissao"] = resultado["total_servicos"] * (comissao_pct / 100)

# -------------------------- EXIBIR RESULTADO ---------------------------------
st.subheader("📊 Resumo por Mecânico")

resultado["total_servicos_fmt"] = resultado["total_servicos"].apply(formatar_dos)
resultado["comissao_fmt"] = resultado["comissao"].apply(formatar_dos)

st.dataframe(resultado[["mecanico", "total_servicos_fmt", "comissao_fmt"]], use_container_width=True)


# Mostrar totais
total_carros = len(df_filtrado)
total_geral = resultado["total_servicos"].sum()
total_comissao = resultado["comissao"].sum()

st.markdown(f"**🚗 Total de carros atendidos no período:** {total_carros}")
st.markdown(f"**🔧 Total de serviços no período:** R$ {formatar_dos(total_geral)}")
st.markdown(f"**💰 Total de comissões:** R$ {formatar_dos(total_comissao)} ({comissao_pct:.0f}%)")


st.subheader("📄 Detalhes dos Serviços Realizados")

df_filtrado["comissao"] = df_filtrado["total_servicos"] * (comissao_pct / 100)
df_filtrado["total_servicos_fmt"] = df_filtrado["total_servicos"].apply(formatar_dos)
df_filtrado["comissao_fmt"] = df_filtrado["comissao"].apply(formatar_dos)
df_filtrado["date_in_fmt"] = df_filtrado["date_in"].dt.strftime("%d/%m/%Y")

st.dataframe(df_filtrado[[
    "mecanico", "carro", "modelo", "placa", "date_in_fmt", "total_servicos_fmt", "comissao_fmt"
]], use_container_width=True)

 # ---------------------- GESTÃO DE MECÂNICOS ------------------------------
st.markdown("---")
st.subheader("🔧 Gerenciar lista de Mecânicos")

#ws_mecanicos = gc.open_by_key(SPREADSHEET_KEY).worksheet("Mecanicos")
mecanicos_existentes = cargar_mecanicos()

with st.expander("➕ Adicionar novo mecânico"):
    novo_mecanico = st.text_input("Nome do novo mecânico")
    if st.button("Adicionar", key="add_mecanico"):
        if not novo_mecanico.strip():
            st.warning("O nome não pode estar vazio.")
        elif novo_mecanico in mecanicos_existentes:
            st.warning("Esse mecânico já está na lista.")
        else:
            db.collection("usuarios").document(user_id).collection("mecanicos").add({"nome": novo_mecanico})
            st.success(f"Mecânico '{novo_mecanico}' adicionado com sucesso!")

with st.expander("📝 Editar ou remover mecânico existente"):
    mecanico_selecionado = st.selectbox("Selecione o mecânico", options=mecanicos_existentes)

    novo_nome = st.text_input("Editar nome", value=mecanico_selecionado, key="editar_nome")
    if st.button("Salvar edição"):
        try:
            colecao = db.collection("usuarios").document(user_id).collection("mecanicos").stream()
            for doc in colecao:
                if doc.to_dict().get("nome", "") == mecanico_selecionado:
                    doc.reference.update({"nome": novo_nome})
                    st.success(f"Nome atualizado para '{novo_nome}'.")
        except Exception as e:
            st.error(f"Erro ao editar: {e}")

    if st.button("Remover mecânico"):
        try:
            colecao = db.collection("usuarios").document(user_id).collection("mecanicos").stream()
            for doc in colecao:
                if doc.to_dict().get("nome", "") == mecanico_selecionado:
                    doc.reference.delete()
                    st.success(f"Mecânico '{mecanico_selecionado}' removido.")
        except Exception as e:
            st.error(f"Erro ao remover: {e}")
