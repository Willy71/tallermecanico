# 1_Gestão de ordens de serviço.py

import streamlit as st
from firebase_config import db
from firebase_admin import firestore
import pandas as pd
import re
import datetime
import numpy as np  # Asegúrate de importar numpy para manejar NaN

# Colocar nome na pagina, icone e ampliar a tela
st.set_page_config(
    page_title="Gestão de ordens",
    page_icon="🚗",
    layout="wide"
)

# We reduced the empty space at the beginning of the streamlit
reduce_space ="""
            <style type="text/css">
            /* Remueve el espacio en el encabezado por defecto de las apps de Streamlit */
            div[data-testid="stAppViewBlockContainer"]{
                padding-top:30px;
            }
            </style>
            """
#====================================================================================================================================
# Colocar background azul muy oscuro
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

#====================================================================================================================================
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Você precisa estar logado para registrar ordens.")
    st.stop()

oficina_id = st.session_state.usuario

#====================================================================================================================================
@st.cache_data(ttl=600)
def carregar_ordens():
    try:
        user_id = st.session_state.usuario
        docs = db.collection("usuarios").document(user_id).collection("ordens_servico").stream()
        registros = [doc.to_dict() | {"doc_id": doc.id} for doc in docs]
        return pd.DataFrame(registros)
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        return pd.DataFrame()


# Cargar datos desde Google Sheets
existing_data = carregar_ordens()

@st.cache_data(ttl=600)
def carregar_mecanicos():
    try:
        user_id = st.session_state.usuario
        docs = db.collection("usuarios").document(user_id).collection("mecanicos").stream()
        nomes = [doc.to_dict().get("nome", "").strip() for doc in docs if doc.exists]
        return [n for n in nomes if n]  # Retorna lista de nomes não vazios
    except Exception as e:
        st.error(f"Erro ao carregar mecânicos do Firebase: {e}")
        return []

#=============================================================================================================================
# Función para obtener el próximo ID disponible
def obtener_proximo_id(df):
    if df.empty or 'user_id' not in df.columns:
        return 1  # Si no hay datos, el primer ID es 1
    try:
        # Calcular el máximo ID y sumar 1
        return int(df['user_id'].max()) + 1
    except (ValueError, TypeError):
        # Si hay algún error (por ejemplo, valores no numéricos), retornar 1
        return 1

# Esta función actualiza directamente la fila con el ID correspondiente sin alterar el orden
def atualizar_ordem(worksheet, vendor_to_update, updated_record):
    # Convertir el registro actualizado a DataFrame
    updated_record_df = pd.DataFrame([updated_record])
    try:
        # Obtener la hoja de cálculo
        #worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
    
        # Obtener todos los valores de la columna A (donde están los IDs)
        col_ids = worksheet.col_values(1)  # Columna A = 1
    
        # Buscar la fila exacta donde está el ID
        row_index = None
        for i, val in enumerate(col_ids, start=1):
            if val == str(vendor_to_update):
                row_index = i
                break
    
        if row_index:
            # Actualizar solo la fila correspondiente
            worksheet.update(f"A{row_index}", updated_record_df.values.tolist())
            st.success("Ordem de serviço atualizada com sucesso")
        else:
            st.warning("ID não encontrado. Nenhuma atualização realizada.")
    
    except Exception as e:
        st.error(f"Erro ao atualizar planilha: {str(e)}")

# Función para buscar vehículo por placa
def buscar_por_placa(placa, df):
    if df.empty:
        return None
    
    # Buscar coincidencias exactas (ignorando mayúsculas/minúsculas y espacios)
    resultado = df[df['placa'].astype(str).str.upper().str.strip() == placa.upper().strip()]
    
    if not resultado.empty:
        return resultado.iloc[-1].to_dict()  # Tomar el último ingreso en lugar del primero
    return None

