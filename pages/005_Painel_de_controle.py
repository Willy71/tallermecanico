# 005_Painel_de_controle.py
import streamlit as st
import pandas as pd
from datetime import datetime
from firebase_config import db

#===================================================================================================================================================================
# Configuración de página (igual que tu código original)
st.set_page_config(
    page_title="Painel de controle",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS (copiados de tu código original)
reduce_space = """
<style type="text/css">
div[data-testid="stAppViewBlockContainer"]{
    padding-top:30px;
}
</style>
"""
st.markdown(reduce_space, unsafe_allow_html=True)

# Colocar background azul navy
page_bg_color = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-color: #00001a;
}}

[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}

[data-testid="stToolbar"] {{
right: 2rem;
}}

[data-testid="stSidebar"] {{
background: rgba(0,0,0,0);
}}
</style>
"""
st.markdown(page_bg_color, unsafe_allow_html=True)

#===================================================================================================================================================================

from firebase_config import db

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        user_id = st.session_state.usuario
        docs = db.collection("usuarios").document(user_id).collection("ordens_servico").stream()
        registros = [doc.to_dict() for doc in docs]
        df = pd.DataFrame(registros)

        # Conversão de datas
        df['date_in'] = pd.to_datetime(df['date_in'], dayfirst=True, errors='coerce')
        df['date_prev'] = pd.to_datetime(df['date_prev'], dayfirst=True, errors='coerce')
        df['date_out'] = pd.to_datetime(df['date_out'], dayfirst=True, errors='coerce')

        df_completo = df.copy()

        # Filtrar apenas veículos NÃO Entregados
        df_filtrado = df[~df['estado'].astype(str).str.strip().str.lower().eq('entregado')]

        return df_filtrado.sort_values('date_in', ascending=False), df_completo
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        return pd.DataFrame(), pd.DataFrame()

#===================================================================================================================================================
# Título e carregamento de dados
st.title("📊 Painel de Controle de Veículos")
#===================================================================================================================================================
# Carregando os dados corretamente
dados, dados_completos = carregar_dados()

# Normalizar a coluna 'estado'
dados_completos['estado'] = dados_completos['estado'].astype(str).str.strip().str.lower()

# Filtrar registros com estado "entregado"
entregados_df = dados_completos[dados_completos['estado'] == 'entregado']
entregues_total = entregados_df.shape[0]

# Obter o maior user_id (último ID)
ultimo_id = dados_completos['user_id'].max()

# Calcular veículos no taller
veiculos_no_taller = ultimo_id - entregues_total -1

# 📌 FILTRAR DADOS: excluir entregues da visualização
dados = dados[dados['estado'].astype(str).str.strip().str.lower() != 'entregado']


#===================================================================================================================================================

# 🔒 Checar si hay datos
if dados.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()
else:
    # Carregar dados e tratar datas
    dados, dados_completos = carregar_dados()
    dados['estado'] = dados['estado'].astype(str).str.strip()
    dados['date_in'] = pd.to_datetime(dados['date_in'], dayfirst=True, errors='coerce')
    dados = dados.dropna(subset=["date_in"])
    dados['date_in'] = dados['date_in'].dt.date  # remover hora
    
    # Filtros visuais na área principal
    st.markdown("## 🔍 Filtros")
    
    min_date, max_date = dados['date_in'].min(), dados['date_in'].max()
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("📅 Data inicial", value=min_date, min_value=min_date, max_value=max_date, key="painel_inicio")
    with col2:
        data_final = st.date_input("📅 Data final", value=max_date, min_value=data_inicial, max_value=max_date, key="painel_fim")
    
    estados = dados['estado'].value_counts().index.tolist()
    estado_opcoes = ["Todos"] + estados
    estado_selecionado = st.selectbox("🧾 Status do veículo", estado_opcoes)

    
    # Sidebar com filtros
    #with st.sidebar:
      #  st.header("Filtros")
        # Excluir os veículos entregues da exibição
     #   dados = dados[dados['estado'].astype(str).str.strip().str.lower() != 'entregado']
        
        # Filtro por estado com contagem
      #  estados = dados['estado'].value_counts().index.tolist()
      #  estado_opcoes = ["Todos"] + estados
      #  estado_selecionado = st.selectbox(
     #       "Status do veículo",
     #       estado_opcoes,
      #      format_func=lambda x: f"{x} ({len(dados[dados['estado']==x])})" if x != 'Todos' else x
      #  )
        
        # Filtro por datas com formato brasileiro
      #  min_date, max_date = dados['date_in'].min().date(), dados['date_in'].max().date()
       # faixa_data = st.date_input(
        #    "Período de entrada",
           # value=(min_date, max_date),
          #  min_value=min_date,
         #   max_value=max_date,
        #    format="DD/MM/YYYY"
       # )

    

    # Aplicar filtros
  #  dados_filtrados = dados.copy()
    
 #   if estado_selecionado != "Todos":
   #     dados_filtrados = dados_filtrados[dados_filtrados['estado'] == estado_selecionado]
    
  #  if len(faixa_data) == 2:
   #     dados_filtrados = dados_filtrados[
   #         (dados_filtrados['date_in'].dt.date >= faixa_data[0]) & 
    #        (dados_filtrados['date_in'].dt.date <= faixa_data[1])
     #   ]
    dados_filtrados = dados[
        (dados['date_in'] >= data_inicial) & (dados['date_in'] <= data_final)
    ]
    
    if estado_selecionado != "Todos":
        dados_filtrados = dados_filtrados[dados_filtrados['estado'] == estado_selecionado]



    # Função para formatar datas
    def formatar_data(serie_data):
        return pd.to_datetime(serie_data, errors='coerce').dt.strftime('%d/%m/%Y').fillna('')

    
    # Métricas resumidas
    st.subheader("Visão Geral")
    #veiculos_no_taller = len(dados)

    metricas = [
        ("📋 Registros totais", len(dados_completos)),
        ("🏠 Na Oficina", veiculos_no_taller),
        ("⏳ Orçamento", len(dados[dados['estado'] == "Em orçamento"])),
        ("🛠️ Reparação", len(dados[dados['estado'] == "Em reparação"])),
        ("✅ Prontos", len(dados[dados['estado'] == "Concluido"])),
        ("📅 Hoje", len(dados[dados['date_in'] == datetime.today().date()]))
    ]
    
    cols = st.columns(len(metricas))
    for col, (titulo, valor) in zip(cols, metricas):
        col.metric(titulo, valor)


    # Abas por status
    tabs = st.tabs(["📋 Todos", "🏠 Na Oficina", "⏳ Orçamento", "🛠️ Reparação", "✅ Prontos", "🚫 Não Aprovados"])
    
    with tabs[0]:  # Todos
        dados_mostrar = dados_filtrados[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "mecanico": "Mecánico",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )

    with tabs[1]:  # Na oficina
        na_oficina = dados_filtrados[dados_filtrados['estado'].str.lower().str.strip() != 'entregado']
        dados_mostrar = na_oficina[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "mecanico": "Mecánico",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[2]:  # Orçamento
        orcamento = dados_filtrados[dados_filtrados['estado'] == "Em orçamento"]
        dados_mostrar = orcamento[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        #dados_mostrar['date_prev'] = formatar_data(dados_mostrar['date_prev'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "mecanico": "Mecánico",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[3]:  # Reparação
        reparacao = dados_filtrados[dados_filtrados['estado'] == "Em reparação"]
        dados_mostrar = reparacao[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        #dados_mostrar['date_prev'] = formatar_data(dados_mostrar['date_prev'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "mecanico": "Mecánico",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
    
    with tabs[4]:  # Prontos
        estados_prontos = ["concluido", "entregado", "entregado e cobrado"]
        prontos = dados_filtrados[dados_filtrados['estado'].str.lower().isin(estados_prontos)]
        dados_mostrar = prontos[['date_in', 'date_out', 'placa', 'carro', 'modelo', 'ano', 'estado', 'mecanico','dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        dados_mostrar['date_out'] = formatar_data(dados_mostrar['date_out'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "date_out": "Data de saida",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "mecanico": "Mecánico",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Gráfico de distribuição
    st.subheader("Distribuição por Status")
    contagem_status = dados['estado'].value_counts()
    st.bar_chart(contagem_status)

    with tabs[5]:  # Não Aprovados
        nao_aprovados = dados_filtrados[dados_filtrados['estado'].str.lower().str.strip() == "não aprovado"]
        dados_mostrar = nao_aprovados[['date_in', 'placa', 'carro', 'modelo', 'ano', 'estado', 'dono_empresa']].copy()
        dados_mostrar['date_in'] = formatar_data(dados_mostrar['date_in'])
        st.dataframe(
            dados_mostrar,
            column_config={
                "date_in": "Entrada (D/M/A)",
                "placa": "Placa",
                "carro": "Marca",
                "modelo": "Modelo",
                "ano": "Ano",
                "estado": "Status",
                "dono_empresa": "Cliente"
            },
            hide_index=True,
            use_container_width=True
        )
