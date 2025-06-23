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
def cargar_mecanicos():
    #ws_mecanicos = gc.open_by_key(SPREADSHEET_KEY).worksheet("Mecanicos")
    nombres = ws_mecanicos.col_values(1)[1:]  # Ignorar header
    return [n.strip() for n in nombres if n.strip()]

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

if action == "Nova ordem de serviço":
    #st.markdown("Insira os detalhes da nova ordem de serviço")
    with st.form(key="ordem"):
        centrar_texto("Dados do carro", 2, "yellow")
        with st.container():    
            col00, col01, col02, col03, col04 = st.columns(5)
            with col00:
                placa_input = st.text_input("Placa").strip().upper()
                # Formatar para garantir que apenas letras fiquem em maiúsculas
                placa = ''.join([char.upper() if char.isalpha() else char for char in placa_input])
            with col02:
                data_entrada = st.text_input("Data de entrada")
            with col03:
                previsao_entrega = st.text_input("Previsão de entrega")
            with col04:
                data_saida= st.text_input("Data de saida")
            
                
        with st.container():    
            col10, col11, col12, col13, col14 = st.columns(5)
            with col10:
                carro = st.text_input("Marca")
            with col11:
                modelo = st.text_input("Modelo")
            with col12:
                ano = st.text_input("Ano")
            with col13:
                cor = st.text_input("Cor")
            with col14:
                km = st.text_input("Km")

        # Opciones para el desplegable
        opciones_estado = [
            "Entrada",
            "Em orçamento",
            "Aguardando aprovação",
            "Em reparação",
            "Concluido",
            "Não aprovado",
            "Entregado",
            "Entregado e cobrado"
        ]
        
        with st.container():    
            col20, col21, col22, col23 = st.columns(4)
            with col20:
                estado = st.selectbox("Estado do serviço", opciones_estado)
            with col23:
                mecanicos_lista = cargar_mecanicos()
                mecanico = st.selectbox("Mecânico responsável", options=mecanicos_lista)


        with st.container():    
            col30, col31, col32 = st.columns(3)
            with col30:
                dono_empresa = st.text_input("Dono / Empresa")
            with col31:
                telefone = st.text_input("Telefone")
            with col32:
                endereco = st.text_input("Endereço")

        line(4, "blue")
        centrar_texto("Serviços", 2, "yellow")

        # ENCABEZADOS
        with st.container():
            col1101, col1102, col1103 = st.columns([0.7, 6.5, 2.2])
            with col1101:
                gold_text("#", align="center")
            with col1102:
                gold_text("Descrição do serviço")
            with col1103:
                gold_text("Valor do serviço")


        with st.container():    
            col40, col41, col42 = st.columns([0.7, 6.5, 2.2])
            with col40:
                item_serv_1 = 1
                gold_text("1", align="center")
            with col41:
                desc_ser_1 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_1")
            with col42:
                valor_serv_1 = st.number_input(" ", value=None, label_visibility="collapsed", key="valor_serv_1")
                
        with st.container():    
            col50, col51, col52 = st.columns([0.7, 6.5, 2.2])
            with col50:
                item_serv_2 = 2
                gold_text("2", align="center")
            with col51:
                desc_ser_2 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_2")
            with col52:
                valor_serv_2 = st.number_input(" ", value=None, label_visibility="collapsed", key="valor_serv_2")

        with st.container():    
            col60, col61, col62 = st.columns([0.7, 6.5, 2.2])
            with col60:
                item_serv_3 = 3
                gold_text("3", align="center")
            with col61:
                desc_ser_3 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_3")
            with col62:
                valor_serv_3 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_3")

        with st.container():    
            col70, col71, col72 = st.columns([0.7, 6.5, 2.2])
            with col70:
                item_serv_4 = 4
                gold_text("4", align="center")
            with col71:
                desc_ser_4 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_4")
            with col72:
                valor_serv_4 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_4")
                
        with st.container():    
            col80, col81, col82 = st.columns([0.7, 6.5, 2.2])
            with col80:
                item_serv_5 = 5
                gold_text("5", align="center")
            with col81:
                desc_ser_5 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_5")
            with col82:
                valor_serv_5 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_5")
        
        with st.container():    
            col90, col91, col92 = st.columns([0.7, 6.5, 2.2])
            with col90:
                item_serv_6 = 6
                gold_text("6", align="center")
            with col91:
                desc_ser_6 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_6")
            with col92:
                valor_serv_6 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_6")
        
        with st.container():    
            col100, col101, col102 = st.columns([0.7, 6.5, 2.2])
            with col100:
                item_serv_7 = 7
                gold_text("7", align="center")
            with col101:
                desc_ser_7 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_7")
            with col102:
                valor_serv_7 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_7")
        
        with st.container():    
            col110, col111, col112 = st.columns([0.7, 6.5, 2.2])
            with col110:
                item_serv_8 = 8
                gold_text("8", align="center")
            with col111:
                desc_ser_8 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_8")
            with col112:
                valor_serv_8 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_8")
        
        with st.container():    
            col120, col121, col122 = st.columns([0.7, 6.5, 2.2])
            with col120:
                item_serv_9 = 9
                gold_text("9", align="center")
            with col121:
                desc_ser_9 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_9")
            with col122:
                valor_serv_9 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_9")
        
        with st.container():    
            col130, col131, col132 = st.columns([0.7, 6.5, 2.2])
            with col130:
                item_serv_10 = 10
                gold_text("10", align="center")
            with col131:
                desc_ser_10 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_10")
            with col132:
                valor_serv_10 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_10")
        
        with st.container():    
            col140, col141, col142 = st.columns([0.7, 6.5, 2.2])
            with col140:
                item_serv_11 = 11
                gold_text("11", align="center")
            with col141:
                desc_ser_11 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_11")
            with col142:
                valor_serv_11 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_11")
        
        with st.container():    
            col150, col151, col152 = st.columns([0.7, 6.5, 2.2])
            with col150:
                item_serv_12 = 12
                gold_text("12", align="center")
            with col151:
                desc_ser_12 = st.text_input("", "", label_visibility="collapsed", key="desc_ser_12")
            with col152:
                valor_serv_12 = st.text_input(" ", value=None, label_visibility="collapsed", key="valor_serv_12")
                
        line(4, "blue")
        centrar_texto("Peças", 2, "yellow")
        
        with st.container():
            col_perc, col_empty, col_final = st.columns([4, 2.5, 4])
            with col_empty:
                porcentaje_adicional = st.number_input(
                    "Porcentagem adicional (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=35.0,  # Valor por defecto del 30%
                    step=0.5,
                    key="porcentaje_adicional"
                )
        # ENCABEZADOS
        with st.container():
            col1001, col1002, col1003, col1004, col1005, col1006 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col1001:
                gold_text("#")
            with col1002:
                gold_text("Quant.")
            with col1003:
                gold_text("Descrição da peça")
            with col1004:
                gold_text("Valor Unit")
            with col1005:
                gold_text("Sub Total")
            with col1006:
                gold_text("Total")
        
                        
        with st.container():  
            col160, col161, col162, col163, col164, col165 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col160:
                gold_text("1")     
            with col161:
                quant_peca_1 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_1")
            with col162:
                desc_peca_1 = st.text_input("", " ", label_visibility="collapsed", key="desc_peca_1")
            with col163:
                valor_peca_1 = st.number_input(" ", value=None, label_visibility="collapsed", key="valor_peca_1")
            with col164: 
                if quant_peca_1 and valor_peca_1:
                    try:
                        costo_inicial_1 = float(quant_peca_1) * float(valor_peca_1)
                        gold_text(f"R$ {costo_inicial_1:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col165:
                # Mostrar costo final (con porcentaje aplicado)
                if quant_peca_1 and valor_peca_1 and porcentaje_adicional:
                    try:
                        costo_final_1 = float(quant_peca_1) * float(valor_peca_1) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_1:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")   


        with st.container():
            col170, col171, col172, col173, col174, col175 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col170:
                gold_text("2")     
            with col171:
                quant_peca_2 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_2")
            with col172:
                desc_peca_2 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_2")
            with col173:
                valor_peca_2 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_2")
            with col174: 
                if quant_peca_2 and valor_peca_2:
                    try:
                        costo_inicial_2 = float(quant_peca_2) * float(valor_peca_2)
                        gold_text(f"R$ {costo_inicial_2:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col175:
                # Mostrar costo final (con porcentaje aplicado)
                if quant_peca_2 and valor_peca_2 and porcentaje_adicional:
                    try:
                        costo_final_2 = float(quant_peca_2) * float(valor_peca_2) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_2:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")                

        with st.container():
            col180, col181, col182, col183, col184, col185 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col180:
                gold_text("3")     
            with col181:
                quant_peca_3 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_3")
            with col182:
                desc_peca_3 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_3")
            with col183:
                valor_peca_3 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_3")
            with col184: 
                if quant_peca_3 and valor_peca_3:
                    try:
                        costo_inicial_3 = float(quant_peca_3) * float(valor_peca_3)
                        gold_text(f"R$ {costo_inicial_3:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col185:
                if quant_peca_3 and valor_peca_3 and porcentaje_adicional:
                    try:
                        costo_final_3 = float(quant_peca_3) * float(valor_peca_3) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_3:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
        
        with st.container():
            col190, col191, col192, col193, col194, col195 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col190:
                gold_text("4")     
            with col191:
                quant_peca_4 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_4")
            with col192:
                desc_peca_4 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_4")
            with col193:
                valor_peca_4 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_4")
            with col194: 
                if quant_peca_4 and valor_peca_4:
                    try:
                        costo_inicial_4 = float(quant_peca_4) * float(valor_peca_4)
                        gold_text(f"R$ {costo_inicial_4:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col195:
                if quant_peca_4 and valor_peca_4 and porcentaje_adicional:
                    try:
                        costo_final_4 = float(quant_peca_4) * float(valor_peca_4) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_4:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col200, col201, col202, col203, col204, col205 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col200:
                gold_text("5")     
            with col201:
                quant_peca_5 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_5")
            with col202:
                desc_peca_5 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_5")
            with col203:
                valor_peca_5 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_5")
            with col204: 
                if quant_peca_5 and valor_peca_5:
                    try:
                        costo_inicial_5 = float(quant_peca_5) * float(valor_peca_5)
                        gold_text(f"R$ {costo_inicial_5:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col205:
                if quant_peca_5 and valor_peca_5 and porcentaje_adicional:
                    try:
                        costo_final_5 = float(quant_peca_5) * float(valor_peca_5) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_5:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col210, col211, col212, col213, col214, col215 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col210:
                gold_text("6")     
            with col211:
                quant_peca_6 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_6")
            with col212:
                desc_peca_6 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_6")
            with col213:
                valor_peca_6 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_6")
            with col214: 
                if quant_peca_6 and valor_peca_6:
                    try:
                        costo_inicial_6 = float(quant_peca_6) * float(valor_peca_6)
                        gold_text(f"R$ {costo_inicial_6:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col215:
                if quant_peca_6 and valor_peca_6 and porcentaje_adicional:
                    try:
                        costo_final_6 = float(quant_peca_6) * float(valor_peca_6) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_6:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col220, col221, col222, col223, col224, col225 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col220:
                gold_text("7")     
            with col221:
                quant_peca_7 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_7")
            with col222:
                desc_peca_7 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_7")
            with col223:
                valor_peca_7 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_7")
            with col224: 
                if quant_peca_7 and valor_peca_7:
                    try:
                        costo_inicial_7 = float(quant_peca_7) * float(valor_peca_7)
                        gold_text(f"R$ {costo_inicial_7:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col225:
                if quant_peca_7 and valor_peca_7 and porcentaje_adicional:
                    try:
                        costo_final_7 = float(quant_peca_7) * float(valor_peca_7) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_7:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col230, col231, col232, col233, col234, col235 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col230:
                gold_text("8")     
            with col231:
                quant_peca_8 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_8")
            with col232:
                desc_peca_8 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_8")
            with col233:
                valor_peca_8 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_8")
            with col234: 
                if quant_peca_8 and valor_peca_8:
                    try:
                        costo_inicial_8 = float(quant_peca_8) * float(valor_peca_8)
                        gold_text(f"R$ {costo_inicial_8:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col235:
                if quant_peca_8 and valor_peca_8 and porcentaje_adicional:
                    try:
                        costo_final_8 = float(quant_peca_8) * float(valor_peca_8) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_8:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col240, col241, col242, col243, col244, col245 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col240:
                gold_text("9")     
            with col241:
                quant_peca_9 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_9")
            with col242:
                desc_peca_9 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_9")
            with col243:
                valor_peca_9 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_9")
            with col244: 
                if quant_peca_9 and valor_peca_9:
                    try:
                        costo_inicial_9 = float(quant_peca_9) * float(valor_peca_9)
                        gold_text(f"R$ {costo_inicial_9:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col245:
                if quant_peca_9 and valor_peca_9 and porcentaje_adicional:
                    try:
                        costo_final_9 = float(quant_peca_9) * float(valor_peca_9) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_9:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")


        with st.container():
            col250, col251, col252, col253, col254, col255 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col250:
                gold_text("10")     
            with col251:
                quant_peca_10 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_10")
            with col252:
                desc_peca_10 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_10")
            with col253:
                valor_peca_10 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_10")
            with col254: 
                if quant_peca_10 and valor_peca_10:
                    try:
                        costo_inicial_10 = float(quant_peca_10) * float(valor_peca_10)
                        gold_text(f"R$ {costo_inicial_10:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col255:
                if quant_peca_10 and valor_peca_10 and porcentaje_adicional:
                    try:
                        costo_final_10 = float(quant_peca_10) * float(valor_peca_10) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_10:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col260, col261, col262, col263, col264, col265 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col260:
                gold_text("11")     
            with col261:
                quant_peca_11 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_11")
            with col262:
                desc_peca_11 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_11")
            with col263:
                valor_peca_11 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_11")
            with col264: 
                if quant_peca_11 and valor_peca_11:
                    try:
                        costo_inicial_11 = float(quant_peca_11) * float(valor_peca_11)
                        gold_text(f"R$ {costo_inicial_11:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col265:
                if quant_peca_11 and valor_peca_11 and porcentaje_adicional:
                    try:
                        costo_final_11 = float(quant_peca_11) * float(valor_peca_11) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_11:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")


        with st.container():
            col270, col271, col272, col273, col274, col275 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col270:
                gold_text("12")     
            with col271:
                quant_peca_12 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_12")
            with col272:
                desc_peca_12 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_12")
            with col273:
                valor_peca_12 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_12")
            with col274: 
                if quant_peca_12 and valor_peca_12:
                    try:
                        costo_inicial_12 = float(quant_peca_12) * float(valor_peca_12)
                        gold_text(f"R$ {costo_inicial_12:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col275:
                if quant_peca_12 and valor_peca_12 and porcentaje_adicional:
                    try:
                        costo_final_12 = float(quant_peca_12) * float(valor_peca_12) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_12:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")


        with st.container():
            col280, col281, col282, col283, col284, col285 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col280:
                gold_text("13")     
            with col281:
                quant_peca_13 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_13")
            with col282:
                desc_peca_13 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_13")
            with col283:
                valor_peca_13 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_13")
            with col284: 
                if quant_peca_13 and valor_peca_13:
                    try:
                        costo_inicial_13 = float(quant_peca_13) * float(valor_peca_13)
                        gold_text(f"R$ {costo_inicial_13:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col285:
                if quant_peca_13 and valor_peca_13 and porcentaje_adicional:
                    try:
                        costo_final_13 = float(quant_peca_13) * float(valor_peca_13) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_13:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")


        with st.container():
            col290, col291, col292, col293, col294, col295 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col290:
                gold_text("14")     
            with col291:
                quant_peca_14 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_14")
            with col292:
                desc_peca_14 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_14")
            with col293:
                valor_peca_14 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_14")
            with col294: 
                if quant_peca_14 and valor_peca_14:
                    try:
                        costo_inicial_14 = float(quant_peca_14) * float(valor_peca_14)
                        gold_text(f"R$ {costo_inicial_14:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col295:
                if quant_peca_14 and valor_peca_14 and porcentaje_adicional:
                    try:
                        costo_final_14 = float(quant_peca_14) * float(valor_peca_14) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_14:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            col300, col301, col302, col303, col304, col305 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col300:
                gold_text("15")     
            with col301:
                quant_peca_15 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_15")
            with col302:
                desc_peca_15 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_15")
            with col303:
                valor_peca_15 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_15")
            with col304: 
                if quant_peca_15 and valor_peca_15:
                    try:
                        costo_inicial_15 = float(quant_peca_15) * float(valor_peca_15)
                        gold_text(f"R$ {costo_inicial_15:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with col305:
                if quant_peca_15 and valor_peca_15 and porcentaje_adicional:
                    try:
                        costo_final_15 = float(quant_peca_15) * float(valor_peca_15) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_15:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")

        with st.container():
            coll310, coll311, coll312, coll313, col304, coll315 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with coll310:
                gold_text("16")     
            with coll311:
                quant_peca_16 = st.text_input("", "1", label_visibility="collapsed", key="quant_peca_16")
            with coll312:
                desc_peca_16 = st.text_input("", "", label_visibility="collapsed", key="desc_peca_16")
            with coll313:
                valor_peca_16 = st.number_input("", value=None, label_visibility="collapsed", key="valor_peca_16")
            with col304: 
                if quant_peca_16 and valor_peca_16:
                    try:
                        costo_inicial_16 = float(quant_peca_16) * float(valor_peca_16)
                        gold_text(f"R$ {costo_inicial_16:.2f}")
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
            with coll315:
                if quant_peca_16 and valor_peca_16 and porcentaje_adicional:
                    try:
                        costo_final_16 = float(quant_peca_16) * float(valor_peca_16) * (1 + porcentaje_adicional/100)
                        gold_text(f"R$ {costo_final_16:.2f}")        
                    except:
                        gold_text("R$ 0.00")
                else:
                    gold_text("R$ 0.00")
        
        line(4, "blue")
        
        # Asegurar que el DataFrame existente tenga todas las columnas en el orden correcto
        existing_data = existing_data.reindex(columns=columnas_ordenadas)
     
        with st.container():
            col320, col321, col322, col323, col324 = st.columns([1.2, 1.2, 1, 1, 1])
            with col322:
                submit_button = st.form_submit_button("Enviar")
            if submit_button:
                # Crear un nuevo registro con los datos del formulario
                new_record = {
                    'user_id': obtener_proximo_id(existing_data),
                    'date_in': data_entrada,
                    'date_prev': previsao_entrega,
                    'date_out': data_saida,
                    'carro': carro,
                    'modelo': modelo,
                    'cor': cor,
                    'placa': placa,
                    'km': km,
                    'ano': ano,
                    'estado': estado,
                    'mecanico': mecanico,
                    'dono_empresa': dono_empresa,
                    'telefone': telefone,
                    'endereco': endereco,
                    'item_serv_1': item_serv_1 if 'item_serv_1' in locals() else None,
                    'desc_ser_1': desc_ser_1 if 'desc_ser_1' in locals() else None,
                    'valor_serv_1': valor_serv_1 if 'valor_serv_1' in locals() else None,
                    'item_serv_2': item_serv_2 if 'item_serv_2' in locals() else None,
                    'desc_ser_2': desc_ser_2 if 'desc_ser_2' in locals() else None,
                    'valor_serv_2': valor_serv_2 if 'valor_serv_2' in locals() else None,
                    'item_serv_3': item_serv_3 if 'item_serv_3' in locals() else None,
                    'desc_ser_3': desc_ser_3 if 'desc_ser_3' in locals() else None,
                    'valor_serv_3': valor_serv_3 if 'valor_serv_3' in locals() else None,
                    'item_serv_4': item_serv_4 if 'item_serv_4' in locals() else None,
                    'desc_ser_4': desc_ser_4 if 'desc_ser_4' in locals() else None,
                    'valor_serv_4': valor_serv_4 if 'valor_serv_4' in locals() else None,
                    'item_serv_5': item_serv_5 if 'item_serv_5' in locals() else None,
                    'desc_ser_5': desc_ser_5 if 'desc_ser_5' in locals() else None,
                    'valor_serv_5': valor_serv_5 if 'valor_serv_5' in locals() else None,
                    'item_serv_6': item_serv_6 if 'item_serv_6' in locals() else None,
                    'desc_ser_6': desc_ser_6 if 'desc_ser_6' in locals() else None,
                    'valor_serv_6': valor_serv_6 if 'valor_serv_6' in locals() else None,
                    'item_serv_7': item_serv_7 if 'item_serv_7' in locals() else None,
                    'desc_ser_7': desc_ser_7 if 'desc_ser_7' in locals() else None,
                    'valor_serv_7': valor_serv_7 if 'valor_serv_7' in locals() else None,
                    'item_serv_8': item_serv_8 if 'item_serv_8' in locals() else None,
                    'desc_ser_8': desc_ser_8 if 'desc_ser_8' in locals() else None,
                    'valor_serv_8': valor_serv_8 if 'valor_serv_8' in locals() else None,
                    'item_serv_9': item_serv_9 if 'item_serv_9' in locals() else None,
                    'desc_ser_9': desc_ser_9 if 'desc_ser_9' in locals() else None,
                    'valor_serv_9': valor_serv_9 if 'valor_serv_9' in locals() else None,
                    'item_serv_10': item_serv_10 if 'item_serv_10' in locals() else None,
                    'desc_ser_10': desc_ser_10 if 'desc_ser_10' in locals() else None,
                    'valor_serv_10': valor_serv_10 if 'valor_serv_10' in locals() else None,
                    'item_serv_11': item_serv_11 if 'item_serv_11' in locals() else None,
                    'desc_ser_11': desc_ser_11 if 'desc_ser_11' in locals() else None,
                    'valor_serv_11': valor_serv_11 if 'valor_serv_11' in locals() else None,
                    'item_serv_12': item_serv_12 if 'item_serv_12' in locals() else None,
                    'desc_ser_12': desc_ser_12 if 'desc_ser_12' in locals() else None,
                    'valor_serv_12': valor_serv_12 if 'valor_serv_12' in locals() else None,
                    'total_serviço': None,
                    'porcentaje_adicional': porcentaje_adicional,
                    'quant_peca_1': quant_peca_1 if 'quant_peca_1' in locals() else None,
                    'desc_peca_1': desc_peca_1 if 'desc_peca_1' in locals() else None,
                    'valor_peca_1': valor_peca_1 if 'valor_peca_1' in locals() else None,
                    'sub_tota_peca_1': costo_inicial_1 if 'costo_inicial_1' in locals() else 0,
                    'valor_total_peca_1': costo_final_1 if 'costo_final_1' in locals() else 0,             
                    'quant_peca_2': quant_peca_2 if 'quant_peca_2' in locals() else None,
                    'desc_peca_2': desc_peca_2 if 'desc_peca_2' in locals() else None,
                    'valor_peca_2': valor_peca_2 if 'valor_peca_2' in locals() else None,
                    'sub_tota_peca_2': costo_inicial_2 if 'costo_inicial_2' in locals() else 0,
                    'valor_total_peca_2': costo_final_2 if 'costo_final_2' in locals() else 0,                   
                    'quant_peca_3': quant_peca_3 if 'quant_peca_3' in locals() else None,
                    'desc_peca_3': desc_peca_3 if 'desc_peca_3' in locals() else None,
                    'valor_peca_3': valor_peca_3 if 'valor_peca_3' in locals() else None,
                    'sub_tota_peca_3': costo_inicial_3 if 'costo_inicial_3' in locals() else 0,
                    'valor_total_peca_3': costo_final_3 if 'costo_final_3' in locals() else 0,                   
                    'quant_peca_4': quant_peca_4 if 'quant_peca_4' in locals() else None,
                    'desc_peca_4': desc_peca_4 if 'desc_peca_4' in locals() else None,
                    'valor_peca_4': valor_peca_4 if 'valor_peca_4' in locals() else None,
                    'sub_tota_peca_4': costo_inicial_4 if 'costo_inicial_4' in locals() else 0,
                    'valor_total_peca_4': costo_final_4 if 'costo_final_4' in locals() else 0,                    
                    'quant_peca_5': quant_peca_5 if 'quant_peca_5' in locals() else None,
                    'desc_peca_5': desc_peca_5 if 'desc_peca_5' in locals() else None,
                    'valor_peca_5': valor_peca_5 if 'valor_peca_5' in locals() else None,
                    'sub_tota_peca_5': costo_inicial_5 if 'costo_inicial_5' in locals() else 0,
                    'valor_total_peca_5': costo_final_5 if 'costo_final_5' in locals() else 0,                    
                    'quant_peca_6': quant_peca_6 if 'quant_peca_6' in locals() else None,
                    'desc_peca_6': desc_peca_6 if 'desc_peca_6' in locals() else None,
                    'valor_peca_6': valor_peca_6 if 'valor_peca_6' in locals() else None,
                    'sub_tota_peca_6': costo_inicial_6 if 'costo_inicial_6' in locals() else 0,
                    'valor_total_peca_6': costo_final_6 if 'costo_final_6' in locals() else 0,                  
                    'quant_peca_7': quant_peca_7 if 'quant_peca_7' in locals() else None,
                    'desc_peca_7': desc_peca_7 if 'desc_peca_7' in locals() else None,
                    'valor_peca_7': valor_peca_7 if 'valor_peca_7' in locals() else None,
                    'sub_tota_peca_7': costo_inicial_7 if 'costo_inicial_7' in locals() else 0,
                    'valor_total_peca_7': costo_final_7 if 'costo_final_7' in locals() else 0,                      
                    'quant_peca_8': quant_peca_8 if 'quant_peca_8' in locals() else None,
                    'desc_peca_8': desc_peca_8 if 'desc_peca_8' in locals() else None,
                    'valor_peca_8': valor_peca_8 if 'valor_peca_8' in locals() else None,
                    'sub_tota_peca_8': costo_inicial_8 if 'costo_inicial_8' in locals() else 0,
                    'valor_total_peca_8': costo_final_8 if 'costo_final_8' in locals() else 0,                      
                    'quant_peca_9': quant_peca_9 if 'quant_peca_9' in locals() else None,
                    'desc_peca_9': desc_peca_9 if 'desc_peca_9' in locals() else None,
                    'valor_peca_9': valor_peca_9 if 'valor_peca_9' in locals() else None,
                    'sub_tota_peca_9': costo_inicial_9 if 'costo_inicial_9' in locals() else 0,
                    'valor_total_peca_9': costo_final_9 if 'costo_final_9' in locals() else 0,                     
                    'quant_peca_10': quant_peca_10 if 'quant_peca_10' in locals() else None,
                    'desc_peca_10': desc_peca_10 if 'desc_peca_10' in locals() else None,
                    'valor_peca_10': valor_peca_10 if 'valor_peca_10' in locals() else None,
                    'sub_tota_peca_10': costo_inicial_10 if 'costo_inicial_10' in locals() else 0,
                    'valor_total_peca_10': costo_final_10 if 'costo_final_10' in locals() else 0,   
                    'quant_peca_11': quant_peca_11 if 'quant_peca_11' in locals() else None,
                    'desc_peca_11': desc_peca_11 if 'desc_peca_11' in locals() else None,
                    'valor_peca_11': valor_peca_11 if 'valor_peca_11' in locals() else None,
                    'sub_tota_peca_11': costo_inicial_11 if 'costo_inicial_11' in locals() else 0,
                    'valor_total_peca_11': costo_final_11 if 'costo_final_11' in locals() else 0,                      
                    'quant_peca_12': quant_peca_12 if 'quant_peca_12' in locals() else None,
                    'desc_peca_12': desc_peca_12 if 'desc_peca_12' in locals() else None,
                    'valor_peca_12': valor_peca_12 if 'valor_peca_12' in locals() else None,
                    'sub_tota_peca_12': costo_inicial_12 if 'costo_inicial_12' in locals() else 0,
                    'valor_total_peca_12': costo_final_12 if 'costo_final_12' in locals() else 0,                      
                    'quant_peca_13': quant_peca_13 if 'quant_peca_13' in locals() else None,
                    'desc_peca_13': desc_peca_13 if 'desc_peca_13' in locals() else None,
                    'valor_peca_13': valor_peca_13 if 'valor_peca_13' in locals() else None,
                    'sub_tota_peca_13': costo_inicial_13 if 'costo_inicial_13' in locals() else 0,
                    'valor_total_peca_13': costo_final_13 if 'costo_final_13' in locals() else 0,                    
                    'quant_peca_14': quant_peca_14 if 'quant_peca_14' in locals() else None,
                    'desc_peca_14': desc_peca_14 if 'desc_peca_14' in locals() else None,
                    'valor_peca_14': valor_peca_14 if 'valor_peca_14' in locals() else None,
                    'sub_tota_peca_14': costo_inicial_14 if 'costo_inicial_14' in locals() else 0,
                    'valor_total_peca_14': costo_final_14 if 'costo_final_14' in locals() else 0,                     
                    'quant_peca_15': quant_peca_15 if 'quant_peca_15' in locals() else None,
                    'desc_peca_15': desc_peca_15 if 'desc_peca_15' in locals() else None,
                    'valor_peca_15': valor_peca_15 if 'valor_peca_15' in locals() else None,
                    'sub_tota_peca_15': costo_inicial_15 if 'costo_inicial_15' in locals() else 0,
                    'valor_total_peca_15': costo_final_15 if 'costo_final_15' in locals() else 0,                     
                    'quant_peca_16': quant_peca_16 if 'quant_peca_16' in locals() else None,
                    'desc_peca_16': desc_peca_16 if 'desc_peca_16' in locals() else None,
                    'valor_peca_16': valor_peca_16 if 'valor_peca_16' in locals() else None,
                    'sub_tota_peca_16': costo_inicial_16 if 'costo_inicial_16' in locals() else 0,
                    'valor_total_peca_15': costo_final_16 if 'costo_final_16' in locals() else 0,                      
                    'total_costo_inicial': sum([v for k, v in locals().items() if k.startswith('costo_inicial_')]),
                    'total_costo_final': sum([v for k, v in locals().items() if k.startswith('costo_final_')]),
                    'forma_de_pagamento': None,
                    'pagamento_parcial': None,
                    'valor_pago_parcial': None,
                    'data_prox_pag': None,
                    'valor_prox_pag': None,
                    'pag_total': None,
                    'valor_pag_total': None
                }
            
                # Convertir el nuevo registro a DataFrame
                new_record_df = pd.DataFrame([new_record])
            
                # Asegurar que el nuevo registro tenga todas las columnas en el orden correcto
                new_record_df = new_record_df.reindex(columns=columnas_ordenadas)
            
                # Reemplazar NaN con None en el nuevo registro
                new_record_df = replace_nan_with_none(new_record_df)
            
                try:
                    # Obtener la hoja de cálculo
                    #worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
                    
                    # Agregar el nuevo registro al final de la hoja
                    try:
                        user_id = st.session_state.usuario
                        ordens_ref = db.collection("usuarios").document(user_id).collection("ordens_servico")
                        nova_ordem_ref = ordens_ref.document()
                        nova_ordem_ref.set(new_record_df.to_dict(orient="records")[0])
                        st.success("Ordem de serviço adicionada com sucesso")
                    except Exception as e:
                        st.error(f"Erro ao salvar no Firebase: {e}")
                    
                    st.success("Ordem de serviço adicionada com sucesso")
                    
                    # Actualizar la variable existing_data con los datos actualizados
                    existing_data = pd.concat([existing_data, new_record_df], ignore_index=True)
            
                except Exception as e:
                    st.error(f"Erro ao atualizar planilha: {str(e)}")
            
            # Mostrar la tabla actualizada
            st.dataframe(existing_data, hide_index=True)

# ==============================================================================================================================================================


# Código para actualizar una orden de servicio
elif action == "Atualizar ordem existente":
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
                with col201:
                    placa_to_search = st.text_input("Digite o número da placa.").strip().upper()
                    if placa_to_search:
                        resultado = buscar_por_placa(placa_to_search, existing_data)
                        if resultado:
                            vendor_data = resultado
                            vendor_to_update = vendor_data["user_id"]
                        else:
                            with col202:
                                st.write("")  # Espaciador
                                st.warning("Nenhuma ordem de serviço encontrada com essa placa.")
                                st.stop()
                    else:
                        with col202:
                            st.write("")  # Espaciador
                            st.warning("Digite o número da placa para pesquisar e pressione Enter.")
                            st.stop()
            else:
                with col201:
                    vendor_to_update = st.selectbox("Selecione o ID", options=existing_data["user_id"].tolist())
                    vendor_data = existing_data[existing_data["user_id"] == vendor_to_update].iloc[0].to_dict()

                            
    #st.subheader("🧪 Diagnóstico de Google Sheets")

    # Mostrar IDs tal como los ve worksheet
    #id_col = worksheet.col_values(1)
    #st.write("📋 Columna A (user_id):", id_col)


    # Mostrar los campos del formulario con los valores actuales
    with st.form(key="update_form"):
        st.markdown("Atualize os detalhes da ordem de serviço")       
        with st.container():    
            col00, col01, col02, col03, col04 = st.columns(5)
            with col00:
                placa = st.text_input("Placa", value=vendor_data["placa"], key="update_placa", disabled=True) 
            with col02:
                data_entrada = st.text_input("Data de entrada", value=vendor_data["date_in"], key="update_data_entrada")
            with col03:
                previsao_entrega = st.text_input("Previsão de entrega", value=vendor_data["date_prev"], key="update_previsao_entrega")
            with col04:
                data_saida = st.text_input("Data de saida", value=vendor_data["date_out"], key="update_data_saida")
            
        with st.container():    
            col10, col11, col12, col13, col14 = st.columns(5)
            with col10:
                carro = st.text_input("Marca", value=vendor_data["carro"], key="update_carro")
            with col11:
                modelo = st.text_input("Modelo", value=vendor_data["modelo"], key="update_modelo")
            with col12:
                ano = st.text_input("Ano", value=vendor_data["ano"], key="update_ano")
            with col13:
                cor = st.text_input("Cor", value=vendor_data["cor"], key="update_cor")
            with col14:
                km = st.text_input("Km", value=vendor_data["km"], key="update_km")

        # Opciones para el desplegable
        opciones_estado = [
            "Entrada",
            "Em orçamento",
            "Aguardando aprovação",
            "Em reparação",
            "Concluido",
            "Não aprovado",
            "Entregado",
            "Entregado e cobrado"
        ]
        with st.container():    
            col20, col21, col22, col23 = st.columns(4)
        
            with col20:
                # Verificar si el estado actual está en opciones_estado
                estado_actual = vendor_data.get("estado", "")
                if estado_actual in opciones_estado:
                    index_estado = opciones_estado.index(estado_actual)
                else:
                    index_estado = 0
        
                estado = st.selectbox("Estado do serviço", opciones_estado, index=index_estado, key="update_estado")
        
            with col23:
                mecanicos_lista = [""] + cargar_mecanicos()
                mecanico_atual = vendor_data.get("mecanico", "").strip()
                index_mecanico = mecanicos_lista.index(mecanico_atual) if mecanico_atual in mecanicos_lista else 0
                
                mecanico = st.selectbox(
                    "Mecânico responsável", 
                    options=mecanicos_lista, 
                    index=index_mecanico, 
                    key="update_mecanico"
                )

        with st.container():    
            col30, col31, col32 = st.columns(3)
            with col30:
                dono_empresa = st.text_input("Dono / Empresa", value=vendor_data["dono_empresa"], key="update_dono_empresa")
            with col31:
                telefone = st.text_input("Telefone", value=vendor_data["telefone"], key="update_telefone")
            with col32:
                endereco = st.text_input("Endereço", value=vendor_data["endereco"], key="update_endereco")

        line(4, "blue")
        centrar_texto("Serviços", 2, "yellow")
        #=========================================================================================================

         # ENCABEZADOS
        with st.container():
            col1101, col1102, col1103 = st.columns([0.7, 6.5, 2.2])
            with col1101:
                gold_text("#", align="center")
            with col1102:
                gold_text("Descrição do serviço")
            with col1103:
                gold_text("Valor do serviço")

        with st.container():    
            col40, col41, col42 = st.columns([0.7, 6.5, 2.2])
            with col40:
                item_serv_1 = "1"
                gold_text("1")
            with col41:
                desc_ser_1 = st.text_input("", value=vendor_data["desc_ser_1"], label_visibility="collapsed", key="update_desc_ser_1")
            with col42:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_1"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_1 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_1"
                )
            
                
        with st.container():    
            col50, col51, col52 = st.columns([0.7, 6.5, 2.2])
            with col50:
                item_serv_2 = "2"
                gold_text("2")
            with col51:
                desc_ser_2 = st.text_input("", value=vendor_data["desc_ser_2"], label_visibility="collapsed", key="update_desc_ser_2")
            with col52:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_2"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_2 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_2"
                )

        with st.container():    
            col60, col61, col62 = st.columns([0.7, 6.5, 2.2])
            with col60:
                item_serv_3 = "3"
                gold_text("3")
            with col61:
                desc_ser_3 = st.text_input("", value=vendor_data["desc_ser_3"], label_visibility="collapsed", key="update_desc_ser_3")
            with col62:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_3"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_3 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_3"
                )

        with st.container():    
            col70, col71, col72 = st.columns([0.7, 6.5, 2.2])
            with col70:
                item_serv_4 = "4"
                gold_text("4")
            with col71:
                desc_ser_4 = st.text_input("", value=vendor_data["desc_ser_4"], label_visibility="collapsed", key="update_desc_ser_4")
            with col72:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_4"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_4 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_4"
                )

        with st.container():    
            col80, col81, col82 = st.columns([0.7, 6.5, 2.2])
            with col80:
                item_serv_5 = "5"
                gold_text("5")
            with col81:
                desc_ser_5 = st.text_input("", value=vendor_data["desc_ser_5"], label_visibility="collapsed", key="update_desc_ser_5")
            with col82:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_5"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_5 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_5"
                )
        
        with st.container():    
            col90, col91, col92 = st.columns([0.7, 6.5, 2.2])
            with col90:
                item_serv_6 = "6"
                gold_text("6")
            with col91:
                desc_ser_6 = st.text_input("", value=vendor_data["desc_ser_6"], label_visibility="collapsed", key="update_desc_ser_6")
            with col92:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_6"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_6 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_6"
                )
        
        with st.container():    
            col100, col101, col102 = st.columns([0.7, 6.5, 2.2])
            with col100:
                item_serv_7 = "7"
                gold_text("7")
            with col101:
                desc_ser_7 = st.text_input("", value=vendor_data["desc_ser_7"], label_visibility="collapsed", key="update_desc_ser_7")
            with col102:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_7"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_7 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_7"
                )
        
        with st.container():    
            col110, col111, col112 = st.columns([0.7, 6.5, 2.2])
            with col110:
                item_serv_8 = "8"
                gold_text("8")
            with col111:
                desc_ser_8 = st.text_input("", value=vendor_data["desc_ser_8"], label_visibility="collapsed", key="update_desc_ser_8")
            with col112:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_8"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_8 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_8"
                )
        
        with st.container():    
            col120, col121, col122 = st.columns([0.7, 6.5, 2.2])
            with col120:
                item_serv_9 = "9"
                gold_text("9")
            with col121:
                desc_ser_9 = st.text_input("", value=vendor_data["desc_ser_9"], label_visibility="collapsed", key="update_desc_ser_9")
            with col122:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_9"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_9 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_9"
                )
        
        with st.container():    
            col130, col131, col132 = st.columns([0.7, 6.5, 2.2])
            with col130:
                item_serv_10 = "10"
                gold_text("10")
            with col131:
                desc_ser_10 = st.text_input("", value=vendor_data["desc_ser_10"], label_visibility="collapsed", key="update_desc_ser_10")
            with col132:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_10"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_10 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_10"
                )
        
        with st.container():    
            col140, col141, col142 = st.columns([0.7, 6.5, 2.2])
            with col140:
                item_serv_11 = "11"
                gold_text("11")
            with col141:
                desc_ser_11 = st.text_input("", value=vendor_data["desc_ser_11"], label_visibility="collapsed", key="update_desc_ser_11")
            with col142:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_11"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_11 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_11"
                )
        
        with st.container():    
            col150, col151, col152 = st.columns([0.7, 6.5, 2.2])
            with col150:
                item_serv_12 = "12"
                gold_text("12")
            with col151:
                desc_ser_12 = st.text_input("", value=vendor_data["desc_ser_12"], label_visibility="collapsed", key="update_desc_ser_12")
            with col152:
                # Validación robusta del valor numérico
                try:
                    raw_value = vendor_data["valor_serv_12"]  # Acceso directo (puede fallar)
                    default_value = float(raw_value) if raw_value is not None else 0.0
                    default_value = max(0.0, min(default_value, 1000000.0))  # Aseguramos límites
                except (KeyError, TypeError, ValueError):
                    default_value = 0.0  # Valor por defecto si hay cualquier error
                
                valor_serv_12 = st.number_input(
                    "",
                    value=default_value,
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed",
                    key="update_valor_serv_12"
                )
                
        # En la sección "Atualizar ordem existente":
        line(4, "blue")
        centrar_texto("Peças", 2, "yellow")
        
        with st.container():
            col_perc, col_empty, col_final = st.columns([4, 2.5, 4])
            with col_empty:
                # 1. Obtener el valor de la base de datos
                porcentaje_guardado = vendor_data.get("porcentaje_adicional")
                
                # 2. Conversión ultra-segura (maneja todos los casos)
                try:
                    if porcentaje_guardado is None or str(porcentaje_guardado).strip() == "":
                        porcentaje_default = 35.0  # Valor por defecto actualizado a 35%
                    else:
                        # Convierte tanto "35,5" como "35.5" correctamente
                        if isinstance(porcentaje_guardado, str):
                            porcentaje_default = float(porcentaje_guardado.replace(",", "."))
                        else:
                            porcentaje_default = float(porcentaje_guardado)
                except:
                    porcentaje_default = 35.0
                
                # 3. Mostrar el campo con formato adecuado
                porcentaje_adicional = st.number_input(
                    "Porc. adicional (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=porcentaje_default,
                    step=0.5,
                    format="%.1f",  # Muestra con 1 decimal
                    key="update_porcentaje_adicional_unique"  # Key único
                )


        # ENCABEZADOS
        with st.container():
            col1001, col1002, col1003, col1004, col1005, col1006 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col1001:
                gold_text("#")
            with col1002:
                gold_text("Quant.")
            with col1003:
                gold_text("Descrição da peça")
            with col1004:
                gold_text("Valor Unit")
            with col1005:
                gold_text("Sub Total")
            with col1006:
                gold_text("Total")

        with st.container():    
            col160, col161, col162, col163, col164, col165 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col160:
                gold_text("1") 
            with col161:
                quant_peca_1 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_1", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_1"
                )
            with col162:
                desc_peca_1 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_1", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_1"
                )
            with col163:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_1")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_1 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_1"
                )
            with col164:
                try:
                    qty = float(quant_peca_1.replace(",", ".")) if quant_peca_1 else 0.0
                    val = float(valor_peca_1) if valor_peca_1 else 0.0
                    sub_tota_peca_1 = qty * val
                    gold_text(f"R$ {sub_tota_peca_1:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col165:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_1 = float(quant_peca_1.replace(",", ".")) * float(valor_peca_1) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_1:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")   

        with st.container():    
            col170, col171, col172, col173, col174, col175 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col170:
                gold_text("2") 
            with col171:
                quant_peca_2 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_2", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_2"
                )
            with col172:
                desc_peca_2 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_2", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_2"
                )
            with col173:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_2")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_2 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_2"
                )
                
            with col174:
                try:
                    qty = float(quant_peca_2.replace(",", ".")) if quant_peca_2 else 0.0
                    val = float(valor_peca_2) if valor_peca_2 else 0.0
                    sub_tota_peca_2 = qty * val
                    gold_text(f"R$ {sub_tota_peca_2:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col175:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_2 = float(quant_peca_2.replace(",", ".")) * float(valor_peca_2) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_2:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        with st.container():
            col180, col181, col182, col183, col184, col185 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col180:
                gold_text("3") 
            with col181:
                quant_peca_3 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_3", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_3"
                )
            with col182:
                desc_peca_3 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_3", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_3"
                )
            with col183:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_3")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_3 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_3"
                )
                
            with col184:
                try:
                    qty = float(quant_peca_3.replace(",", ".")) if quant_peca_3 else 0.0
                    val = float(valor_peca_3) if valor_peca_3 else 0.0
                    sub_tota_peca_3 = qty * val
                    gold_text(f"R$ {sub_tota_peca_3:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col185:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_3 = float(quant_peca_3.replace(",", ".")) * float(valor_peca_3) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_3:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        
        with st.container():   
            col190, col191, col192, col193, col194, col195 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col190:
                gold_text("4") 
            with col191:
                quant_peca_4 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_4", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_4"
                )
            with col192:
                desc_peca_4 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_4", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_4"
                )
            with col193:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_4")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_4 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_4"
                )
            with col194:
                try:
                    qty = float(quant_peca_4.replace(",", ".")) if quant_peca_4 else 0.0
                    val = float(valor_peca_4) if valor_peca_4 else 0.0
                    sub_tota_peca_4 = qty * val
                    gold_text(f"R$ {sub_tota_peca_4:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col195:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_4 = float(quant_peca_4.replace(",", ".")) * float(valor_peca_4) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_4:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        
        with st.container():    
            col200, col201, col202, col203, col204, col205 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col200:
                gold_text("5") 
            with col201:
                quant_peca_5 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_5", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_5"
                )
            with col202:
                desc_peca_5 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_5", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_5"
                )
            with col203:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_5")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_5 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_5"
                )
            with col204:
                try:
                    qty = float(quant_peca_5.replace(",", ".")) if quant_peca_5 else 0.0
                    val = float(valor_peca_5) if valor_peca_5 else 0.0
                    sub_tota_peca_5 = qty * val
                    gold_text(f"R$ {sub_tota_peca_5:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col205:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_5 = float(quant_peca_5.replace(",", ".")) * float(valor_peca_5) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_5:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        
        with st.container():    
            col210, col211, col212, col213, col214, col215 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col210:
                gold_text("6") 
            with col211:
                quant_peca_6 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_6", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_6"
                )
            with col212:
                desc_peca_6 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_6", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_6"
                )
            with col213:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_6")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_6 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_6"
                )
            with col214:
                try:
                    qty = float(quant_peca_6.replace(",", ".")) if quant_peca_6 else 0.0
                    val = float(valor_peca_6) if valor_peca_6 else 0.0
                    sub_tota_peca_6 = qty * val
                    gold_text(f"R$ {sub_tota_peca_6:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col215:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_6 = float(quant_peca_6.replace(",", ".")) * float(valor_peca_6) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_6:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        
        with st.container():    
            col220, col221, col222, col223, col224, col225 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col220:
                gold_text("7") 
            with col221:
                quant_peca_7 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_7", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_7"
                )
            with col222:
                desc_peca_7 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_7", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_7"
                )
            with col223:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_7")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_7 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_7"
                )
            with col224:
                try:
                    qty = float(quant_peca_7.replace(",", ".")) if quant_peca_7 else 0.0
                    val = float(valor_peca_7) if valor_peca_7 else 0.0
                    sub_tota_peca_7 = qty * val
                    gold_text(f"R$ {sub_tota_peca_7:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col225:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_7 = float(quant_peca_7.replace(",", ".")) * float(valor_peca_7) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_7:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        with st.container():    
            col230, col231, col232, col233, col234, col235 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col230:
                gold_text("8") 
            with col231:
                quant_peca_8 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_8", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_8"
                )
            with col232:
                desc_peca_8 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_8", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_8"
                )
            with col233:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_8")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_8 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_8"
                )
            with col234:
                try:
                    qty = float(quant_peca_8.replace(",", ".")) if quant_peca_8 else 0.0
                    val = float(valor_peca_8) if valor_peca_8 else 0.0
                    sub_tota_peca_8 = qty * val
                    gold_text(f"R$ {sub_tota_peca_8:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col235:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_8 = float(quant_peca_8.replace(",", ".")) * float(valor_peca_8) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_8:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        with st.container():    
            col240, col241, col242, col243, col244, col245 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col240:
                gold_text("9") 
            with col241:
                quant_peca_9 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_9", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_9"
                )
            with col242:
                desc_peca_9 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_9", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_9"
                )
            with col243:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_9")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_9 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_9"
                )
            with col244:
                try:
                    qty = float(quant_peca_9.replace(",", ".")) if quant_peca_9 else 0.0
                    val = float(valor_peca_9) if valor_peca_9 else 0.0
                    sub_tota_peca_9 = qty * val
                    gold_text(f"R$ {sub_tota_peca_9:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col245:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_9 = float(quant_peca_9.replace(",", ".")) * float(valor_peca_9) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_9:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
            
        
        with st.container():    
            col250, col251, col252, col253, col254, col255 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col250:
                gold_text("10") 
            with col251:
                quant_peca_10 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_10", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_10"
                )
            with col252:
                desc_peca_10 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_10", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_10"
                )
            with col253:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_10")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_10 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_10"
                )
            with col254:
                try:
                    qty = float(quant_peca_10.replace(",", ".")) if quant_peca_10 else 0.0
                    val = float(valor_peca_10) if valor_peca_10 else 0.0
                    sub_tota_peca_10 = qty * val
                    gold_text(f"R$ {sub_tota_peca_10:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col255:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_10 = float(quant_peca_10.replace(",", ".")) * float(valor_peca_10) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_10:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        
        with st.container():    
            col260, col261, col262, col263, col264, col265 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col260:
                gold_text("11") 
            with col261:
                quant_peca_11 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_11", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_11"
                )
            with col262:
                desc_peca_11 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_11", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_11"
                )
            with col263:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_11")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_11 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_11"
                )
            with col264:
                try:
                    qty = float(quant_peca_11.replace(",", ".")) if quant_peca_11 else 0.0
                    val = float(valor_peca_11) if valor_peca_11 else 0.0
                    sub_tota_peca_11 = qty * val
                    gold_text(f"R$ {sub_tota_peca_11:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col265:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_11 = float(quant_peca_11.replace(",", ".")) * float(valor_peca_11) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_11:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
                    
        
        with st.container():    
            col270, col271, col272, col273, col274, col275 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col270:
                gold_text("12") 
            with col271:
                quant_peca_12 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_12", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_12"
                )
            with col272:
                desc_peca_12 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_12", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_12"
                )
            with col273:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_12")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_12 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_12"
                )
            with col274:
                try:
                    qty = float(quant_peca_12.replace(",", ".")) if quant_peca_12 else 0.0
                    val = float(valor_peca_12) if valor_peca_12 else 0.0
                    sub_tota_peca_12 = qty * val
                    gold_text(f"R$ {sub_tota_peca_12:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col275:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_12 = float(quant_peca_12.replace(",", ".")) * float(valor_peca_12) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_12:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")

        
        with st.container():    
            col280, col281, col282, col283, col284, col285 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col280:
                gold_text("13") 
            with col281:
                quant_peca_13 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_13", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_13"
                )
            with col282:
                desc_peca_13 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_13", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_13"
                )
            with col283:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_13")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_13 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_13"
                )
            with col284:
                try:
                    qty = float(quant_peca_13.replace(",", ".")) if quant_peca_13 else 0.0
                    val = float(valor_peca_13) if valor_peca_13 else 0.0
                    sub_tota_peca_13 = qty * val
                    gold_text(f"R$ {sub_tota_peca_13:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col285:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_13 = float(quant_peca_13.replace(",", ".")) * float(valor_peca_13) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_13:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        with st.container():    
            col290, col291, col292, col293, col294, col295 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col290:
                gold_text("14") 
            with col291:
                quant_peca_14 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_14", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_14"
                )
            with col292:
                desc_peca_14 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_14", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_14"
                )
            with col293:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_14")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_14 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_14"
                )
            with col294:
                try:
                    qty = float(quant_peca_14.replace(",", ".")) if quant_peca_14 else 0.0
                    val = float(valor_peca_14) if valor_peca_14 else 0.0
                    sub_tota_peca_14 = qty * val
                    gold_text(f"R$ {sub_tota_peca_14:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col295:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_14 = float(quant_peca_14.replace(",", ".")) * float(valor_peca_14) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_14:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        with st.container():    
            col300, col301, col302, col303, col304, col305 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col300:
                gold_text("15") 
            with col301:
                quant_peca_15 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_15", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_15"
                )
            with col302:
                desc_peca_15 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_15", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_15"
                )
            with col303:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_15")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_15 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_15"
                )
            with col304:
                try:
                    qty = float(quant_peca_15.replace(",", ".")) if quant_peca_15 else 0.0
                    val = float(valor_peca_15) if valor_peca_15 else 0.0
                    sub_tota_peca_15 = qty * val
                    gold_text(f"R$ {sub_tota_peca_15:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col305:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_15 = float(quant_peca_15.replace(",", ".")) * float(valor_peca_15) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_15:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        with st.container():    
            col310, col311, col312, col313, col314, col315 = st.columns([0.3, 0.5, 3, 0.7, 0.7, 0.7])
            with col310:
                gold_text("16") 
            with col311:
                quant_peca_16 = st.text_input(
                    "", 
                    value=str(vendor_data.get("quant_peca_16", "1")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_quant_peca_16"
                )
            with col312:
                desc_peca_16 = st.text_input(
                    "", 
                    value=str(vendor_data.get("desc_peca_16", "")),  # Aseguramos string
                    label_visibility="collapsed", 
                    key="update_desc_peca_16"
                )
            with col313:
                # Conversión ultra-segura del valor numérico
                try:
                    raw_value = vendor_data.get("valor_peca_16")
                    if raw_value in [None, "", "None"]:
                        default_value = 0.0
                    else:
                        default_value = float(str(raw_value).replace(",", "."))  # Manejo de decimales
                except (ValueError, TypeError):
                    default_value = 0.0
                    
                valor_peca_16 = st.number_input(
                    "", 
                    value=float(default_value),  # Aseguramos float
                    min_value=0.0,
                    max_value=1000000.0,
                    step=0.01,
                    format="%.2f",
                    label_visibility="collapsed", 
                    key="update_valor_peca_16"
                )
            with col314:
                try:
                    qty = float(quant_peca_16.replace(",", ".")) if quant_peca_16 else 0.0
                    val = float(valor_peca_16) if valor_peca_16 else 0.0
                    sub_tota_peca_16 = qty * val
                    gold_text(f"R$ {sub_tota_peca_16:.2f}")
                except:
                    gold_text("R$ 0.00")
            with col315:
                try:
                    if porcentaje_adicional:
                        valor_total_peca_16 = float(quant_peca_16.replace(",", ".")) * float(valor_peca_16) * (1 + float(porcentaje_adicional)/100)
                        gold_text(f"R$ {valor_total_peca_16:.2f}")
                    else:
                        gold_text("R$ 0.00")
                except:
                    gold_text("R$ 0.00")
        
        line(4, "blue")
        
        with st.container():
            col320, col321, col322, col323, col324 = st.columns([1.2, 1.2, 1, 1, 1])
            with col322:
                update_button = st.form_submit_button("Atualizar")

            if update_button:
                # Crear un diccionario con los datos actualizados
                updated_record = {
                    'user_id': vendor_to_update,  # Mantener el mismo user_id
                    'date_in': data_entrada,
                    'date_prev': previsao_entrega,
                    'date_out': data_saida,
                    'carro': carro,
                    'modelo': modelo,
                    'cor': cor,
                    'placa': placa,
                    'km': km,
                    'ano': ano,
                    'estado': estado,
                    'mecanico': mecanico,
                    'dono_empresa': dono_empresa,
                    'telefone': telefone,
                    'endereco': endereco,
                    'item_serv_1': item_serv_1 if 'item_serv_1' in locals() else None,
                    'desc_ser_1': desc_ser_1 if 'desc_ser_1' in locals() else None,
                    'valor_serv_1': valor_serv_1 if 'valor_serv_1' in locals() else None,
                    'item_serv_2': item_serv_2 if 'item_serv_2' in locals() else None,
                    'desc_ser_2': desc_ser_2 if 'desc_ser_2' in locals() else None,
                    'valor_serv_2': valor_serv_2 if 'valor_serv_2' in locals() else None,
                    'item_serv_3': item_serv_3 if 'item_serv_3' in locals() else None,
                    'desc_ser_3': desc_ser_3 if 'desc_ser_3' in locals() else None,
                    'valor_serv_3': valor_serv_3 if 'valor_serv_3' in locals() else None,
                    'item_serv_4': item_serv_4 if 'item_serv_4' in locals() else None,
                    'desc_ser_4': desc_ser_4 if 'desc_ser_4' in locals() else None,
                    'valor_serv_4': valor_serv_4 if 'valor_serv_4' in locals() else None,
                    'item_serv_5': item_serv_5 if 'item_serv_5' in locals() else None,
                    'desc_ser_5': desc_ser_5 if 'desc_ser_5' in locals() else None,
                    'valor_serv_5': valor_serv_5 if 'valor_serv_5' in locals() else None,
                    'item_serv_6': item_serv_6 if 'item_serv_6' in locals() else None,
                    'desc_ser_6': desc_ser_6 if 'desc_ser_6' in locals() else None,
                    'valor_serv_6': valor_serv_6 if 'valor_serv_6' in locals() else None,
                    'item_serv_7': item_serv_7 if 'item_serv_7' in locals() else None,
                    'desc_ser_7': desc_ser_7 if 'desc_ser_7' in locals() else None,
                    'valor_serv_7': valor_serv_7 if 'valor_serv_7' in locals() else None,
                    'item_serv_8': item_serv_8 if 'item_serv_8' in locals() else None,
                    'desc_ser_8': desc_ser_8 if 'desc_ser_8' in locals() else None,
                    'valor_serv_8': valor_serv_8 if 'valor_serv_8' in locals() else None,
                    'item_serv_9': item_serv_9 if 'item_serv_9' in locals() else None,
                    'desc_ser_9': desc_ser_9 if 'desc_ser_9' in locals() else None,
                    'valor_serv_9': valor_serv_9 if 'valor_serv_9' in locals() else None,
                    'item_serv_10': item_serv_10 if 'item_serv_10' in locals() else None,
                    'desc_ser_10': desc_ser_10 if 'desc_ser_10' in locals() else None,
                    'valor_serv_10': valor_serv_10 if 'valor_serv_10' in locals() else None,
                    'item_serv_11': item_serv_11 if 'item_serv_11' in locals() else None,
                    'desc_ser_11': desc_ser_11 if 'desc_ser_11' in locals() else None,
                    'valor_serv_11': valor_serv_11 if 'valor_serv_11' in locals() else None,
                    'item_serv_12': item_serv_12 if 'item_serv_12' in locals() else None,
                    'desc_ser_12': desc_ser_12 if 'desc_ser_12' in locals() else None,
                    'valor_serv_12': valor_serv_12 if 'valor_serv_12' in locals() else None,
                    'total_serviço': None,
                    'porcentaje_adicional': porcentaje_adicional,
                    'quant_peca_1': quant_peca_1 if 'quant_peca_1' in locals() else None,
                    'desc_peca_1': desc_peca_1 if 'desc_peca_1' in locals() else None,
                    'valor_peca_1': valor_peca_1 if 'valor_peca_1' in locals() else 0,
                    'sub_tota_peca_1': sub_tota_peca_1 if 'sub_tota_peca_1' in locals() else 0,
                    'valor_total_peca_1': valor_total_peca_1 if 'valor_total_peca_1' in locals() else 0, 
                    'quant_peca_2': quant_peca_2 if 'quant_peca_2' in locals() else None,
                    'desc_peca_2': desc_peca_2 if 'desc_peca_2' in locals() else None,
                    'valor_peca_2': valor_peca_2 if 'valor_peca_2' in locals() else 0,
                    'sub_tota_peca_2': sub_tota_peca_2 if 'sub_tota_peca_2' in locals() else 0,
                    'valor_total_peca_2': valor_total_peca_2 if 'valor_total_peca_2' in locals() else 0,
                    'quant_peca_3': quant_peca_3 if 'quant_peca_3' in locals() else None,
                    'desc_peca_3': desc_peca_3 if 'desc_peca_3' in locals() else None,
                    'valor_peca_3': valor_peca_3 if 'valor_peca_3' in locals() else 0,
                    'sub_tota_peca_3': sub_tota_peca_3 if 'sub_tota_peca_3' in locals() else 0,
                    'valor_total_peca_3': valor_total_peca_3 if 'valor_total_peca_3' in locals() else 0,          
                    'quant_peca_4': quant_peca_4 if 'quant_peca_4' in locals() else None,
                    'desc_peca_4': desc_peca_4 if 'desc_peca_4' in locals() else None,
                    'valor_peca_4': valor_peca_4 if 'valor_peca_4' in locals() else 0,
                    'sub_tota_peca_4': sub_tota_peca_4 if 'sub_tota_peca_4' in locals() else 0,
                    'valor_total_peca_4': valor_total_peca_4 if 'valor_total_peca_4' in locals() else 0,                     
                    'quant_peca_5': quant_peca_5 if 'quant_peca_5' in locals() else None,
                    'desc_peca_5': desc_peca_5 if 'desc_peca_5' in locals() else None,
                    'valor_peca_5': valor_peca_5 if 'valor_peca_5' in locals() else 0,
                    'sub_tota_peca_5': sub_tota_peca_5 if 'sub_tota_peca_5' in locals() else 0,
                    'valor_total_peca_5': valor_total_peca_5 if 'valor_total_peca_5' in locals() else 0,                     
                    'quant_peca_6': quant_peca_6 if 'quant_peca_6' in locals() else None,
                    'desc_peca_6': desc_peca_6 if 'desc_peca_6' in locals() else None,
                    'valor_peca_6': valor_peca_6 if 'valor_peca_6' in locals() else 0,
                    'sub_tota_peca_6': sub_tota_peca_6 if 'sub_tota_peca_6' in locals() else 0,
                    'valor_total_peca_6': valor_total_peca_6 if 'valor_total_peca_6' in locals() else 0,                 
                    'quant_peca_7': quant_peca_7 if 'quant_peca_7' in locals() else None,
                    'desc_peca_7': desc_peca_7 if 'desc_peca_7' in locals() else None,
                    'valor_peca_7': valor_peca_7 if 'valor_peca_7' in locals() else 0,
                    'sub_tota_peca_7': sub_tota_peca_7 if 'sub_tota_peca_7' in locals() else 0,
                    'valor_total_peca_7': valor_total_peca_7 if 'valor_total_peca_7' in locals() else 0,                  
                    'quant_peca_8': quant_peca_8 if 'quant_peca_8' in locals() else None,
                    'desc_peca_8': desc_peca_8 if 'desc_peca_8' in locals() else None,
                    'valor_peca_8': valor_peca_8 if 'valor_peca_8' in locals() else 0,
                    'sub_tota_peca_8': sub_tota_peca_8 if 'sub_tota_peca_8' in locals() else 0,
                    'valor_total_peca_8': valor_total_peca_8 if 'valor_total_peca_8' in locals() else 0,                      
                    'quant_peca_9': quant_peca_9 if 'quant_peca_9' in locals() else None,
                    'desc_peca_9': desc_peca_9 if 'desc_peca_9' in locals() else None,
                    'valor_peca_9': valor_peca_9 if 'valor_peca_9' in locals() else 0,
                    'sub_tota_peca_9': sub_tota_peca_9 if 'sub_tota_peca_9' in locals() else 0,
                    'valor_total_peca_9': valor_total_peca_9 if 'valor_total_peca_9' in locals() else 0,                     
                    'quant_peca_10': quant_peca_10 if 'quant_peca_10' in locals() else None,
                    'desc_peca_10': desc_peca_10 if 'desc_peca_10' in locals() else None,
                    'valor_peca_10': valor_peca_10 if 'valor_peca_10' in locals() else 0,
                    'sub_tota_peca_10': sub_tota_peca_10 if 'sub_tota_peca_10' in locals() else 0,
                    'valor_total_peca_10': valor_total_peca_10 if 'valor_total_peca_10' in locals() else 0,                      
                    'quant_peca_11': quant_peca_11 if 'quant_peca_11' in locals() else None,
                    'desc_peca_11': desc_peca_11 if 'desc_peca_11' in locals() else None,
                    'valor_peca_11': valor_peca_11 if 'valor_peca_11' in locals() else 0,
                    'sub_tota_peca_11': sub_tota_peca_11 if 'sub_tota_peca_11' in locals() else 0,
                    'valor_total_peca_11': valor_total_peca_11 if 'valor_total_peca_11' in locals() else 0,                      
                    'quant_peca_12': quant_peca_12 if 'quant_peca_12' in locals() else None,
                    'desc_peca_12': desc_peca_12 if 'desc_peca_12' in locals() else None,
                    'valor_peca_12': valor_peca_12 if 'valor_peca_12' in locals() else 0,
                    'sub_tota_peca_12': sub_tota_peca_12 if 'sub_tota_peca_12' in locals() else 0,
                    'valor_total_peca_12': valor_total_peca_12 if 'valor_total_peca_12' in locals() else 0,  
                    'quant_peca_13': quant_peca_13 if 'quant_peca_13' in locals() else None,
                    'desc_peca_13': desc_peca_13 if 'desc_peca_13' in locals() else None,
                    'valor_peca_13': valor_peca_13 if 'valor_peca_13' in locals() else 0,
                    'sub_tota_peca_13': sub_tota_peca_13 if 'sub_tota_peca_13' in locals() else 0,
                    'valor_total_peca_13': valor_total_peca_13 if 'valor_total_peca_13' in locals() else 0, 
                    'quant_peca_14': quant_peca_14 if 'quant_peca_14' in locals() else None,
                    'desc_peca_14': desc_peca_14 if 'desc_peca_14' in locals() else None,
                    'valor_peca_14': valor_peca_14 if 'valor_peca_14' in locals() else 0,
                    'sub_tota_peca_14': sub_tota_peca_14 if 'sub_tota_peca_14' in locals() else 0,
                    'valor_total_peca_14': valor_total_peca_14 if 'valor_total_peca_14' in locals() else 0,        
                    'quant_peca_15': quant_peca_15 if 'quant_peca_15' in locals() else None,
                    'desc_peca_15': desc_peca_15 if 'desc_peca_15' in locals() else None,
                    'valor_peca_15': valor_peca_15 if 'valor_peca_15' in locals() else 0,
                    'sub_tota_peca_15': sub_tota_peca_15 if 'sub_tota_peca_15' in locals() else 0,
                    'valor_total_peca_15': valor_total_peca_15 if 'valor_total_peca_15' in locals() else 0,
                    'quant_peca_16': quant_peca_16 if 'quant_peca_16' in locals() else None,
                    'desc_peca_16': desc_peca_16 if 'desc_peca_16' in locals() else None,
                    'valor_peca_16': valor_peca_16 if 'valor_peca_16' in locals() else 0,
                    'sub_tota_peca_16': sub_tota_peca_16 if 'sub_tota_peca_16' in locals() else 0,
                    'valor_total_peca_16': valor_total_peca_16 if 'valor_total_peca_16' in locals() else 0,                    
                    'total_costo_inicial': sum([v for k, v in locals().items() if k.startswith('costo_inicial_')]),
                    'total_costo_final': sum([v for k, v in locals().items() if k.startswith('costo_final_')]),
                    'forma_de_pagamento': None,
                    'pagamento_parcial': None,
                    'valor_pago_parcial': None,
                    'data_prox_pag': None,
                    'valor_prox_pag': None,
                    'pag_total': None,
                    'valor_pag_total': None
                }
                #worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
                atualizar_ordem(worksheet, vendor_to_update, updated_record)

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
