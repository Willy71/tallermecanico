# 2_Consultar_carro.py
import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from firebase_config import db
from firebase_admin import firestore

#====================================================================================================================================================
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


# Título de la página
st.title("🔍 Consultar Veículo por Placa")

##====================================================================================================================================================
# Conexion via gspread a traves de https://console.cloud.google.com/ y Google sheets



def carregar_ordens_firebase():
    try:
        user_id = st.session_state.usuario
        ordens = db.collection("usuarios").document(user_id).collection("ordens_servico").stream()
        lista = []
        for doc in ordens:
            item = doc.to_dict()
            lista.append(item)
        df = pd.DataFrame(lista)
        if 'user_id' in df.columns:
            df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        return pd.DataFrame()

# Función para buscar vehículo por placa
def buscar_por_placa(placa, df):
    if df.empty:
        return None
    
    # Buscar coincidencias exactas (ignorando mayúsculas/minúsculas y espacios)
    resultado = df[df['placa'].astype(str).str.upper().str.strip() == placa.upper().strip()]
    
    if not resultado.empty:
        return resultado.iloc[-1].to_dict()  # Tomar el último ingreso en lugar del primero
    return None
#====================================================================================================================================================

def safe_float(valor):
    """Convierte cualquier valor a float de manera segura"""
    # Verificación segura de valores nulos o vacíos
    if pd.isna(valor) or valor in [None, '']:
        return 0.0
    
    # Si ya es numérico, retornar directamente
    if isinstance(valor, (int, float)):
        return float(valor)
    
    try:
        # Convertir a string y limpiar
        str_valor = str(valor).strip()
        str_valor = str_valor.replace('R$', '').replace('$', '').strip()
        
        # Detección automática de formato
        if '.' in str_valor and ',' in str_valor:  # Formato 1.234,56
            return float(str_valor.replace('.', '').replace(',', '.'))
        elif ',' in str_valor:  # Formato 1234,56
            return float(str_valor.replace(',', '.'))
        else:  # Formato americano 1234.56 o entero
            return float(str_valor)
    except:
        return 0.0


def formatar_valor(valor, padrao=""):
    """
    Formatea valores para visualización segura
    
    Args:
        valor: Valor a formatear (str, float, int, None)
        padrao: Valor por defecto si no se puede formatear (default: "")
    
    Returns:
        str: Valor formateado o string vacío si es nulo/inválido
    """
    if pd.isna(valor) or valor in [None, '']:
        return padrao
    try:
        return str(valor).strip()
    except:
        return padrao

def formatar_dos(valor):
    try:
        valor_float = float(valor)
        return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "0,00"


def formatar_real(valor, padrao="0,00"):
    """
    Formata valores para el estándar monetario brasileño (R$ 0,00)
    
    Args:
        valor: Valor a formatear (str, float, int o None)
        padrao: Valor por defecto si no se puede formatear (default: "0,00")
    
    Returns:
        str: Valor formateado con coma decimal (ej. "1.234,56")
    """
    try:
        # Convierte a string y limpia
        str_valor = str(valor).strip()
        
        # Verifica valores vacíos o inválidos
        if not str_valor or str_valor.lower() in ['nan', 'none', 'null', '']:
            return padrao
            
        # Reemplaza comas por puntos para conversión a float
        str_valor = str_valor.replace('.', '').replace(',', '.')
        
        # Formatea con 2 decimales y comas como separador decimal
        valor_float = float(str_valor)
        return f"{valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    except (ValueError, TypeError, AttributeError):
        return padrao
#====================================================================================================================================================

def line(size, color):
    """
    Draws a horizontal line on the Streamlit page.

    Parameters:
    - size (str): The thickness of the line.
    - color (str): The color of the line.
    """
    st.markdown(
        f"<hr style='height:{size}px;border:none;color:{color};background-color:{color};' />",
        unsafe_allow_html=True
    )

def center_text(text, size, color):
    """
    Centers text on the Streamlit page.

    Parameters:
    - text (str): The text to display.
    - size (str): The size of the text (HTML heading size, e.g., "1" for <h1>).
    - color (str): The color of the text.
    """
    st.markdown(
        f"<h{size} style='text-align: center; color: {color}'>{text}</h{size}>",
        unsafe_allow_html=True
    )