def buscar_ordem_por_placa_ou_id(valor_busca, tipo="placa"):
    try:
        user_id = st.session_state.usuario
        col_ref = db.collection("usuarios").document(user_id).collection("ordens_servico")
        docs = col_ref.stream()
        for doc in docs:
            data = doc.to_dict()
            if tipo == "placa" and data.get("placa", "").upper() == valor_busca.upper():
                return doc.id, data
            elif tipo == "id" and str(data.get("user_id")) == str(valor_busca):
                return doc.id, data
        return None, None
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return None, None

def safe_float(value):
    try:
        return float(str(value).replace(",", "."))
    except:
        return 0.0

#==============================================================================================================================================================


def centrar_imagen(imagen, ancho):
    # Aplicar estilo CSS para centrar la imagen con Markdown
    st.markdown(
        f'<div style="display: flex; justify-content: center;">'
        f'<img src="{imagen}" width="{ancho}">'
        f'</div>',
        unsafe_allow_html=True
    )
    

def centrar_texto(texto, tamanho, color):
    st.markdown(f"<h{tamanho} style='text-align: center; color: {color}'>{texto}</h{tamanho}>",
                unsafe_allow_html=True)
    

def validar_email(email):
    # Expresión regular para validar direcciones de correo electrónico
    patron_email = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    if re.match(patron_email, email):
        return True
    else:
        return False


def validar_numero_telefono(numero):
    # Define una expresión regular para un número de teléfono
    patron = re.compile(r'^\d{11}$')  # Asumiendo un formato de 10 dígitos, ajusta según tus necesidades
    # Comprueba si el número coincide con el patrón
    if patron.match(numero):
        return True
    else:
        return False

# Función para reemplazar NaN con None
def replace_nan_with_none(df):
    return df.replace({np.nan: None})

def line(size, color):
    st.markdown(
        f"<hr style='height:{size}px;border:none;color:{color};background-color:{color};' />",
        unsafe_allow_html=True
    )

