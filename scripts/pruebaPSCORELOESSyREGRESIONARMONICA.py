import streamlit as st
import duckdb
import pandas as pd
import altair as alt
import numpy as np

# =============================================================================
# BLOQUE 1: CONFIGURACIÓN DE LA APLICACIÓN
# Establece los parámetros básicos de la ventana web y define estilos CSS
# para que los contenedores, métricas y títulos se vean limpios y corporativos.
# =============================================================================
st.set_page_config(
    page_title="Vigilancia Respiratoria SST",
    layout="wide", # Usa todo el ancho de la pantalla
    initial_sidebar_state="collapsed"
)

# Inyección de CSS para estandarizar fuentes, colores y bordes.
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 3rem;}
    h1 {font-family: 'Segoe UI', sans-serif; font-weight: 700; color: #102a43; font-size: 2.2rem;}
    h2 {font-family: 'Segoe UI', sans-serif; font-weight: 600; color: #102a43; font-size: 1.5rem; border-bottom: 1px solid #d9e2ec; padding-bottom: 10px;}
    h3 {font-family: 'Segoe UI', sans-serif; font-weight: 600; color: #334e68; font-size: 1.2rem;}
    .stMetric {background-color: #f0f4f8; border: 1px solid #d9e2ec; padding: 10px; border-radius: 4px;}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# BLOQUE 2: CARGA, TRANSFORMACIÓN Y CACHÉ DE DATOS
# Se utiliza DuckDB para leer el archivo Parquet pesado de forma casi instantánea.
# Los resultados se guardan en la memoria caché de Streamlit para no volver a
# leer el archivo en cada interacción del usuario (click en botones/sliders).
# =============================================================================
FILE_PATH = 'base_talcahuano_final_tasa_ok.parquet'

# Diccionario utilizado exclusivamente para simplificar la lectura en los gráficos.
# Toma las clasificaciones técnicas establecidas en el dataset publico del gobierno y las convierte en lenguaje clínico común.
MAPEO_CAUSAS = {
    "IRA Alta (J00-J06)": "IRA Alta",
    "Bronquitis/bronquiolitis aguda (J20-J21)": "Bronquiolitis",
    "Neumonía (J12-J18)": "Neumonía",
    "Crisis obstructiva bronquial (J40-J46)": "Crisis Obstructiva",
    "Influenza (J09-J11)": "Influenza",
    "TOTAL ATENCIONES POR COVID-19 Virus Identificado U07.1": "COVID",
    "TOTAL ATENCIONES POR COVID-19 Virus no Identificado U07.2": "SOSPECHA COVID",
    "Otra causa respiratoria no contenidas en las categorías anteriores (J22; J30-J39, J47, J60-J98)": "Otras IRA",
    "- Causas sistema respiratorio (J00-J98)": "Causas Totales"
}

@st.cache_resource
def get_connection():
    """Establece una única conexión viva a DuckDB."""
    return duckdb.connect()

@st.cache_data
def load_data():
    """
    Lee el Parquet, aplica los mapeos visuales y genera una nueva columna
    ('NivelGestion') que categoriza los establecimientos según su complejidad.
    """
    con = duckdb.connect()
    try:
        # Lee directamente el archivo local usando SQL
        df = con.execute(f"SELECT * FROM '{FILE_PATH}'").df()
        
        # Se aplica la limpieza visual a la columna 'Causa' si existe.
        if 'Causa' in df.columns:
            df['Causa'] = df['Causa'].str.strip().replace(MAPEO_CAUSAS)
            
        def clasificar_nivel(glosa_tipo):
            """Función auxiliar para agrupar centros de salud por nivel resolutivo."""
            glosa = str(glosa_tipo).upper()
            if 'HOSPITAL' in glosa or 'INSTITUTO' in glosa:
                return 'Atención Hospitalaria'
            elif any(x in glosa for x in ['SAPU', 'SAR', 'SUR']):
                return 'Atención Primaria Urgencia'
            else:
                return 'Otros'

        # Busca la columna correcta (por compatibilidad de nombres) y aplica la clasificación.
        col_ref = 'TipoEstablecimiento' if 'TipoEstablecimiento' in df.columns else 'EstablecimientoGlosa'
        df['NivelGestion'] = df[col_ref].apply(clasificar_nivel)
            
        return df
    except Exception as e:
        return None

# Llamada de ejecución principal de datos
df_full = load_data()

# Mecanismo de parada segura si no se encuentra el archivo
if df_full is None:
    st.error(f"❌ Error Crítico: No se encuentra el archivo '{FILE_PATH}'. Asegúrate de que esté en la misma carpeta.")
    st.stop()

# Extracción de variables universales para poblar los selectores del dashboard
ANIOS_DISPONIBLES = sorted(df_full['Anio'].unique(), reverse=True)
COMUNAS_DISPONIBLES = sorted(df_full['ComunaGlosa'].unique())

# =============================================================================
# BLOQUE 3: ESTRUCTURA PRINCIPAL DE LA INTERFAZ
# Se define el título y se instancian las pestañas de navegación principales.
# =============================================================================
st.title("Vigilancia de Urgencia Respiratoria")
st.markdown("**Servicio de Salud Talcahuano** | Unidad de Análisis de Datos")
st.markdown("---")

tabs = st.tabs([
    "Inicio: Exploración", 
    "Nivel 1: Visión Estratégica", 
    "Análisis P-Score (Exceso)",   
    "Tendencias Suavizadas",       
    "Nivel 2A: Gestión Global", 
    "Nivel 2B: Detalle Comunal", 
    "Nivel 3: Priorización Territorial",
    "Predicción (R. Armónica)",
    "Predicción por Causas"
])

# =============================================================================
# TAB 1: INICIO (EXPLORATORIO Y ACTUALIZADOR AUTOMÁTICO)
# Esta pestaña es el "Control Room". Muestra los Top 10 actuales y 
# contiene los botones para descargar el dataset semanal (todos los miercoles) y genera la actualizacion de datos.
# La descarga del dataset genera un documento temporal y reemplaza automaticamente el de la semana anterior
# =============================================================================
# Importamos el módulo personalizado que maneja las descargas silenciosas
import actualizador_sadu

with tabs[0]:
    col_titulo, col_btns = st.columns([2, 1])
    
    with col_titulo:
        st.header("Panorama General")
        st.markdown("Resumen de cargas máximas y rankings actuales.")
        
    with col_btns:
        st.write("")
        btn1, btn2 = st.columns(2)
        
        # Botón 1: Descarga el archivo Raw desde Datos Abiertos
        with btn1:
            if st.button("📥 1. Bajar Raw", use_container_width=True, help="Descarga el último archivo Parquet desde Datos.gob.cl"):
                with st.spinner("Descargando, el reemplazo es automatico..."):
                    exito, mensaje = actualizador_sadu.descargar_y_guardar_dataset()
                    if exito:
                        st.toast(mensaje, icon="✅")
                    else:
                        st.error(mensaje)
                        
        # Botón 2: Ejecuta el script de Python externo para cruzar SADU x INE
        with btn2:
            if st.button("⚙️ 2. Procesar", use_container_width=True, help="Ejecuta el pipeline de limpieza y cruce con INE"):
                with st.spinner("Procesando millones de filas. Esto puede tomar unos segundos..."):
                    exito, mensaje = actualizador_sadu.ejecutar_pipeline_limpieza()
                    if exito:
                        st.toast(mensaje, icon="✅")
                        st.cache_data.clear() # CRÍTICO: Obliga al dashboard a recargar el archivo nuevo
                        st.rerun() # Fuerza la recarga de la página web
                    else:
                        st.error(mensaje)
                        
    st.markdown("---")

    # Controles de filtrado generales para el análisis de Tops
    with st.container():
        c1, c2 = st.columns(2)
        t1_anio = c1.selectbox("Año de Análisis", ANIOS_DISPONIBLES, index=0, key="t1_y")
        t1_semanas = c2.slider("Ventana de Semanas", 1, 53, (1, 52), key="t1_w")

    # Filtrado del dataframe base
    mask_t1 = (df_full['Anio'] == t1_anio) & \
              (df_full['SemanaEstadistica'] >= t1_semanas[0]) & \
              (df_full['SemanaEstadistica'] <= t1_semanas[1])
    df_t1 = df_full[mask_t1]

    if df_t1.empty:
        st.warning("No hay datos para la selección.")
    else:
        # Renderizado de gráficos de barras simples (Altair) para Comunas, Causas y Centros
        c_left, c_right = st.columns(2)

        # =========================================================================
        # SECCIÓN DE GRÁFICOS EXPLORATORIOS (TOP RANKINGS)
        # Renderiza tres gráficos de barras horizontales para mostrar rápidamente
        # los principales focos de presión asistencial (dónde y por qué).
        # Se usan dos columnas superiores (Comunas y Causas) y una fila inferior (Centros).
        # =========================================================================

        with c_left:
            st.subheader("Top Comunas (Carga Promedio)")
            # CÁLCULO: Agrupa los datos filtrados por Comuna y calcula la Tasa media
            # en el periodo seleccionado. Luego, ordena de mayor a menor.
            top_com = df_t1.groupby('ComunaGlosa')['Tasa'].mean().reset_index().sort_values('Tasa', ascending=False)
            # GRÁFICO: Barra horizontal monocromática.
            # sort='-x' ordena las barras dinámicamente de mayor a menor en el eje Y.
            chart_com = alt.Chart(top_com).mark_bar().encode(
                x=alt.X('Tasa:Q', title='Tasa Promedio x 10k'),
                y=alt.Y('ComunaGlosa:N', sort='-x', title='Comuna'),
                color=alt.value('#102a43'),
                tooltip=['ComunaGlosa', alt.Tooltip('Tasa:Q', format='.2f')]
            ).properties(height=250)
            st.altair_chart(chart_com, use_container_width=True)

        with c_right:
            st.subheader("Top Causas (Prevalencia)")
            # CÁLCULO: Agrupa por diagnóstico (Causa), calcula la tasa media, 
            # ordena de mayor a menor y extrae SOLO las 5 causas principales (.head(5)).
            top_causa = df_t1.groupby('Causa')['Tasa'].mean().reset_index().sort_values('Tasa', ascending=False).head(5)
            # GRÁFICO: Barra horizontal. Se oculta el título del eje Y (title=None)
            # para ahorrar espacio, ya que los nombres de los diagnósticos suelen ser largos.
            chart_causa = alt.Chart(top_causa).mark_bar().encode(
                x=alt.X('Tasa:Q', title='Tasa Promedio x 10k'),
                y=alt.Y('Causa:N', sort='-x', title=None),
                color=alt.value('#334e68'),
                tooltip=['Causa', alt.Tooltip('Tasa:Q', format='.2f')]
            ).properties(height=250)
            st.altair_chart(chart_causa, use_container_width=True)
            
            # =========================================================================
        # GRÁFICO INFERIOR: TOP 10 ESTABLECIMIENTOS MÁS ESTRESADOS
        # =========================================================================

        st.subheader("Establecimientos con Mayor Carga (Top 10)")
    
    # CÁLCULO: Agrupa a nivel de Centro (manteniendo la Comuna para la leyenda),
        # calcula la tasa media, ordena y extrae los 10 centros con mayor presión de toda la red.

        top_est = df_t1.groupby(['ComunaGlosa', 'EstablecimientoGlosa'])['Tasa'].mean().reset_index().sort_values('Tasa', ascending=False).head(10)

# GRÁFICO: Barra horizontal categorizada.
        # A diferencia de los gráficos anteriores, aquí el color NO es fijo, sino que
        # se codifica ('encode') según la Comuna (color=alt.Color(...)). Esto permite 
        # ver visualmente si los top 10 centros pertenecen a la misma comuna o están distribuidos.

        chart_est = alt.Chart(top_est).mark_bar().encode(
            x=alt.X('Tasa:Q', title='Tasa Promedio'),
            y=alt.Y('EstablecimientoGlosa:N', sort='-x', title='Establecimiento'),
            color=alt.Color('ComunaGlosa:N', title='Comuna'),
            tooltip=['EstablecimientoGlosa', 'ComunaGlosa', alt.Tooltip('Tasa:Q', format='.2f')]
        ).properties(height=400)
        st.altair_chart(chart_est, use_container_width=True)

# =============================================================================
# TAB 2: NIVEL 1 - VISIÓN ESTRATÉGICA (CANAL ENDÉMICO)
# Construye un canal epidemiológico clásico comparando tasas actuales 
# contra cuartiles históricos prepandemia (2014-2019).
# =============================================================================
global_df_viz = None
global_anio_evaluar = None

with tabs[1]:
    st.header("Nivel 1: Visión Estratégica (Canal Endémico)")
    st.markdown("**Objetivo:** Monitoreo de la presión asistencial respecto a la normalidad histórica (2014-2019).")

    # 1. AISLAR HISTORIA PREPANDEMIA
    mask_base = (df_full['Anio'] >= 2014) & (df_full['Anio'] <= 2019)
    df_hist = df_full[mask_base].copy()

    if df_hist.empty:
        st.error("Error: Faltan datos históricos 2014-2019.")
    else:
        # Agrupación por semana y cálculo de la Tasa Bruta
        rates_hist = df_hist.groupby(['Anio', 'SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
        rates_hist['Tasa'] = (rates_hist['Atenciones'] / rates_hist['Poblacion'].replace(0, np.nan)) * 10000
        
        # Cálculo de los cuartiles epidemiológicos (Q1: Éxito, Q2: Seguridad, Q3: Alarma)
        canal_stats = rates_hist.groupby('SemanaEstadistica')['Tasa'].quantile([0.25, 0.50, 0.75]).unstack()
        canal_stats.columns = ['Q1', 'Q2', 'Q3']
        canal_stats = canal_stats.reset_index()

        # Interpolación lineal para asegurar que las 53 semanas tengan un valor base
        all_weeks = pd.DataFrame({'SemanaEstadistica': range(1, 54)})
        canal_final = pd.merge(all_weeks, canal_stats, on='SemanaEstadistica', how='left').interpolate(method='linear')

        col_main_graph, col_sidebar_tools = st.columns([3, 1.2], gap="large")

        # --- SECCIÓN DERECHA: TARJETAS MÉTRICAS Y LÓGICA CLÍNICA ---
        with col_sidebar_tools:
            st.markdown("### Configuración")
            anio_evaluar = st.selectbox("Año a Evaluar", ANIOS_DISPONIBLES, index=0, key="ce_year_v7")
            global_anio_evaluar = anio_evaluar 
            
            # Leyenda HTML pura
            st.markdown("""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #dcdcdc; color: #333333; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="margin-bottom:10px; font-weight:bold; font-size: 0.9rem; border-bottom: 1px solid #eee; padding-bottom: 5px;">ZONAS EPIDEMIOLÓGICAS:</div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:0.8rem;">
                    <span style="color:#2ca02c; font-size:1.4em;">■</span> <div><b>Éxito</b><br><span style="color:#666;">Bajo Q1 (25% inf.)</span></div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:0.8rem;">
                    <span style="color:#eeee00; font-size:1.4em;">■</span> <div><b>Seguridad</b><br><span style="color:#666;">Entre Q1 y Q2</span></div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:0.8rem;">
                    <span style="color:#ff7f0e; font-size:1.4em;">■</span> <div><b>Alarma</b><br><span style="color:#666;">Entre Q2 y Q3</span></div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; font-size:0.8rem;">
                    <span style="color:#d62728; font-size:1.4em;">■</span> <div><b>Epidemia</b><br><span style="color:#666;">Sobre Q3 (Exceso)</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Cálculo de la Tasa Real del Año Seleccionado
            df_actual = df_full[df_full['Anio'] == anio_evaluar].copy()
            max_sem = 1
            df_viz = canal_final.copy()
            df_viz['TasaActual'] = None

            if not df_actual.empty:
                act_rates = df_actual.groupby(['SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
                act_rates['TasaActual'] = (act_rates['Atenciones'] / act_rates['Poblacion'].replace(0, np.nan)) * 10000
                
                # Cruce de la tasa actual contra el canal endémico histórico
                df_viz = pd.merge(canal_final, act_rates[['SemanaEstadistica', 'TasaActual']], on='SemanaEstadistica', how='left')
                global_df_viz = df_viz 
                
                valid_sems = act_rates.dropna(subset=['TasaActual'])
                if not valid_sems.empty:
                    max_sem = int(valid_sems['SemanaEstadistica'].max())

            st.markdown("---")
            st.markdown("### Diagnóstico Semanal")
            sem_sel = st.slider("Seleccionar Semana:", 1, 53, max_sem)

            # LÓGICA IF-ELSE: Compara el valor actual vs el canal para determinar el estado de riesgo
            row = df_viz[df_viz['SemanaEstadistica'] == sem_sel]
            if not row.empty and pd.notnull(row.iloc[0]['TasaActual']):
                val = row.iloc[0]['TasaActual']
                q1, q2, q3 = row.iloc[0]['Q1'], row.iloc[0]['Q2'], row.iloc[0]['Q3']
                
                row_prev = df_viz[df_viz['SemanaEstadistica'] == sem_sel - 1]
                trend_icon = "➖"
                if not row_prev.empty and pd.notnull(row_prev.iloc[0]['TasaActual']):
                    val_prev = row_prev.iloc[0]['TasaActual']
                    if val > val_prev: trend_icon = "📈 Alza"
                    elif val < val_prev: trend_icon = "📉 Baja"

                if val < q1:
                    st_color, st_txt = "#2ca02c", "ÉXITO"
                    insight_txt = "Demanda inferior al histórico. Situación bajo control."
                    accion_txt = "Mantener vigilancia basal."
                elif val < q2:
                    st_color, st_txt = "#d4c800", "SEGURIDAD"
                    insight_txt = "Comportamiento normal (bajo la mediana)."
                    accion_txt = "Vigilancia estándar."
                elif val < q3:
                    st_color, st_txt = "#ff7f0e", "ALARMA"
                    insight_txt = f"Se superó la mediana (Q2={q2:.1f}). Inicio de tensión."
                    accion_txt = "Alerta preventiva a la red."
                else:
                    st_color, st_txt = "#d62728", "EPIDEMIA"
                    insight_txt = f"Exceso de demanda. Se supera el umbral crítico (Q3={q3:.1f})."
                    accion_txt = "Activar Plan de Contingencia."

                # Tarjeta dinámica en HTML basada en el estado calculado
                st.markdown(f"""
                <div style="border: 1px solid #ccc; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-top:10px;">
                    <div style="background:{st_color}; color:white; padding: 12px; text-align:center; font-weight:bold; letter-spacing: 1px; font-size: 1.1rem;">
                        {st_txt}
                    </div>
                    <div style="padding: 15px; color: #333;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:10px;">
                            <div><span style="font-size:0.75rem; color:#666; font-weight:bold;">TASA REAL</span><br><span style="font-size:1.8rem; font-weight:800; color:#222;">{val:.2f}</span></div>
                            <div style="text-align:right;"><span style="font-size:0.75rem; color:#666; font-weight:bold;">UMBRAL Q3</span><br><span style="font-size:1.2rem; font-weight:600; color:#555;">{q3:.2f}</span></div>
                        </div>
                        <div style="background-color:#f4f4f4; padding:10px; border-radius:6px; font-size:0.85rem; margin-bottom:10px;">
                            <b>Tendencia:</b> {trend_icon} <br>
                            <b>Estado:</b> {insight_txt}
                        </div>
                        <div style="font-size:0.85rem; color:#333; font-weight:500; border-left:3px solid {st_color}; padding-left:8px;">
                            🛡️ <b>Acción:</b> {accion_txt}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Sin datos para esta semana.")

        # --- SECCIÓN IZQUIERDA: GRÁFICO DE ÁREAS (ALTAIR) ---
        with col_main_graph:
            st.subheader(f"Curva de Tendencia {anio_evaluar}")
            
            # Dinamismo de Ejes Y
            max_q3 = df_viz['Q3'].max() if not df_viz['Q3'].isna().all() else 10
            max_act = df_viz['TasaActual'].max() if 'TasaActual' in df_viz and not df_viz['TasaActual'].isna().all() else 0
            ymax = max(max_q3, max_act) * 1.25
            
            df_viz['Techo'] = ymax
            df_viz['Piso'] = 0
            rule_df = pd.DataFrame({'SemanaEstadistica': [sem_sel]})

            # Gráfico Base y Generación de Áreas de Colores
            base = alt.Chart(df_viz).encode(x=alt.X('SemanaEstadistica:Q', title='Semana Epidemiológica (1-53)'))

            areas = (
                base.mark_area(color='#2ca02c', opacity=0.3).encode(y='Piso:Q', y2='Q1:Q', tooltip=alt.value(None)) +
                base.mark_area(color='#eeee00', opacity=0.3).encode(y='Q1:Q', y2='Q2:Q', tooltip=alt.value(None)) +
                base.mark_area(color='#ff7f0e', opacity=0.3).encode(y='Q2:Q', y2='Q3:Q', tooltip=alt.value(None)) +
                base.mark_area(color='#d62728', opacity=0.3).encode(y='Q3:Q', y2='Techo:Q', tooltip=alt.value(None))
            )

            # Interactividad: Regla vertical móvil en Altair
            nearest = alt.selection_point(nearest=True, on='mouseover', fields=['SemanaEstadistica'], empty=False)
            linea = base.mark_line(color='#102a43', strokeWidth=3).encode(y=alt.Y('TasaActual:Q', title='Tasa x 10.000 hab'))
            selectors = base.mark_point().encode(x='SemanaEstadistica:Q', opacity=alt.value(0)).add_params(nearest)
            
            points = base.mark_circle(size=80, color='#102a43').encode(
                y='TasaActual:Q', opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
                tooltip=[alt.Tooltip('SemanaEstadistica', title='Semana'), alt.Tooltip('TasaActual', title='Tasa', format='.2f')]
            )
            text = base.mark_text(align='left', dx=5, dy=-5, fontWeight='bold', color='#102a43').encode(
                y='TasaActual:Q', text=alt.condition(nearest, alt.Text('TasaActual:Q', format='.2f'), alt.value(' '))
            )

            slider_rule = alt.Chart(rule_df).mark_rule(color='gray', strokeDash=[4, 4], size=2).encode(x='SemanaEstadistica:Q')
            hover_rule = base.mark_rule(color='#ccc').encode(x='SemanaEstadistica:Q', opacity=alt.condition(nearest, alt.value(1), alt.value(0)))

            chart_final = (areas + slider_rule + hover_rule + linea + selectors + points + text).properties(
                height=550, title="Canal Endémico (Interactivo)"
            )

            st.altair_chart(chart_final, use_container_width=True)
            st.caption("💡 El área sombreada es la normalidad (2014-2019). La línea punteada indica la semana seleccionada en el panel derecho.")

# =============================================================================
# TAB 3: ANÁLISIS P-SCORE
# Calcula matemáticamente el porcentaje de desviación de las atenciones actuales
# versus la mediana esperada (Q2).
# =============================================================================
with tabs[2]:
    st.header("Análisis de Exceso (P-Score)")
    st.markdown("**Objetivo:** Cuantificar el porcentaje de exceso de demanda respecto a la mediana histórica específica.")
    
    c_scope, c_yr = st.columns([2, 1])
    with c_scope:
        opciones_alcance = ["Global (Toda la Red)"] + sorted(df_full['ComunaGlosa'].unique())
        alcance_sel = st.selectbox("Seleccione Alcance Territorial:", opciones_alcance, index=0, key="pscore_scope")
    with c_yr:
        anio_p = st.selectbox("Año a Analizar:", ANIOS_DISPONIBLES, index=0, key="pscore_year")

    # Adaptación del Dataframe según filtro territorial
    if alcance_sel == "Global (Toda la Red)":
        df_scope = df_full.copy()
        titulo_chart = f"P-Score Global - Servicio de Salud ({anio_p})"
    else:
        df_scope = df_full[df_full['ComunaGlosa'] == alcance_sel].copy()
        titulo_chart = f"P-Score Comunal - {alcance_sel} ({anio_p})"

    if df_scope.empty:
        st.warning(f"No hay datos disponibles para {alcance_sel}.")
    else:
        mask_h = df_scope['Anio'].between(2014, 2019)
        df_h_sc = df_scope[mask_h]
        
        if df_h_sc.empty:
            st.error("No hay historia 2014-2019 para este alcance. No se puede calcular P-Score.")
        else:
            # 1. Calcular Baseline (Mediana Histórica)
            rh = df_h_sc.groupby(['Anio', 'SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
            rh['Tasa'] = (rh['Atenciones'] / rh['Poblacion'].replace(0, np.nan)) * 10000
            baseline = rh.groupby('SemanaEstadistica')['Tasa'].median().reset_index()
            baseline.columns = ['SemanaEstadistica', 'Q2_Hist']

            # 2. Calcular Datos Actuales
            df_act_sc = df_scope[df_scope['Anio'] == anio_p]
            
            if df_act_sc.empty:
                st.warning(f"No hay datos para el año {anio_p} en la selección.")
            else:
                curr = df_act_sc.groupby('SemanaEstadistica')[['Atenciones', 'Poblacion']].sum().reset_index()
                curr['TasaActual'] = (curr['Atenciones'] / curr['Poblacion'].replace(0, np.nan)) * 10000
                
                # 3. FÓRMULA DEL P-SCORE: ((Actual - Esperado) / Esperado) * 100
                df_final_p = pd.merge(baseline, curr[['SemanaEstadistica', 'TasaActual']], on='SemanaEstadistica', how='left')
                df_final_p['P_Score'] = ((df_final_p['TasaActual'] - df_final_p['Q2_Hist']) / df_final_p['Q2_Hist']) * 100
                df_final_p['Tipo'] = np.where(df_final_p['P_Score'] > 0, 'Exceso (+)', 'Déficit (-)')
                
                col_graph, col_insights = st.columns([3, 1.2])
                
                with col_graph:
                    chart_p = alt.Chart(df_final_p).mark_bar().encode(
                        x=alt.X('SemanaEstadistica:Q', title='Semana Epidemiológica'),
                        y=alt.Y('P_Score:Q', title='% Exceso sobre Mediana'),
                        color=alt.Color('Tipo', 
                                        scale=alt.Scale(domain=['Exceso (+)', 'Déficit (-)'], range=['#d62728', '#2ca02c']),
                                        legend=alt.Legend(title="Situación")),
                        tooltip=[
                            alt.Tooltip('SemanaEstadistica', title='Semana'),
                            alt.Tooltip('P_Score', title='P-Score (%)', format='.1f'),
                            alt.Tooltip('TasaActual', title='Tasa Real', format='.2f'),
                            alt.Tooltip('Q2_Hist', title='Esperado', format='.2f')
                        ]
                    ).properties(height=400, title=titulo_chart)
                    
                    rule = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='black').encode(y='y')
                    st.altair_chart(chart_p + rule, use_container_width=True)

                with col_insights:
                    st.markdown("#### 📊 Diagnóstico")
                    valid_data = df_final_p.dropna(subset=['P_Score'])
                    
                    if not valid_data.empty:
                        # Extraer máximos y promedios para métricas
                        max_excess = valid_data['P_Score'].max()
                        wk_max = valid_data.loc[valid_data['P_Score'].idxmax(), 'SemanaEstadistica']
                        excess_vals = valid_data[valid_data['P_Score'] > 0]['P_Score']
                        avg_excess = excess_vals.mean() if not excess_vals.empty else 0.0
                        
                        if max_excess > 50: 
                            status_msg, bg_color, border_color = "⚠️ ALERTA CRÍTICA: Sobrecarga Severa", "#ffebee", "#d32f2f"
                        elif max_excess > 20: 
                            status_msg, bg_color, border_color = "🔸 PRECAUCIÓN: Sobrecarga Moderada", "#fff3e0", "#f57c00"
                        elif max_excess > 0:
                            status_msg, bg_color, border_color = "🔹 ATENCIÓN: Leve aumento", "#e3f2fd", "#1976d2"
                        else: 
                            status_msg, bg_color, border_color = "✅ NORMALIDAD: Holgura total", "#e8f5e9", "#388e3c"

                        st.markdown(f"""
                        <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; color: black;">
                            <div style="font-size: 0.9em; font-weight: bold; color: #555; margin-bottom: 5px;">PEAK DE SOBRECARGA</div>
                            <div style="font-size: 2em; font-weight: bold; color: black; line-height: 1;">{max_excess:+.1f}%</div>
                            <div style="font-size: 0.9em; color: #666;">Semana {int(wk_max)}</div>
                            <hr style="margin: 15px 0; border-top: 1px solid #eee;">
                            <div style="font-size: 0.9em; font-weight: bold; color: #555; margin-bottom: 5px;">PROMEDIO EN ALZA</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: black; line-height: 1;">{avg_excess:+.1f}%</div>
                            <div style="font-size: 0.9em; color: #666;">sobre la mediana</div>
                            <div style="margin-top: 20px; background-color: {bg_color}; padding: 10px; border-radius: 5px; border-left: 5px solid {border_color}; color: black;">
                                <strong>{status_msg}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                            
                    else:
                        st.info("Seleccione un año con datos para ver el diagnóstico.")

# =============================================================================
# TAB 4: TENDENCIAS SUAVIZADAS
# Aplica un algoritmo de Media Móvil (Moving Average) a la tasa bruta
# para eliminar la volatilidad estadística entre semanas consecutivas,
# revelando la verdadera dirección de la curva epidémica.
# =============================================================================
with tabs[3]:
    st.header("Tendencias Suavizadas")
    st.markdown("**Objetivo:** Eliminar el ruido semanal para visualizar la verdadera curva epidémica, permitiendo aislar por territorio.")
    
# Layout asimétrico: 1 parte para controles (izq), 3 partes para el gráfico (der)
    col_suav_1, col_suav_2 = st.columns([1, 3])
    
    # --- 1. PANEL DE FILTROS Y CONTROLES ---
    with col_suav_1:
        st.markdown("### Filtros")
        # Selector de alcance: Permite ver toda la red o hacer drill-down a una comuna específica
        opciones_alcance_ts = ["Global (Toda la Red)"] + sorted(df_full['ComunaGlosa'].unique())
        ts_alcance = st.selectbox("Alcance:", opciones_alcance_ts, index=0, key="ts_scope")
        ts_anio = st.selectbox("Año a Analizar:", ANIOS_DISPONIBLES, key="ts_anio")
        st.divider()
        
        # Control del algoritmo: El usuario define la "ventana" de suavizado.
        # A mayor número, más plana la curva (menor varianza).
        ventana = st.slider("Nivel de Suavizado (Semanas)", 2, 8, 4, help="Mayor número = Curva más suave pero menos sensible a cambios rápidos.")
        st.caption(f"Aplicando Media Móvil de {ventana} semanas.")

    # --- 2. FILTRADO DE DATOS (SEGÚN ALCANCE TERRITORIAL Y AÑO) ---
    if ts_alcance == "Global (Toda la Red)":
        df_scope_ts = df_full.copy()
        titulo_ts = f"Tendencia Global ({ts_anio})"
    else:
        df_scope_ts = df_full[df_full['ComunaGlosa'] == ts_alcance].copy()
        titulo_ts = f"Tendencia {ts_alcance} ({ts_anio})"

    df_ts = df_scope_ts[df_scope_ts['Anio'] == ts_anio].copy()
    
    if df_ts.empty:
        with col_suav_2:
            st.warning(f"No hay datos para {ts_alcance} en el año {ts_anio}.")
    else:
        # --- 3. CÁLCULOS ESTADÍSTICOS ---
        # 3.1. Tasa Cruda: Se agrupa por semana para obtener el volumen real.
        ts_rates = df_ts.groupby(['SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
        ts_rates['Tasa_Cruda'] = (ts_rates['Atenciones'] / ts_rates['Poblacion'].replace(0, np.nan)) * 10000
        
        # 3.2. Tasa Suavizada (Media Móvil):
        # rolling(window=ventana) toma las 'n' semanas anteriores.
        # center=True ubica el promedio en el centro de la ventana temporal,
        # evitando que la curva suavizada se desplace hacia la derecha respecto a los datos reales.
        ts_rates['Tasa_Suavizada'] = ts_rates['Tasa_Cruda'].rolling(window=ventana, center=True).mean()
        
        # 3.3. Transformación Estructural (Melt):
        # Altair requiere datos en formato "largo" (tidy data) para graficar múltiples series.
        # Convertimos las columnas 'Tasa_Cruda' y 'Tasa_Suavizada' en filas categóricas bajo la columna 'Tipo'.
        df_melt_ts = ts_rates.melt(id_vars=['SemanaEstadistica'], value_vars=['Tasa_Cruda', 'Tasa_Suavizada'], var_name='Tipo', value_name='Tasa')
        
        # --- 4. VISUALIZACIÓN MULTICAPA CON ALTAIR ---
        with col_suav_2:
            # Gráfico base definiendo el eje X compartido
            base_ts = alt.Chart(df_melt_ts).encode(x=alt.X('SemanaEstadistica:Q', title='Semana Epidemiológica'))
            # Capa 1: Línea Cruda (Gris, punteada). Muestra la volatilidad real.
            line_raw = base_ts.transform_filter(alt.datum.Tipo == 'Tasa_Cruda').mark_line(
                color='#999', strokeDash=[4,2], size=2, opacity=0.6
            ).encode(y=alt.Y('Tasa:Q', title='Tasa x 10.000 hab'))
            
            # Capa 2: Puntos Crudos (Gris). Permite hacer hover exacto sobre el dato real.
            points_raw = base_ts.transform_filter(alt.datum.Tipo == 'Tasa_Cruda').mark_circle(color='#999', size=30, opacity=0.6).encode(
                y='Tasa:Q', tooltip=[alt.Tooltip('SemanaEstadistica', title='Semana'), alt.Tooltip('Tasa', title='Tasa Real', format='.2f')]
            )
            
            # Capa 3: Línea Suavizada (Azul, sólida). Destaca la tendencia de la enfermedad.
            line_smooth = base_ts.transform_filter(alt.datum.Tipo == 'Tasa_Suavizada').mark_line(color='#1f77b4', size=4).encode(
                y='Tasa:Q', tooltip=[alt.Tooltip('SemanaEstadistica', title='Semana'), alt.Tooltip('Tasa', title='Tendencia Suavizada', format='.2f')]
            )
            
            # Ensamblaje final de las capas y renderizado
            chart_ts = (line_raw + points_raw + line_smooth).properties(height=450, title=f"{titulo_ts} - Suavizado {ventana} Semanas")
            st.altair_chart(chart_ts, use_container_width=True)
            st.info(f"**Interpretación:** La línea gris muestra los datos reales (con saltos). La línea azul muestra la dirección real del brote en **{ts_alcance}**, ignorando el ruido diario.")

# =============================================================================
# TABS 5, 6 y 7: ANÁLISIS DESCRIPTIVO (Gestión, Comunas, Priorización)
# Agrupaciones estándar para ver las distribuciones en barras y tortas
# =============================================================================

with tabs[4]: # NIVEL 2A
    st.header("Nivel 2A: Gestión Operativa de la Red")
    st.markdown("""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:5px; border-left:5px solid #102a43; margin-bottom:20px; color: #000;">
        <strong>Objetivo Estratégico:</strong> Identifición de nodos críticos según territorio y grupos de riesgo.
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        c_filt1, c_filt2, c_filt3, c_filt4 = st.columns(4)
        t3_anio = c_filt1.selectbox("Año", ANIOS_DISPONIBLES, key="t3_y")
        opciones_comuna = ["Global (Toda la Red)"] + sorted(df_full['ComunaGlosa'].unique())
        t3_comuna = c_filt2.selectbox("Territorio", opciones_comuna, key="t3_c")
        opciones_edad = ["Todos los Grupos"] + sorted(df_full['grupo_etario'].unique())
        t3_edad = c_filt3.selectbox("Grupo Etario Objetivo", opciones_edad, key="t3_e")
        t3_sem = st.slider("Ventana de Tiempo (Semanas)", 1, 53, (1, 52), key="t3_w")

    mask_t3 = (df_full['Anio'] == t3_anio) & (df_full['SemanaEstadistica'].between(t3_sem[0], t3_sem[1]))
    df_t3 = df_full[mask_t3].copy()
    if t3_comuna != "Global (Toda la Red)": df_t3 = df_t3[df_t3['ComunaGlosa'] == t3_comuna]
    if t3_edad != "Todos los Grupos": df_t3 = df_t3[df_t3['grupo_etario'] == t3_edad]

    if df_t3.empty:
        st.warning("No hay registros que coincidan con todos los filtros seleccionados.")
    else:
        total_atenciones = df_t3['Atenciones'].sum()
        vol_hosp = df_t3[df_t3['NivelGestion'] == 'Atención Hospitalaria']['Atenciones'].sum()
        vol_aps = df_t3[df_t3['NivelGestion'] == 'Atención Primaria Urgencia']['Atenciones'].sum()
        
        # Dashboard de métricas superiores
        kpi_html = f"""
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center;">
                <div style="font-size: 0.9em; color: #555; font-weight: bold;">TOTAL ATENCIONES</div>
                <div style="font-size: 2em; color: #102a43; font-weight: 800;">{total_atenciones:,.0f}</div>
            </div>
            <div style="flex: 1; background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center;">
                <div style="font-size: 0.9em; color: #555; font-weight: bold;">HOSPITAL</div>
                <div style="font-size: 2em; color: #d62728; font-weight: 800;">{vol_hosp:,.0f}</div>
                <div style="font-size: 0.8em; color: #666;">{(vol_hosp/total_atenciones)*100:.1f}%</div>
            </div>
            <div style="flex: 1; background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; text-align: center;">
                <div style="font-size: 0.9em; color: #555; font-weight: bold;">APS (SAPU/SAR)</div>
                <div style="font-size: 2em; color: #2ca02c; font-weight: 800;">{vol_aps:,.0f}</div>
                <div style="font-size: 0.8em; color: #666;">{(vol_aps/total_atenciones)*100:.1f}%</div>
            </div>
        </div>
        """
        st.markdown(kpi_html, unsafe_allow_html=True)

        st.subheader(f"1. Tendencia de Demanda: {t3_comuna}")
        df_trend = df_t3.groupby(['SemanaEstadistica', 'NivelGestion'])['Tasa'].mean().reset_index()
        chart_trend = alt.Chart(df_trend).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X('SemanaEstadistica:Q', title='Semana'),
            y=alt.Y('Tasa:Q', title='Tasa Promedio x 10k'),
            color=alt.Color('NivelGestion:N', title='Nivel', scale=alt.Scale(scheme='category10')),
            tooltip=['SemanaEstadistica', 'NivelGestion', alt.Tooltip('Tasa', format='.2f')]
        ).properties(height=350, title="Evolución temporal por nivel")
        st.altair_chart(chart_trend, use_container_width=True)

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 2. Perfil del Paciente")
            if t3_edad != "Todos los Grupos":
                st.info(f"Filtro activo: **{t3_edad}**. Mostrando Centros.")
                df_who = df_t3.groupby(['EstablecimientoGlosa', 'NivelGestion'])['Atenciones'].sum().reset_index().sort_values('Atenciones', ascending=False).head(10)
                chart_who = alt.Chart(df_who).mark_bar().encode(
                    x=alt.X('Atenciones:Q', title='Total Atenciones'),
                    y=alt.Y('EstablecimientoGlosa:N', sort='-x', title='Centro'),
                    color='NivelGestion:N', tooltip=['EstablecimientoGlosa', 'Atenciones']
                ).properties(height=350)
            else:
                df_who = df_t3.groupby(['grupo_etario', 'NivelGestion'])['Tasa'].mean().reset_index()
                chart_who = alt.Chart(df_who).mark_bar().encode(
                    x=alt.X('Tasa:Q', title='Tasa Promedio'),
                    y=alt.Y('grupo_etario:N', title='Grupo Etario'),
                    color='NivelGestion:N', tooltip=['grupo_etario', 'Tasa']
                ).properties(height=350)
            st.altair_chart(chart_who, use_container_width=True)

        with c_right:
            st.markdown("#### 3. Perfil Clínico (Causas)")
            df_why = df_t3.groupby(['Causa', 'NivelGestion'])['Atenciones'].sum().reset_index()
            top_causes = df_why.groupby('Causa')['Atenciones'].sum().nlargest(5).index.tolist()
            df_why = df_why[df_why['Causa'].isin(top_causes)]
            chart_why = alt.Chart(df_why).mark_bar().encode(
                x=alt.X('Atenciones:Q', title='Total Atenciones'),
                y=alt.Y('Causa:N', sort='-x', title='Diagnóstico'),
                color='NivelGestion:N', tooltip=['Causa', 'Atenciones']
            ).properties(height=350)
            st.altair_chart(chart_why, use_container_width=True)

        # Insights Automatizados
        st.markdown("### Insights")
        top_c = df_t3.groupby('Causa')['Atenciones'].sum().idxmax()
        val_c = df_t3.groupby('Causa')['Atenciones'].sum().max()
        pct_c = (val_c / total_atenciones) * 100
        
        if t3_edad == "Todos los Grupos":
            top_e = df_t3.groupby('grupo_etario')['Tasa'].mean().idxmax()
            msg_edad = f"El grupo etario con mayor tasa de consulta es <b>{top_e}</b>."
        else:
            msg_edad = f"Análisis enfocado exclusivamente en el grupo <b>{t3_edad}</b>."

        insight_html = f"""
        <div style="background-color: #e3f2fd; border: 1px solid #90caf9; border-left: 6px solid #1976d2; border-radius: 8px; padding: 20px; color: #0d47a1; font-family: sans-serif; margin-top: 10px;">
            <h4 style="margin-top: 0; color: #0d47a1;">Conclusiones</h4>
            <ul style="margin-bottom: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;"><strong>Diagnóstico Predominante:</strong> La principal causa es <b>{top_c}</b>, representando el <b>{pct_c:.1f}%</b> de la demanda analizada.</li>
                <li style="margin-bottom: 8px;"><strong>Foco Demográfico:</strong> {msg_edad}</li>
                <li><strong>Carga Asistencial:</strong> Se registraron un total de <b>{total_atenciones:,.0f}</b> atenciones en el periodo seleccionado.</li>
            </ul>
        </div>
        """
        st.markdown(insight_html, unsafe_allow_html=True)

with tabs[5]: # NIVEL 2B
    st.header("Nivel 2B: Detalle Comunal de Centros")
    st.markdown("**Foco Local:** Análisis de carga específica por establecimiento dentro de cada comuna.")
    c1, c2, c3 = st.columns(3)
    t2b_anio = c1.selectbox("Año", ANIOS_DISPONIBLES, key="t2b_y")
    t2b_comuna = c2.selectbox("Seleccionar Comuna", COMUNAS_DISPONIBLES, key="t2b_c")
    t2b_sem = c3.slider("Semanas", 1, 53, (1, 52), key="t2b_w")
    
    mask_2b = (df_full['Anio'] == t2b_anio) & (df_full['ComunaGlosa'] == t2b_comuna) & (df_full['SemanaEstadistica'] >= t2b_sem[0]) & (df_full['SemanaEstadistica'] <= t2b_sem[1])
    df_2b = df_full[mask_2b]
    
    if df_2b.empty:
        st.warning(f"No hay datos para {t2b_comuna} en el periodo seleccionado.")
    else:
        st.subheader(f"Ranking de Carga: Centros de {t2b_comuna}")
        rank_centros = df_2b.groupby(['EstablecimientoGlosa', 'NivelGestion'])['Tasa'].mean().reset_index().sort_values('Tasa', ascending=False)
        ch_rank = alt.Chart(rank_centros).mark_bar().encode(
            x=alt.X('Tasa:Q', title='Tasa Promedio x 10k'),
            y=alt.Y('EstablecimientoGlosa:N', sort='-x', title='Establecimiento'),
            color=alt.Color('NivelGestion:N', title='Tipo'),
            tooltip=['EstablecimientoGlosa', 'NivelGestion', alt.Tooltip('Tasa', format='.2f')]
        ).properties(height=400)
        st.altair_chart(ch_rank, use_container_width=True)
        
        st.subheader("Tendencia Semanal por Centro")
        trend_centros = df_2b.groupby(['SemanaEstadistica', 'EstablecimientoGlosa'])['Tasa'].mean().reset_index()
        ch_trend_c = alt.Chart(trend_centros).mark_line(point=True).encode(
            x=alt.X('SemanaEstadistica:Q', title='Semana'),
            y=alt.Y('Tasa:Q', title='Tasa'),
            color=alt.Color('EstablecimientoGlosa:N', title='Centro'),
            tooltip=['SemanaEstadistica', 'EstablecimientoGlosa', alt.Tooltip('Tasa', format='.2f')]
        ).properties(height=350)
        st.altair_chart(ch_trend_c, use_container_width=True)

with tabs[6]: # NIVEL 3
    st.header("Nivel 3: Priorización Territorial (Comunas)")
    st.markdown("**Objetivo:** Ranking de carga comunal.")

    c1, c2 = st.columns(2)
    t4_anio = c1.selectbox("Año", ANIOS_DISPONIBLES, key="t4_y")
    t4_semanas = c2.slider("Semanas", 1, 53, (1, 52), key="t4_w")

    mask_t4 = (df_full['Anio'] == t4_anio) & (df_full['SemanaEstadistica'] >= t4_semanas[0]) & (df_full['SemanaEstadistica'] <= t4_semanas[1])
    df_t4 = df_full[mask_t4]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ranking de Presión (Tasa)")
        df_rank = df_t4.groupby('ComunaGlosa')['Tasa'].mean().reset_index().sort_values('Tasa', ascending=False)
        chart_rank = alt.Chart(df_rank).mark_bar(color='#102a43').encode(
            x=alt.X('Tasa:Q', title='Tasa Promedio'), y=alt.Y('ComunaGlosa:N', sort='-x', title='Comuna'), tooltip=['ComunaGlosa', alt.Tooltip('Tasa', format='.2f')]
        ).properties(height=300)
        st.altair_chart(chart_rank, use_container_width=True)

    with col2:
        st.subheader("Volumen Relativo (% Participación)")
        df_vol = df_t4.groupby('ComunaGlosa')['Atenciones'].sum().reset_index()
        total_vol = df_vol['Atenciones'].sum()
        df_vol['Porcentaje'] = (df_vol['Atenciones'] / total_vol)
        chart_pie = alt.Chart(df_vol).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Atenciones", type="quantitative"), color=alt.Color(field="ComunaGlosa", type="nominal"), tooltip=['ComunaGlosa', alt.Tooltip('Atenciones', format=','), alt.Tooltip('Porcentaje', format='.1%')]
        ).properties(height=300)
        st.altair_chart(chart_pie, use_container_width=True)

    st.markdown("#### Evolución Temporal por Comuna")
    df_temp_com = df_t4.groupby(['SemanaEstadistica', 'ComunaGlosa'])['Tasa'].mean().reset_index()
    chart_evo = alt.Chart(df_temp_com).mark_line(point=True).encode(
        x='SemanaEstadistica:Q', y='Tasa:Q', color='ComunaGlosa:N', tooltip=['SemanaEstadistica', 'ComunaGlosa', 'Tasa']
    ).properties(height=350, width='container')
    st.altair_chart(chart_evo, use_container_width=True)

# =============================================================================
# TAB 8: PREDICCIÓN Y EVALUACIÓN (REGRESIÓN ARMÓNICA PONDERADA)
# Este bloque es el motor analítico del sistema. Utiliza Mínimos Cuadrados
# Ponderados (WLS) para ajustar una curva de senos y cosenos a los datos
# históricos, dándole más peso a los años post-pandemia para predecir el futuro.
# =============================================================================
with tabs[7]:
    st.header("Predicción y Evaluación Epidemiológica (Modelo Ponderado)")
    
    st.markdown("""
    <div style="background-color:#e3f2fd; padding:15px; border-radius:8px; border-left:6px solid #1976d2; margin-bottom:20px; color: #0d47a1; font-family: sans-serif;">
        <h4 style="margin-top: 0; color: #0d47a1;"> Lógica y Evaluación del Modelo Ponderado</h4>
        <ul style="margin-bottom: 0;">
            <li><b>Entrenamiento con Pesos:</b> Aprende la curva de los años prepandemia (Peso 1x), y le otorga pesos x5 a los años 2023+</li>
            <li><b>Umbral de Riesgo:</b> Se proyecta la tasa y se cruza con el <b>Límite Epidémico (Q3)</b> histórico.</li>
            <li><b>Evaluación:</b> <b>Error Absoluto (MAE) y Porcentual (MAPE)</b>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- 1. FILTROS ---
    with st.container():
        c_pred1, c_pred2 = st.columns(2)
        opciones_alcance_pred = ["Global (Toda la Red)"] + sorted(df_full['ComunaGlosa'].unique())
        pred_alcance = c_pred1.selectbox("Territorio a Predecir:", opciones_alcance_pred, key="pred_scope")
        
        anio_max = df_full['Anio'].max()
        opciones_anios_pred = [2026, 2025, 2024] 
        pred_anio = c_pred2.selectbox("Año Objetivo (Proyección):", opciones_anios_pred, index=0, key="pred_year")

    # --- 2. PREPARACIÓN DE DATOS (HÍBRIDO: HISTORIA + NUEVA NORMALIDAD) ---
    # EXCLUSIÓN ESTRICTA: Se borran los años 2020-2022 ya que la cuarentena y las
    # restricciones destruyeron el comportamiento estacional normal del virus.
    mask_train = (~df_full['Anio'].isin([2020, 2021, 2022])) & (df_full['Anio'] < pred_anio)
    
    if pred_alcance == "Global (Toda la Red)":
        df_hist_pred = df_full[mask_train].copy()
        df_real_eval = df_full[df_full['Anio'] == pred_anio].copy()
    else:
        df_hist_pred = df_full[mask_train & (df_full['ComunaGlosa'] == pred_alcance)].copy()
        df_real_eval = df_full[(df_full['Anio'] == pred_anio) & (df_full['ComunaGlosa'] == pred_alcance)].copy()

    if df_hist_pred.empty:
        st.warning("No hay suficiente historia para entrenar el modelo en este territorio.")
    else:
        # Agrupa la base de datos histórica validada
        hist_agrupado = df_hist_pred.groupby(['Anio', 'SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
        hist_agrupado['Tasa'] = (hist_agrupado['Atenciones'] / hist_agrupado['Poblacion'].replace(0, np.nan)) * 10000
        hist_agrupado = hist_agrupado.dropna(subset=['Tasa'])

        # Extrae el umbral de Epidemia Histórica (Q3) para compararlo en el gráfico final
        umbral_hist = hist_agrupado.groupby('SemanaEstadistica')['Tasa'].quantile(0.75).reset_index()
        umbral_hist.rename(columns={'Tasa': 'Umbral_Q3'}, inplace=True)

        # --- 3. ENTRENAMIENTO PONDERADO (WEIGHTED LEAST SQUARES - WLS) ---
        WEEKS_PER_YEAR = 52.1429
        min_year = 2014
        
        # FEATURE ENGINEERING: Convierte el tiempo (Semana) en señales matemáticas cíclicas
        # Esto permite que la regresión "entienda" que después de la ultima semana viene la semana 1
        hist_agrupado['t'] = (hist_agrupado['Anio'] - min_year) * WEEKS_PER_YEAR + hist_agrupado['SemanaEstadistica']
        hist_agrupado['sin1'] = np.sin(2 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
        hist_agrupado['cos1'] = np.cos(2 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
        hist_agrupado['sin2'] = np.sin(4 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
        hist_agrupado['cos2'] = np.cos(4 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
        hist_agrupado['intercepto'] = 1

        # ASIGNACIÓN DE PESOS: Se fuerza al modelo a "creerle" 5 veces más 
        # a los datos recientes (2023 en adelante) que a los datos antiguos.
        hist_agrupado['peso'] = np.where(hist_agrupado['Anio'] >= 2023, 5.0, 1.0)
        
        # Aplicamos la raíz cuadrada del peso a las variables X e Y (Requisito Matemático de WLS)
        W = np.sqrt(hist_agrupado['peso'].values)
        
        X_train = hist_agrupado[['intercepto', 't', 'sin1', 'cos1', 'sin2', 'cos2']].values
        X_train_w = X_train * W[:, np.newaxis] # Multiplica cada fila de X por su peso correspondiente
        
        y_train = hist_agrupado['Tasa'].values
        y_train_w = y_train * W # Multiplica cada valor de Y por su peso

        # EJECUCIÓN DEL MODELO: Extrae los coeficientes (betas) usando álgebra lineal
        beta, residuals, rank, s = np.linalg.lstsq(X_train_w, y_train_w, rcond=None)

        # --- 4. PROYECCIÓN FUTURA ---
        # Se crea un dataframe "vacío" con las semanas del año a predecir
        df_futuro = pd.DataFrame({'SemanaEstadistica': range(1, 53)})
        df_futuro['Anio'] = pred_anio
        df_futuro['t'] = (df_futuro['Anio'] - min_year) * WEEKS_PER_YEAR + df_futuro['SemanaEstadistica']
        df_futuro['sin1'] = np.sin(2 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
        df_futuro['cos1'] = np.cos(2 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
        df_futuro['sin2'] = np.sin(4 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
        df_futuro['cos2'] = np.cos(4 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
        df_futuro['intercepto'] = 1

        # La predicción (Y) es el producto punto entre la matriz de características (X) y los coeficientes (beta)
        X_future = df_futuro[['intercepto', 't', 'sin1', 'cos1', 'sin2', 'cos2']].values
        df_futuro['Tasa_Proyectada'] = X_future.dot(beta)
        df_futuro['Tasa_Proyectada'] = df_futuro['Tasa_Proyectada'].clip(lower=0) # Evita proyecciones negativas imposibles

        df_plot = pd.merge(df_futuro, umbral_hist, on='SemanaEstadistica', how='left')

        # --- 5. EVALUACIÓN DE PRECISIÓN (MAPE Y MAE) ---
        # Si el usuario selecciona un año que "ya pasó" o está en curso (ej. 2024), 
        # cruzamos la proyección contra la realidad para medir el error del modelo.
        error_mape = None
        error_mae_val = None
        if not df_real_eval.empty:
            real_agrupado = df_real_eval.groupby('SemanaEstadistica')[['Atenciones', 'Poblacion']].sum().reset_index()
            real_agrupado['Tasa_Real'] = (real_agrupado['Atenciones'] / real_agrupado['Poblacion'].replace(0, np.nan)) * 10000
            df_plot = pd.merge(df_plot, real_agrupado[['SemanaEstadistica', 'Tasa_Real']], on='SemanaEstadistica', how='left')
            
            df_plot['Tasa_Real'] = pd.to_numeric(df_plot['Tasa_Real'], errors='coerce')
            df_plot['Tasa_Proyectada'] = pd.to_numeric(df_plot['Tasa_Proyectada'], errors='coerce')
            
            eval_data = df_plot.dropna(subset=['Tasa_Real', 'Tasa_Proyectada'])
            eval_data_mape = eval_data[eval_data['Tasa_Real'] > 0]
            
            if not eval_data_mape.empty:
                # MAPE (Mean Absolute Percentage Error): ¿En qué % se equivocó en promedio?
                error_mape = ((eval_data_mape['Tasa_Real'] - eval_data_mape['Tasa_Proyectada']).abs() / eval_data_mape['Tasa_Real']).mean() * 100
            if not eval_data.empty:
                # MAE (Mean Absolute Error): ¿Por cuántos puntos de tasa se equivocó en promedio?
                error_mae_val = (eval_data['Tasa_Proyectada'] - eval_data['Tasa_Real']).abs().mean()
        else:
            df_plot['Tasa_Real'] = np.nan

        # --- 6. IDENTIFICAR COLAPSOS ---
        df_plot['Umbral_Q3'] = pd.to_numeric(df_plot['Umbral_Q3'], errors='coerce')
        df_plot['Es_Colapso'] = df_plot['Tasa_Proyectada'] > df_plot['Umbral_Q3']
        num_semanas_colapso = df_plot['Es_Colapso'].sum()
        
        semana_peak = df_plot.loc[df_plot['Tasa_Proyectada'].idxmax(), 'SemanaEstadistica']
        tasa_peak = df_plot['Tasa_Proyectada'].max()

        # --- 7. TARJETAS KPI (DISEÑO HÍBRIDO MAPE + MAE) ---
        kpi_color = "#d62728" if num_semanas_colapso > 0 else "#2ca02c"
        
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        st.write("") 
        
        with col_kpi1:
            st.markdown(f"""
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; border-left: 5px solid #102a43; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 0.85em; color: #555; font-weight: bold; text-transform: uppercase;">Tasa Peak Proyectada</div>
                <div style="font-size: 2.2em; color: #102a43; font-weight: 800; line-height: 1.2;">{tasa_peak:.1f}</div>
                <div style="font-size: 0.85em; color: #666;">Semana {int(semana_peak)}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kpi2:
            st.markdown(f"""
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; border-left: 5px solid {kpi_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 0.85em; color: #555; font-weight: bold; text-transform: uppercase;">Riesgo de Epidemia</div>
                <div style="font-size: 2.2em; color: {kpi_color}; font-weight: 800; line-height: 1.2;">{num_semanas_colapso}</div>
                <div style="font-size: 0.85em; color: #666;">Semanas sobre Límite Q3</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kpi3:
            if error_mape is not None and error_mae_val is not None:
                mape_color = "#2ca02c" if error_mape < 25 else "#ff7f0e" if error_mape < 40 else "#d62728"
                st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; border-left: 5px solid {mape_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 0.85em; color: #555; font-weight: bold; text-transform: uppercase;">Desviación del Modelo</div>
                    <div style="font-size: 2.2em; color: {mape_color}; font-weight: 800; line-height: 1.2;">± {error_mape:.1f}%</div>
                    <div style="font-size: 0.85em; color: #666;">Aprox. ± {error_mae_val:.1f} pts de tasa real</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; border-left: 5px solid #999; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center;">
                    <div style="font-size: 0.85em; color: #555; font-weight: bold; text-transform: uppercase;">Desviación del Modelo</div>
                    <div style="font-size: 1.4em; color: #999; font-weight: 800; line-height: 1.2; margin-top: 10px;">Proyección</div>
                    <div style="font-size: 0.85em; color: #666; margin-top: 5px;">Sin datos reales para evaluar</div>
                </div>
                """, unsafe_allow_html=True)

        st.write("")

        # --- 8. GRÁFICO EXPLICATIVO ---
        st.markdown(f"### 📊 Evolución Semanal Esperada vs Límite Epidémico")

        base = alt.Chart(df_plot).encode(x=alt.X('SemanaEstadistica:O', title='Semana Epidemiológica del Año', axis=alt.Axis(labelAngle=0)))

        barras_pred = base.mark_bar(size=14).encode(
            y=alt.Y('Tasa_Proyectada:Q', title='Tasa Proyectada (x 10k hab)'),
            color=alt.condition(
                alt.datum.Tasa_Proyectada > alt.datum.Umbral_Q3,
                alt.value('#d62728'), # Rojo si colapsa
                alt.value('#1f77b4')  # Azul si es seguro
            ),
            tooltip=[
                alt.Tooltip('SemanaEstadistica', title='Semana'),
                alt.Tooltip('Tasa_Proyectada:Q', title='Proyección Ponderada', format='.1f'),
                alt.Tooltip('Umbral_Q3:Q', title='Límite Q3', format='.1f')
            ]
        )

        linea_q3 = base.mark_line(color='#333333', strokeDash=[4, 4], strokeWidth=2).encode(y='Umbral_Q3:Q')
        grafico_final = barras_pred + linea_q3

        caption_extra = ""
        # Si hay datos reales (ej. evaluando 2024), plotea los puntos negros para comparar
        if error_mape is not None:
            df_reales = df_plot.dropna(subset=['Tasa_Real']).copy()
            puntos_reales = alt.Chart(df_reales).mark_circle(color='black', size=60, opacity=1).encode(
                x='SemanaEstadistica:O', y='Tasa_Real:Q',
                tooltip=[alt.Tooltip('SemanaEstadistica', title='Semana'), alt.Tooltip('Tasa_Real:Q', title='Dato Real (Validación)', format='.1f')]
            )
            grafico_final = grafico_final + puntos_reales
            caption_extra = " | ⚫ **Puntos Negros:** Tasa Real registrada."

        st.altair_chart(grafico_final.properties(height=450), use_container_width=True)
        st.caption(f"🟦 **Barra Azul:** Pico proyectado en zona segura. | 🟥 **Barra Roja:** Pico proyectado en Alerta (Epidemia). | ➖ **Línea Punteada:** Límite máximo histórico esperado (Q3).{caption_extra}")

# =============================================================================
# TAB 9: PREDICCIÓN POR CAUSA ESPECÍFICA (GRILLA)
# Replica el modelo de la Tab anterior pero aplicándolo de forma iterada
# y encapsulada a las 4 enfermedades respiratorias principales.
# =============================================================================
with tabs[8]:
    st.header("Predicción Específica por Causa Respiratoria")
    
    st.markdown("""
    <div style="background-color:#f3e5f5; padding:15px; border-radius:8px; border-left:6px solid #8e24aa; margin-bottom:20px; color: #4a148c; font-family: sans-serif;">
        <h4 style="margin-top: 0; color: #4a148c;">🔬 Desglose Predictivo por Patología</h4>
        <p style="margin-bottom: 0;">4 causas respiratorias más críticas. Permite anticipar qué tipo de carga viral predominará en la red.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        c_causa1, c_causa2 = st.columns(2)
        opciones_alcance_causa = ["Global (Toda la Red)"] + sorted(df_full['ComunaGlosa'].unique())
        causa_alcance = c_causa1.selectbox("Territorio a Predecir (Causas):", opciones_alcance_causa, key="causa_scope")
        opciones_anios_causa = [2026, 2025, 2024] 
        causa_anio = c_causa2.selectbox("Año Objetivo (Proyección Causas):", opciones_anios_causa, index=0, key="causa_year")

    # Lista de enfermedades a modelar. Deben coincidir EXACTAMENTE con el diccionario MAPEO_CAUSAS
    COLUMNA_ENFERMEDAD = "Causa" 
    enfermedades_objetivo = [
        "IRA Alta", 
        "Bronquiolitis", 
        "Neumonía", 
        "Influenza"
    ]
    
    st.markdown("---")
    
    # Renderizado en Grilla 2x2
    col_izq, col_der = st.columns(2)
    columnas_asignadas = [col_izq, col_der, col_izq, col_der] 

    for i, enfermedad in enumerate(enfermedades_objetivo):
        with columnas_asignadas[i]:
            st.markdown(f"### 🦠 {enfermedad.split(' (')[0]}")
            
            # FILTRO CRÍTICO: Selecciona solo la enfermedad actual iterada
            # regex=False previene errores con nombres que tienen paréntesis
            df_enf = df_full[df_full[COLUMNA_ENFERMEDAD].str.contains(enfermedad, case=False, na=False, regex=False)].copy()
            
            if df_enf.empty:
                st.warning(f"No hay registros de esta causa.")
                st.write("---") 
                continue
            
            mask_train = (~df_enf['Anio'].isin([2020, 2021, 2022])) & (df_enf['Anio'] < causa_anio)
            
            if causa_alcance == "Global (Toda la Red)":
                df_hist = df_enf[mask_train].copy()
                df_real = df_enf[df_enf['Anio'] == causa_anio].copy()
            else:
                df_hist = df_enf[mask_train & (df_enf['ComunaGlosa'] == causa_alcance)].copy()
                df_real = df_enf[(df_enf['Anio'] == causa_anio) & (df_enf['ComunaGlosa'] == causa_alcance)].copy()

            if df_hist.empty:
                st.info(f"Sin historia suficiente.")
                st.write("---")
                continue
            
            hist_agrupado = df_hist.groupby(['Anio', 'SemanaEstadistica'])[['Atenciones', 'Poblacion']].sum().reset_index()
            hist_agrupado['Tasa'] = (hist_agrupado['Atenciones'] / hist_agrupado['Poblacion'].replace(0, np.nan)) * 10000
            hist_agrupado = hist_agrupado.dropna(subset=['Tasa'])

            umbral_hist = hist_agrupado.groupby('SemanaEstadistica')['Tasa'].quantile(0.75).reset_index()
            umbral_hist.rename(columns={'Tasa': 'Umbral_Q3'}, inplace=True)

            # ENTRENAMIENTO WLS IDENTICO AL MODELO GENERAL
            WEEKS_PER_YEAR = 52.1429
            min_year = 2014
            
            hist_agrupado['t'] = (hist_agrupado['Anio'] - min_year) * WEEKS_PER_YEAR + hist_agrupado['SemanaEstadistica']
            hist_agrupado['sin1'] = np.sin(2 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
            hist_agrupado['cos1'] = np.cos(2 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
            hist_agrupado['sin2'] = np.sin(4 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
            hist_agrupado['cos2'] = np.cos(4 * np.pi * hist_agrupado['t'] / WEEKS_PER_YEAR)
            hist_agrupado['intercepto'] = 1

            hist_agrupado['peso'] = np.where(hist_agrupado['Anio'] >= 2023, 5.0, 1.0)
            W = np.sqrt(hist_agrupado['peso'].values)
            
            X_train = hist_agrupado[['intercepto', 't', 'sin1', 'cos1', 'sin2', 'cos2']].values
            X_train_w = X_train * W[:, np.newaxis]
            y_train = hist_agrupado['Tasa'].values
            y_train_w = y_train * W

            beta, residuals, rank, s = np.linalg.lstsq(X_train_w, y_train_w, rcond=None)

            # PROYECCIÓN
            df_futuro = pd.DataFrame({'SemanaEstadistica': range(1, 53)})
            df_futuro['Anio'] = causa_anio
            df_futuro['t'] = (df_futuro['Anio'] - min_year) * WEEKS_PER_YEAR + df_futuro['SemanaEstadistica']
            df_futuro['sin1'] = np.sin(2 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
            df_futuro['cos1'] = np.cos(2 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
            df_futuro['sin2'] = np.sin(4 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
            df_futuro['cos2'] = np.cos(4 * np.pi * df_futuro['t'] / WEEKS_PER_YEAR)
            df_futuro['intercepto'] = 1

            X_future = df_futuro[['intercepto', 't', 'sin1', 'cos1', 'sin2', 'cos2']].values
            df_futuro['Tasa_Proyectada'] = X_future.dot(beta)
            df_futuro['Tasa_Proyectada'] = df_futuro['Tasa_Proyectada'].clip(lower=0)

            df_plot = pd.merge(df_futuro, umbral_hist, on='SemanaEstadistica', how='left')

            # EVALUACIÓN ESPECÍFICA DE LA CAUSA
            error_mape = None
            if not df_real.empty:
                real_agrupado = df_real.groupby('SemanaEstadistica')[['Atenciones', 'Poblacion']].sum().reset_index()
                real_agrupado['Tasa_Real'] = (real_agrupado['Atenciones'] / real_agrupado['Poblacion'].replace(0, np.nan)) * 10000
                df_plot = pd.merge(df_plot, real_agrupado[['SemanaEstadistica', 'Tasa_Real']], on='SemanaEstadistica', how='left')
                
                eval_data = df_plot.dropna(subset=['Tasa_Real', 'Tasa_Proyectada'])
                eval_data_mape = eval_data[eval_data['Tasa_Real'] > 0]
                if not eval_data_mape.empty:
                    error_mape = ((eval_data_mape['Tasa_Real'] - eval_data_mape['Tasa_Proyectada']).abs() / eval_data_mape['Tasa_Real']).mean() * 100
            else:
                df_plot['Tasa_Real'] = np.nan

            df_plot['Umbral_Q3'] = pd.to_numeric(df_plot['Umbral_Q3'], errors='coerce')
            num_semanas_colapso = (df_plot['Tasa_Proyectada'] > df_plot['Umbral_Q3']).sum()
            tasa_peak = df_plot['Tasa_Proyectada'].max()

            # HTML MINIMALISTA: Tarjeta resumen para el encabezado del mini-gráfico
            color_alerta = "#d62728" if num_semanas_colapso > 0 else "#2ca02c"
            texto_mape = f"🎯 MAPE: ±{error_mape:.1f}%" if error_mape else "🔮 Proyección Pura"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 13px; background-color: white; padding: 10px; border-radius: 5px; border: 1px solid #eee; margin-bottom: 10px;">
                <div><b>Tasa Peak:</b> {tasa_peak:.1f}</div>
                <div style="color:{color_alerta};"><b>Epidemia:</b> {num_semanas_colapso} Sem.</div>
                <div style="color:#673ab7; font-weight:bold;">{texto_mape}</div>
            </div>
            """, unsafe_allow_html=True)

            # RENDERIZACIÓN ALTAIR COMPACTA
            base = alt.Chart(df_plot).encode(x=alt.X('SemanaEstadistica:O', title='', axis=alt.Axis(labelAngle=0, tickCount=10)))
            barras = base.mark_bar(size=6).encode(
                y=alt.Y('Tasa_Proyectada:Q', title='Tasa Proyectada'),
                color=alt.condition(alt.datum.Tasa_Proyectada > alt.datum.Umbral_Q3, alt.value('#d62728'), alt.value('#1f77b4')),
                tooltip=['SemanaEstadistica', alt.Tooltip('Tasa_Proyectada:Q', format='.1f'), alt.Tooltip('Umbral_Q3:Q', format='.1f')]
            )
            linea = base.mark_line(color='#333333', strokeDash=[2, 2], strokeWidth=1.5).encode(y='Umbral_Q3:Q')
            grafico_final = barras + linea
            
            if error_mape is not None:
                df_reales = df_plot.dropna(subset=['Tasa_Real'])
                puntos = alt.Chart(df_reales).mark_circle(color='black', size=40).encode(
                    x='SemanaEstadistica:O', y='Tasa_Real:Q', tooltip=['SemanaEstadistica', alt.Tooltip('Tasa_Real:Q', title='Real', format='.1f')]
                )
                grafico_final = grafico_final + puntos

            st.altair_chart(grafico_final.properties(height=280), use_container_width=True)
            st.write("---") 

st.markdown("---")
st.caption("Sistema de Vigilancia Respiratoria")