def text(text, align = "left", size = 4, color = "white"):
    """
    Centers text on the Streamlit page.

    Parameters:
    - text (str): The text to display.
    - align (str) Indicate the text alignment. center - right - left    
    - size (str): The size of the text (HTML heading size, e.g., "1" for <h1>).
    - color (str): The color of the text.
    """
    st.markdown(
        f"<h{size} style='text-align: {align}; color: {color}'>{text}</h{size}>",
        unsafe_allow_html=True
    )

#====================================================================================================================================================

# Inicializar la hoja de cálculo
#worksheet = inicializar_hoja()

# Cargar datos
#dados = cargar_datos(worksheet)
dados = carregar_ordens_firebase()
env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template_1 = env.get_template("template.html")
template_2 = env.get_template("template_2.html")
#====================================================================================================================================================
# Inicialización (al inicio del script, fuera de cualquier función)
if 'veiculo' not in st.session_state:
    st.session_state.veiculo = None


# Interfaz con input + botón
with st.container():
    col1, col2, col3, col4, col5 = st.columns([3, 3, 3, 3, 2])
    with col1:
        placa = st.text_input("Digite a placa do veículo:", key="placa_input").strip().upper()
    with col2:
        st.write("")  # Espaciador
        st.write("")  # Espaciador
        buscar = st.button("Buscar Veículo", key="buscar_btn")
    

# Manejo del estado de búsqueda
if 'veiculo_encontrado' not in st.session_state:
    st.session_state.veiculo_encontrado = None
    
if buscar:
    if not placa:
        st.warning("Por favor, digite uma placa para buscar")
    else:
        with st.spinner("Buscando veículo..."):
            veiculo = buscar_por_placa(placa, dados)
            if veiculo:
                st.session_state.veiculo_encontrado = veiculo

# Mostrar resultados si hay vehículo encontrado
if st.session_state.veiculo_encontrado:
    veiculo = st.session_state.veiculo_encontrado
    st.success("✅ Veículo encontrado!")
                
    # Mostrar información principal en cards
    with st.container():
        cols = st.columns(4)
        with cols[0]:
            text("Placa", "center", 7, "yellow")
            text(f"{formatar_valor(veiculo.get('placa'))}", "left", 3, "white")
        with cols[1]:
            text("Marca", "center", 7, "yellow")
            text(f"{formatar_valor(veiculo.get('carro'))}", "left", 3, "white")
            #st.metric("Marca", formatar_valor(veiculo.get('carro')))
        with cols[2]:
            text("Modelo", "center", 7, "yellow")
            text(f"{formatar_valor(veiculo.get('modelo'))}", "left", 3, "white")
            #st.metric("Modelo", formatar_valor(veiculo.get('modelo')))
        with cols[3]:
            ano = veiculo.get('ano')
            if isinstance(ano, float):
                ano = int(ano)
            text("Ano", "center", 7, "yellow")
            text(f"{formatar_valor(veiculo.get('ano'))}", "left", 3, "white")
            #st.metric("Ano", formatar_valor(ano))
    st.text("")
    # Mostrar detalles del estado y fechas
    with st.container():
        cols = st.columns(4)
        with cols[0]:
            text("Estado", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('estado'))}", "left", 5, "white")
            #st.metric("Estado", formatar_valor(veiculo.get('estado')))
        with cols[1]:
            text("Mecanico", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('mecanico'))}", "left", 5, "white")
        with cols[2]:
            text("Data de Entrada", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('date_in'))}", "left", 5, "white")
            #st.metric("Data Entrada", formatar_valor(veiculo.get('date_in')))
        with cols[3]:
            text("Data de Entrega", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('date_out'))}", "left", 5, "white")
            #st.metric("Previsão Entrega", formatar_valor(veiculo.get('date_prev')))
    st.text("")    
    # Mostrar información del dueño
    with st.container():
        cols = st.columns(3)
        with cols[0]:
            text("Proprietário", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('dono_empresa'))}", "left", 5, "white")
            #st.subheader("Proprietário", divider=True)
            #st.header(formatar_valor(veiculo.get('dono_empresa')))
        with cols[1]:
            text("Telefone", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('telefone'))}", "left", 5, "white")
            #st.metric("Telefone", formatar_valor(veiculo.get('telefone')))
        with cols[2]:
            text("Endereço", "center", 8, "yellow")
            text(f"{formatar_valor(veiculo.get('endereco'))}", "left", 5, "white")
            #st.metric("Endereço", formatar_valor(veiculo.get('endereco')))