def gold_text(text, font_size="inherit", align="left", height="38px"):
    """
    Muestra un texto en color dorado (#FFD700) con formato flexible.
    
    Parámetros:
    - text (str): El texto a mostrar.
    - font_size (str): Tamaño de fuente (ej. "16px", "1.2rem").
    - align (str): Alineación ("left", "center", "right").
    - height (str): Altura del contenedor (ej. "38px").
    """
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; height: {height}; justify-content: {align};">
            <span style="color: #FFD700; font-weight: bold; font-size: {font_size};">{text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def add_space(lines=1):
    """Añade espacios vacíos (vía st.caption)."""
    for _ in range(lines):
        st.caption("")
    
# ----------------------------------------------------------------------------------------------------------------------------------
# Titulo de la pagina
centrar_texto("Gestão de Ordens de Serviço", 1, "white")
    
# ----------------------------------------------------------------------------------------------------------------------------------
# Seleccion de la opcion de CRUD
action = st.selectbox(
    "Escolha uma ação",
    [
        "Nova ordem de serviço", # Insert
        "Atualizar ordem existente", # Update
        "Ver todos as ordens de serviço", # View
        "Apagar ordem de serviço", # Delete
    ],
)

# ----------------------------------------------------------------------------------------------------------------------------------
# Formulario

vendor_to_update = None  # Establecer un valor predeterminado
# Reescritura del bloque "Nova ordem de serviço" con bucles
# para serviços e peças. Este bloque reemplaza el actual dentro del
# if action == "Nova ordem de serviço":

if action == "Nova ordem de serviço":
    st.markdown("### ✏🔧 Nova Ordem de Serviço")
    with st.form(key="ordem"):

        st.markdown("### 🚗 Dados do carro")
    
        col1, col2, col3 = st.columns(3)
        with col1:
            placa_input = st.text_input("Placa").strip().upper()
            placa = ''.join([char.upper() if char.isalpha() else char for char in placa_input])
        with col2:
            carro = st.text_input("Marca")
        with col3:
            modelo = st.text_input("Modelo")
    
        col4, col5, col6 = st.columns(3)
        with col4:
            cor = st.text_input("Cor")
        with col5:
            ano = st.text_input("Ano")
        with col6:
            km = st.text_input("Km")

        col7, col8 = st.columns(2)
        with col7:
            mecanicos_lista = carregar_mecanicos()
            mecanico = st.selectbox("Mecânico responsável", options=mecanicos_lista)
        with col8:
            opcoes_estado = ["Entrada", "Em orçamento", "Aguardando aprovação", "Em reparação", "Concluido", "Não aprovado", "Entregado", "Entregado e cobrado"]
            estado = st.selectbox("Estado do serviço", opcoes_estado)
            
        st.markdown("### 📆 Datas")
        col9, col10, col11 = st.columns(3)
        with col9:
            data_entrada = st.text_input("Data de entrada")
        with col10:
            previsao_entrega = st.text_input("Previsão de entrega")
        with col11:
            data_saida = st.text_input("Data de saida")

        st.markdown("### 💼 Empresa")
        col12, col13, col14 = st.columns(3)
        with col12:
            dono_empresa = st.text_input("Dono / Empresa")
        with col13:
            telefone = st.text_input("Telefone")
        with col14:
            endereco = st.text_input("Endereço")
        #==============================================================================================

        line(4, "blue")
        st.markdown("### ✅ Serviços")

        servicos = []
        for i in range(1, 13):
            colA, colB = st.columns([7.2, 2.2])
            with colA:
                desc = st.text_input(f"Serviço {i}", key=f"desc_ser_{i}_new") #, label_visibility="collapsed"
            with colB:
                valor = st.number_input(f"Valor {i}", min_value=0.0, max_value=100000.0, step=0.01, format="%.2f", key=f"valor_serv_{i}_new") #, label_visibility="collapsed"
            servicos.append((desc, valor))

        line(4, "blue")
        st.markdown("### 🔩 Peças")

        col_perc = st.columns([1])[0]
        with col_perc:
            porcentaje_adicional = st.number_input("% adicional", min_value=0.0, max_value=100.0, value=35.0, step=0.5)

        pecas = []
        for i in range(1, 17):
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            with col1:
                quant = st.text_input(f"Qtd {i}", value="1", key=f"quant_peca_{i}_new")
            with col2:
                desc = st.text_input(f"Descrição {i}", key=f"desc_peca_{i}_new")
            with col3:
                valor = st.number_input(f"Valor unit {i}", value=0.0, min_value=0.0, max_value=100000.0, step=0.01, key=f"valor_peca_{i}_new")
            with col4:
                try:
                    subtotal = float(quant) * valor if quant else 0.0
                    total = subtotal * (1 + porcentaje_adicional / 100)
                except:
                    subtotal = total = 0.0
            pecas.append((quant, desc, valor, subtotal, total))

        submitted = st.form_submit_button("Salvar nova ordem")

        if submitted:
            # Construir y guardar dict con os dados
            user_id = st.session_state.usuario
            dados = {
                "user_id": obtener_proximo_id(existing_data),
                "placa": placa,
                "date_in": data_entrada,
                "date_prev": previsao_entrega,
                "date_out": data_saida,
                "carro": carro,
                "modelo": modelo,
                "cor": cor,
                "km": km,
                "ano": ano,
                "estado": estado,
                "mecanico": mecanico,
                "dono_empresa": dono_empresa,
                "telefone": telefone,
                "endereco": endereco,
                "porcentaje_adicional": porcentaje_adicional,
                "forma_de_pagamento": None
            }

            for i, (desc, valor) in enumerate(servicos, start=1):
                dados[f"desc_ser_{i}"] = desc
                dados[f"valor_serv_{i}"] = valor

            for i, (quant, desc, valor_unit, subtotal, total) in enumerate(pecas, start=1):
                dados[f"quant_peca_{i}"] = quant
                dados[f"desc_peca_{i}"] = desc
                dados[f"valor_peca_{i}"] = valor_unit
                dados[f"sub_tota_peca_{i}"] = subtotal
                dados[f"valor_total_peca_{i}"] = total

            dados["total_costo_inicial"] = sum([v for _, _, _, v, _ in pecas])
            dados["total_costo_final"] = sum([v for _, _, _, _, v in pecas])

            db.collection("usuarios").document(user_id).collection("ordens_servico").add(dados)
            st.success("Ordem de serviço adicionada com sucesso")

# ==============================================================================================================================================================

if action == "Atualizar ordem existente":
    # Buscar ordem
    doc_id = None
    vendor_data = None
    st.markdown("### ✏🔧 Atualizar ordem existente")
    centrar_texto("Selecione o ID ou PLACA da Ordem de serviço que deseja atualizar.", 6, "yellow")
    
     # Eliminar filas con NaN en la columna "user_id"
    existing_data = existing_data.dropna(subset=["user_id"])

    # Convertir la columna "user_id" a enteros
    existing_data["user_id"] = existing_data["user_id"].astype(int)

    with st.container():    
        col200, col201, col202 = st.columns([1.5, 2.5, 6])
        with col200:
            # Opción para buscar por ID o por placa
            search_option = st.radio("Buscar por:", ["Placa", "ID"])
            
            if search_option == "Placa":
                placa_to_search = st.text_input("Digite o número da placa").strip().upper()
                if placa_to_search:
                    doc_id, vendor_data = buscar_ordem_por_placa_ou_id(placa_to_search, tipo="placa")
                    if not vendor_data:
                        st.warning("Nenhuma ordem de serviço encontrada.")
                        st.stop()
                    vendor_to_update = doc_id
            else:
                all_ordens = carregar_ordens()
                ids_disponiveis = all_ordens["user_id"].astype(str).tolist()
                id_selecionado = st.selectbox("Selecione o ID", options=ids_disponiveis)
                doc_id, vendor_data = buscar_ordem_por_placa_ou_id(id_selecionado, tipo="id")
                if not vendor_data:
                    st.warning("Ordem não encontrada.")
                    st.stop()
            
                vendor_to_update = doc_id
                


                            
    #st.subheader("🧪 Diagnóstico de Google Sheets")

    # Mostrar IDs tal como los ve worksheet
    #id_col = worksheet.col_values(1)
    #st.write("📋 Columna A (user_id):", id_col)
    
    if vendor_data is None:
        st.warning("Nenhum dado carregado para edição.")
        st.stop()


   # Formulário completo para edição de ordem (com serviços e peças)

    with st.form("form_update_ordem_completo"):
        st.markdown("### 🖊️ Dados do carro")
    
        col1, col2, col3 = st.columns(3)
        with col1:
            placa = st.text_input("Placa", value=vendor_data.get("placa", ""))
        with col2:
            carro = st.text_input("Marca", value=vendor_data.get("carro", ""))
        with col3:
            modelo = st.text_input("Modelo", value=vendor_data.get("modelo", ""))
    
        col4, col5, col6 = st.columns(3)
        with col4:
            cor = st.text_input("Cor", value=vendor_data.get("cor", ""))
        with col5:
            ano = st.text_input("Ano", value=vendor_data.get("ano", ""))
        with col6:
            km = st.text_input("Km", value=vendor_data.get("km", ""))
    
        col7, col8 = st.columns(2)
        with col7:
            mecanicos_lista = carregar_mecanicos()
            mecanico = st.selectbox("Mecânico", options=mecanicos_lista, index=mecanicos_lista.index(vendor_data.get("mecanico", "")) if vendor_data.get("mecanico", "") in mecanicos_lista else 0)
        with col8:
            estado_opcoes = [
                "Entrada", "Em orçamento", "Aguardando aprovação", "Em reparação",
                "Concluido", "Não aprovado", "Entregado", "Entregado e cobrado"
            ]
            estado = st.selectbox("Estado", options=estado_opcoes, index=estado_opcoes.index(vendor_data.get("estado", "Entrada")))
    
        st.markdown("### 📆 Datas")
        col9, col10, col11 = st.columns(3)
        with col9:
            data_in = st.text_input("Data entrada", value=vendor_data.get("date_in", ""))
        with col10:
            date_prev = st.text_input("Previsão entrega", value=vendor_data.get("date_prev", ""))
        with col11:
            date_out = st.text_input("Data saída", value=vendor_data.get("date_out", ""))
    
        st.markdown("### 💼 Empresa")
        col12, col13, col14 = st.columns(3)
        with col12:
            dono_empresa = st.text_input("Dono da empresa", value=vendor_data.get("dono_empresa", ""))
        with col13:
            telefone = st.text_input("Telefone", value=vendor_data.get("telefone", ""))
        with col14:
            endereco = st.text_input("Endereço", value=vendor_data.get("endereco", ""))
    
        st.markdown("### 🚜 Serviços")
        servicos = []
        for i in range(1, 13):
            colA, colB = st.columns([7.2, 2.2])
            with colA:
                desc = st.text_input(
                    f"Serviço {i}",
                    value=vendor_data.get(f"desc_ser_{i}", ""),
                    key=f"desc_ser_{i}"
                )
            with colB:
                try:
                    raw_value = vendor_data[f"valor_serv_{i}"]
                    default_value = float(raw_value) if raw_value is not None and raw_value != "" else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0
        
                valor = st.number_input(
                     f"Valor {i}",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key=f"valor_serv_{i}_edit"
                )

            servicos.append((desc, valor))

        st.markdown("### 🛁 Peças")
        pecas = []
        porcentaje_adicional = st.number_input("% adicional", value=float(vendor_data.get("porcentaje_adicional", 35)))
        for i in range(1, 17):
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            with col1:
                quant = st.text_input("Qtd", value=vendor_data.get(f"quant_peca_{i}", ""), key=f"quant_peca_{i}_edit")
            with col2:
                desc = st.text_input("Descrição", value=vendor_data.get(f"desc_peca_{i}", ""), key=f"desc_peca_{i}_edit")
            with col3:
                try:
                    raw_valor = vendor_data.get(f"valor_peca_{i}", "")
                    default_valor = float(raw_valor) if raw_valor not in ["", None] else 0.0
                except:
                    default_valor = 0.0
        
                valor = st.number_input("Valor unit", value=default_valor, key=f"valor_peca_{i}_edit")
            with col4:
                try:
                    subtotal = float(quant) * valor if quant else 0.0
                    total = subtotal * (1 + porcentaje_adicional / 100)
                except:
                    subtotal = total = 0.0
        
            pecas.append((quant, desc, valor, subtotal, total))

    
        submitted = st.form_submit_button("Salvar alterações")
    
    if submitted:
        try:
            user_id = st.session_state.usuario
            atualizacao = {
                "placa": placa,
                "carro": carro,
                "modelo": modelo,
                "cor": cor,
                "ano": ano,
                "km": km,
                "mecanico": mecanico,
                "estado": estado,
                "date_in": data_in,
                "date_prev": date_prev,
                "date_out": date_out,
                "dono_empresa": dono_empresa,
                "telefone": telefone,
                "endereco": endereco,
                "porcentaje_adicional": porcentaje_adicional,
                "ultima_alteracao": firestore.SERVER_TIMESTAMP
            }
    
            for i, (desc, valor) in enumerate(servicos, start=1):
                atualizacao[f"desc_ser_{i}"] = desc
                atualizacao[f"valor_serv_{i}"] = valor
    
            for i, (qtd, desc, valor_unit, subtotal, total) in enumerate(pecas, start=1):
                atualizacao[f"quant_peca_{i}"] = qtd
                atualizacao[f"desc_peca_{i}"] = desc
                atualizacao[f"valor_peca_{i}"] = valor_unit
                atualizacao[f"sub_tota_peca_{i}"] = subtotal
                atualizacao[f"valor_total_peca_{i}"] = total
    
            db.collection("usuarios").document(user_id).collection("ordens_servico").document(vendor_to_update).update(atualizacao)
            st.success("Ordem atualizada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao atualizar Firebase: {e}")

#===================================================================================================================================================================
# --- Nueva Opción 3: Ver todas las órdenes ---
elif action == "Ver todos as ordens de serviço":
    st.header("📋 Lista completa de órdenes de servicio")
    
    # Mostrar el DataFrame con mejor formato
    st.dataframe(
        existing_data,
        use_container_width=True,  # Ajusta el ancho al contenedor
        hide_index=True,            # Oculta el índice numérico
        column_config={            # Personaliza columnas (opcional)
            "date_in": "Data de entrada",
            "placa": "Placa",
            "user_id": "N° Ordem"
        }
    )
    
    # Opción para exportar a CSV (opcional)
    if st.button("Exportar para CSV"):
        csv = existing_data.to_csv(index=False)
        st.download_button(
            label="Baixar arquivo",
            data=csv,
            file_name="ordens_de_servico.csv",
            mime="text/csv"
        )
#===================================================================================================================================================================
elif action == "Apagar ordem de serviço":
    st.header("🗑️ Apagar Ordem de Serviço")
    
    # 1. Selección por ID/Placa (tu código existente)
    search_option = st.radio("Buscar por:", ["ID", "Placa"], horizontal=True)
    
    if search_option == "ID":
        user_id_to_delete = st.selectbox(
            "Selecione o ID da ordem para apagar",
            options=existing_data["user_id"].astype(int).tolist()
        )
    else:
        placa_to_delete = st.selectbox(
            "Selecione a placa para apagar",
            options=existing_data["placa"].unique().tolist()
        )
        user_id_to_delete = existing_data[existing_data["placa"] == placa_to_delete]["user_id"].values[0]
    
    # 2. Mostrar detalles
    st.markdown("**Detalhes da ordem selecionada:**")
    ordem_to_delete = existing_data[existing_data["user_id"] == user_id_to_delete].iloc[0]
    st.json(ordem_to_delete.to_dict())
    
    # 3. Doble confirmación (FUNCIONA CORRECTAMENTE)
    st.warning("⚠️ Esta ação não pode ser desfeita!")
    
    # Usamos session_state para rastrear el checkbox
    if 'confirmado' not in st.session_state:
        st.session_state.confirmado = False
    
    # Checkbox que actualiza session_state
    confirmado = st.checkbox(
        "✅ Marque esta caixa para confirmar a exclusão",
        value=st.session_state.confirmado,
        key='confirm_checkbox'
    )
    
    # Actualizamos el estado cuando cambia el checkbox
    if confirmado != st.session_state.confirmado:
        st.session_state.confirmado = confirmado
        st.rerun()  # Fuerza la actualización
    
    # Botón que depende del estado
    if st.button(
        "CONFIRMAR EXCLUSÃO",
        type="primary",
        disabled=not st.session_state.confirmado
    ):
        # 4. Código de eliminación
        existing_data = existing_data[existing_data["user_id"] != user_id_to_delete]
        existing_data.reset_index(drop=True, inplace=True)
        
        try:
            #worksheet = inicializar_hoja()
            # Limpiar la hoja antes de actualizar
            worksheet.clear()
        
            # Escribir encabezados y datos
            worksheet.append_row(existing_data.columns.tolist())  # encabezados
            worksheet.append_rows(existing_data.values.tolist())  # datos
        
            st.success("Ordem apagada com sucesso!")
            st.session_state.confirmado = False  # Resetear estado
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao atualizar planilha: {str(e)}")
    
    # 5. Mostrar datos actualizados
    st.markdown("### Ordens restantes:")
    st.dataframe(existing_data, hide_index=True, use_container_width=True)
