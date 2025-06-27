import streamlit as st
import pandas as pd
from firebase_config import db
from firebase_admin import firestore

# Config página
st.set_page_config(page_title="Histórico do Veículo", page_icon="📋", layout="wide")

# Estilos y fondo oscuro
st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main {
    background-color: #00001a;
}
[data-testid="stHeader"], [data-testid="stSidebar"] {
    background: rgba(0,0,0,0);
}
[data-testid="stToolbar"] {
    right: 2rem;
}
</style>
""", unsafe_allow_html=True)

from firebase_config import db

def carregar_ordens_firebase():
    try:
        user_id = st.session_state.usuario
        ordens = db.collection("usuarios").document(user_id).collection("ordens_servico").stream()
        lista = [doc.to_dict() for doc in ordens]
        return pd.DataFrame(lista)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def buscar_por_placa(placa, df):
    if df.empty:
        return None
    resultado = df[df['placa'].astype(str).str.upper().str.strip() == placa.upper().strip()]
    if not resultado.empty:
        return resultado
    return pd.DataFrame()

def formatar_dos(valor):
    try:
        valor_float = float(valor)
        return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"


# Inicialización de estado
if "buscar_historico" not in st.session_state:
    st.session_state.buscar_historico = False

st.markdown("<h2 style='color: gold;'>📋 Histórico de Veículo</h2>", unsafe_allow_html=True)

# Interfaz con input + botón
with st.container():
    col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 2])
    with col1:
        placa_input = st.text_input("Digite a placa do veículo:", key="placa_hist_input").strip().upper()
    with col2:
        st.write("")  # Espaciador
        st.write("")  # Espaciador
        buscar = st.button("Buscar", key="buscar_historico_btn")

if buscar:
    st.session_state.buscar_historico = True

# Procesar búsqueda si fue activada
if st.session_state.buscar_historico and placa_input:
    df = carregar_ordens_firebase()
    historico = buscar_por_placa(placa_input, df)

    if historico.empty:
        st.warning("Nenhum histórico encontrado para essa placa.")
    else:
        historico = historico.sort_values(by="date_in")

        # Mostrar info principal del vehículo
        veiculo = historico.iloc[-1]
        st.markdown(f"""
        <div style='background-color: #262730; padding: 20px; border-radius: 10px;'>
            <h4 style='color: gold;'>🚗 Dados do Veículo</h4>
            <p style='color: white;'>Placa: <strong>{veiculo['placa']}</strong></p>
            <p style='color: white;'>Marca: {veiculo['carro']} | Modelo: {veiculo['modelo']}</p>
            <p style='color: white;'>Ano: {veiculo['ano']} | Cor: {veiculo['cor']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # Mostrar historial
        for _, row in historico.iterrows():
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
                <h5 style='color: gold;'>🛠️ Visita em {row['date_in']} - Estado: {row['estado']}</h5>
            """, unsafe_allow_html=True)

            st.markdown("<h6 style='color: #00ffcc;'>🔧 Serviços:</h6>", unsafe_allow_html=True)
            for n in range(1, 13):
                desc = row.get(f'desc_ser_{n}')
                val = row.get(f'valor_serv_{n}')
                if desc and str(desc).strip():
                    st.markdown(f"<p style='color:white;'>• {desc} — <strong>R$ {formatar_dos(val)}</strong></p>", unsafe_allow_html=True)


            st.markdown("<h6 style='color: #00ffcc;'>🧩 Peças utilizadas:</h6>", unsafe_allow_html=True)
            for n in range(1, 17):
                desc = row.get(f'desc_peca_{n}')
                val = row.get(f'valor_total_peca_{n}')
                if desc and str(desc).strip() and val and float(val) > 0:
                    st.markdown(f"<p style='color:white;'>• {desc} — <strong>R$ {formatar_dos(val)}</strong></p>", unsafe_allow_html=True)


            st.markdown("</div>", unsafe_allow_html=True)