#===================================================================================================================================================================
    with st.expander("📋 Serviços Realizados", expanded=False):
        servicos = []
        total_servicos = 0.0
    
        for i in range(1, 13):
            item = veiculo.get(f'item_serv_{i}', '')
            desc = veiculo.get(f'desc_ser_{i}', '')
            valor = veiculo.get(f'valor_serv_{i}', '')
        
            # Convertir el valor a float seguro
            valor_float = safe_float(valor) if pd.notna(valor) else 0.0
        
            # Verificamos si hay descripción o valor diferente de cero
            if (pd.notna(desc) and str(desc).strip() != "") or valor_float > 0:
                valor_formatado = formatar_dos(valor_float)
                total_servicos += valor_float
        
                servicos.append({
                    'Item': item if pd.notna(item) else '',
                    'Descrição': desc if pd.notna(desc) else '',
                    'Valor (R$)': valor_formatado
                })

    
        if servicos:
            df_servicos = pd.DataFrame(servicos)
            st.dataframe(df_servicos, hide_index=True, use_container_width=True)
            
            # Mostrar total de servicios
            st.markdown(f"**Total Serviços:** R$ {formatar_valor(total_servicos)}")
        else:
            st.info("Nenhum serviço registrado")

#==============================================================================================================================================================


   # Mostrar peças con expanders
    with st.expander("🔧 Peças Utilizadas", expanded=False):
        pecas = []
        total_pecas = 0.0
        total_pecas_final = 0.0
        
        for i in range(1, 17):
            quant = veiculo.get(f'quant_peca_{i}', '')  # Cantidad
            desc = veiculo.get(f'desc_peca_{i}', '')  # Descripción
            valor = veiculo.get(f'valor_peca_{i}', '')  # Costo unitario
            porcentaje = veiculo.get('porcentaje_adicional', 0)  # Porcentaje adicional
    
            quant_float = safe_float(quant)
            valor_float = safe_float(valor)
            valor_total_peca = quant_float * valor_float
            valor_total_final = valor_total_peca * (1 + safe_float(porcentaje) / 100)
    
            # Filtrar sólo si hay descripción o valor total > 0
            if (pd.notna(desc) and str(desc).strip() != "") or valor_total_peca > 0:
                total_pecas += valor_total_peca
                total_pecas_final += valor_total_final
    
                pecas.append({
                    'Quant.': quant if pd.notna(quant) else '',
                    'Descrição': desc if pd.notna(desc) else '',
                    'Custo Unit. (R$)': formatar_dos(valor_float),
                    '% Adicional': f"{porcentaje}%" if pd.notna(porcentaje) else "0%",
                    'Valor Final (R$)': f"{formatar_dos(valor_total_final)}"
                })

        
        if pecas:
            df_pecas = pd.DataFrame(pecas)
            st.dataframe(df_pecas, hide_index=True, use_container_width=True)
            
            # Mostrar totales
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Total Costo Peças:** R$ {formatar_dos(total_pecas)}")
            with col2:
                st.markdown(f"**Total Final Peças:** R$ {formatar_dos(total_pecas_final)}")
        else:
            st.info("Nenhuma peça registrada")
    

    # Mostrar el gran total después de ambas secciones
    if 'total_servicos' in locals() and 'total_pecas' in locals():
        total_geral = total_servicos + total_pecas_final
        st.success(f"**TOTAL GERAL (Serviços + Peças):** R$ {formatar_dos(total_geral)}")


    col1, col2, col3, col4, col5 = st.columns(5)
    with col2:
        if st.button("Gerar PDF cliente", key="gerar_pdf_cliente"):
            with st.spinner("Generando PDF..."):
                try:
                    # 1. PROCESAR SERVIÇOS
                    servicos_pdf = []
                    total_servicos_pdf = 0.0
                    
                    for i in range(1, 12):
                        item = veiculo.get(f'item_serv_{i}', '')
                        desc = veiculo.get(f'desc_ser_{i}', '')
                        valor = veiculo.get(f'valor_serv_{i}', '')
                        
                        valor_float = safe_float(valor) if pd.notna(valor) else 0.0
        
                        if (pd.notna(desc) and str(desc).strip() != "") or valor_float > 0:
                            total_servicos_pdf += valor_float
                            servicos_pdf.append({
                                'Item': str(item),
                                'Descrição': str(desc),
                                'Valor': formatar_dos(valor_float)
                            })
        
                    # 2. PROCESAR PEÇAS
                    pecas_pdf = []
                    total_pecas_final_pdf = 0.0
                    porcentaje_adicional = safe_float(veiculo.get('porcentaje_adicional', 0))
                    
                    for i in range(1, 16):
                        quant = veiculo.get(f'quant_peca_{i}', '')
                        desc = veiculo.get(f'desc_peca_{i}', '')
                        valor = veiculo.get(f'valor_peca_{i}', '')
                        sub_total_peça = veiculo.get(f'sub_tota_peca_{i}', '')
                        
                        quant_float = safe_float(quant)
                        valor_unitario = safe_float(valor)
                        sub_total = safe_float(sub_total_peça)
                        valor_total = quant_float * valor_unitario
                        valor_con_adicional = valor_total * (1 + porcentaje_adicional / 100)
        
                        # Mostrar solo si hay descripción o el valor total > 0
                        if (pd.notna(desc) and str(desc).strip() != "") or valor_total > 0:
                            total_pecas_final_pdf += valor_con_adicional
        
                            pecas_pdf.append({
                                'Quant': str(quant),
                                'Descrição': str(desc),
                                'Custo Unit.': formatar_dos(valor_unitario),
                                'Sub-Total' : formatar_dos(sub_total),
                                'Valor Final': formatar_dos(valor_con_adicional)
                            })
        
                    # 3. GENERAR PDF
                    html = template_1.render(
                        data_emissao=datetime.now().strftime("%d/%m/%Y %H:%M"),
                        placa=veiculo['placa'],
                        carro=veiculo['carro'],
                        modelo=veiculo['modelo'],
                        ano=veiculo['ano'],
                        cor=veiculo['cor'],
                        dono_empresa=veiculo.get('dono_empresa', ''),
                        date_in=veiculo.get('date_in', ''),
                        date_prev=veiculo.get('date_prev', ''),
                        servicos=servicos_pdf,
                        pecas=pecas_pdf,
                        total_servicos=formatar_dos(total_servicos_pdf),
                        total_pecas_final=formatar_dos(total_pecas_final_pdf),
                        total_geral=formatar_dos(total_servicos_pdf + total_pecas_final_pdf)
                    )
        
                    pdf = pdfkit.from_string(html, False)
                    st.download_button(
                        "⬇️ Baixar PDF",
                        data=pdf,
                        file_name=f"{veiculo['placa']}_{veiculo['carro']}_{veiculo['modelo']} - CLIENTE.pdf",
                        mime="application/octet-stream"
                    )
        
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")

    with col4:
        if st.button("Gerar PDF oficina", key="gerar_pdf_oficina"):
            with st.spinner("Generando PDF..."):
                try:
                    # 1. PROCESAR SERVIÇOS
                    servicos_pdf = []
                    total_servicos_pdf = 0.0
                    
                    for i in range(1, 12):
                        item = veiculo.get(f'item_serv_{i}', '')
                        desc = veiculo.get(f'desc_ser_{i}', '')
                        valor = veiculo.get(f'valor_serv_{i}', '')
                        
                        valor_float = safe_float(valor) if pd.notna(valor) else 0.0
        
                        if (pd.notna(desc) and str(desc).strip() != "") or valor_float > 0:
                            total_servicos_pdf += valor_float
                            servicos_pdf.append({
                                'Item': str(item),
                                'Descrição': str(desc),
                                'Valor': formatar_dos(valor_float)
                            })
        
                    # 2. PROCESAR PEÇAS
                    pecas_pdf = []
                    total_pecas_final_pdf = 0.0
                    porcentaje_adicional = safe_float(veiculo.get('porcentaje_adicional', 0))
                    
                    for i in range(1, 16):
                        quant = veiculo.get(f'quant_peca_{i}', '')
                        desc = veiculo.get(f'desc_peca_{i}', '')
                        valor = veiculo.get(f'valor_peca_{i}', '')
                        sub_total_peça = veiculo.get(f'sub_tota_peca_{i}', '')
                        
                        quant_float = safe_float(quant)
                        valor_unitario = safe_float(valor)
                        sub_total = safe_float(sub_total_peça)
                        valor_total = quant_float * valor_unitario
                        valor_con_adicional = valor_total * (1 + porcentaje_adicional / 100)
        
                        # Mostrar solo si hay descripción o el valor total > 0
                        if (pd.notna(desc) and str(desc).strip() != "") or valor_total > 0:
                            total_pecas_final_pdf += valor_con_adicional
        
                            pecas_pdf.append({
                                'Quant': str(quant),
                                'Descrição': str(desc),
                                'Custo Unit.': formatar_dos(valor_unitario),
                                'Sub-Total' : formatar_dos(sub_total),
                                'Valor Final': formatar_dos(valor_con_adicional)
                            })
        
                    # 3. GENERAR PDF
                    html = template_2.render(
                        data_emissao=datetime.now().strftime("%d/%m/%Y %H:%M"),
                        placa=veiculo['placa'],
                        carro=veiculo['carro'],
                        modelo=veiculo['modelo'],
                        ano=veiculo['ano'],
                        cor=veiculo['cor'],
                        dono_empresa=veiculo.get('dono_empresa', ''),
                        date_in=veiculo.get('date_in', ''),
                        date_prev=veiculo.get('date_prev', ''),
                        servicos=servicos_pdf,
                        pecas=pecas_pdf,
                        total_servicos=formatar_dos(total_servicos_pdf),
                        total_pecas_final=formatar_dos(total_pecas_final_pdf),
                        total_geral=formatar_dos(total_servicos_pdf + total_pecas_final_pdf)
                    )
        
                    pdf = pdfkit.from_string(html, False)
                    st.download_button(
                        "⬇️ Baixar PDF",
                        data=pdf,
                        file_name=f"{veiculo['placa']}_{veiculo['carro']}_{veiculo['modelo']} - OFICINA.pdf",
                        mime="application/octet-stream"
                    )
        
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")


#==========================================================================================================================================================
# Opción para buscar por otros criterios
with st.expander("🔎 Busca Avançada", expanded=False):
    with st.form(key="busca_avancada"):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca (opcional)", "")
        with col2:
            modelo = st.text_input("Modelo (opcional)", "")
        
        col3, col4 = st.columns(2)
        with col3:
            estado_options = ["Todos"] + dados['estado'].dropna().unique().tolist() if not dados.empty else []
            estado = st.selectbox("Estado (opcional)", estado_options)
        with col4:
            ano = st.text_input("Ano (opcional)", "")
        
        buscar_avancado = st.form_submit_button("Buscar")
        
        if buscar_avancado:
            filtrados = dados.copy()
            
            if marca:
                filtrados = filtrados[filtrados['carro'].astype(str).str.contains(marca, case=False)]
            if modelo:
                filtrados = filtrados[filtrados['modelo'].astype(str).str.contains(modelo, case=False)]
            if estado and estado != "Todos":
                filtrados = filtrados[filtrados['estado'] == estado]
            if ano:
                filtrados = filtrados[filtrados['ano'].astype(str).str.contains(ano)]
            
            if not filtrados.empty:
                st.success(f"🚙 {len(filtrados)} veículos encontrados")    
                for _, row in filtrados.iterrows():
                    veiculo_str = f"🚗 {row['carro']}    {row['modelo']}        🏷️ {row['placa']}        🎨 {row.get('cor', 'Sem cor')}        📅 Entrada: {row.get('date_in', 'Sem data')}        👤 Dono: {row.get('dono_empresa', 'Desconhecido')}" 
                    st.markdown(f"- {veiculo_str}")
            else:
                st.warning("Nenhum veículo encontrado com os critérios especificados")
