import pandas as pd
import numpy as np
import os

# =============================================================================
# ⚙️ CONFIGURACIÓN DE ENTORNO
# Define los archivos de entrada (Raw Data) y de salida (Clean Data).
# Se utiliza el formato Parquet por su alta compresión y velocidad de lectura/escritura,
# lo cual es crucial al manejar bases de datos a nivel nacional.
# =============================================================================
FILE_SADU_RAW = 'at_urg_respiratorio_semanal.parquet' # Base cruda del Minsal
FILE_INE_CLEAN = 'ine_limpio_fase1.parquet'         # Proyecciones poblacionales pre-limpias
OUTPUT_FINAL = 'base_talcahuano_final_tasa_ok.parquet' # Base maestra que leerá el Dashboard

# Diccionario maestro para estandarizar los nombres de las columnas de edad entre 
# la base del DEIS (Minsal) y las clasificaciones del INE.
MAPEO_EDADES = {
    'NumMenor1Anio': 'Menor1Anio',
    'Num1a4Anios':   '1a4Anios',
    'Num5a14Anios':  '5a14Anios',
    'Num15a64Anios': '15a64Anios',
    'Num65oMas':     '65oMas'
}

def pipeline_blindado():
    """
    Función principal de orquestación ETL.
    Extrae, limpia, transforma (Melt), cruza (Merge) y calcula métricas (Tasa).
    """
    print("🚀 INICIANDO PIPELINE (CORRECCIÓN DE TASAS)")
    print("=" * 60)

    # =========================================================================
    # 1. EXTRACCIÓN Y LIMPIEZA INICIAL (SADU)
    # =========================================================================
    if not os.path.exists(FILE_SADU_RAW): 
        print("❌ Falta archivo SADU (Minsal). Proceso abortado."); return
        
    df = pd.read_parquet(FILE_SADU_RAW)
    
    # 1.1 FILTRO GEOGRÁFICO: Aísla únicamente los datos de la red del SS Talcahuano
    df = df[df['ServicioSaludGlosa'] == 'Servicio de Salud Talcahuano'].copy()
    
    # 1.2 FILTRO CLÍNICO: Elimina categorías redundantes o ruidosas.
    # Se excluyen los totales generales (para evitar doble conteo) y los 
    # diagnósticos COVID puros, ya que el enfoque es el análisis de virus respiratorios tradicionales.
    glosas_prohibidas = [
        "TOTAL CAUSA SISTEMA  RESPIRATORIO (J00-J98)",
        "- Por covid-19, virus no identificado U07.2",
        "- Por covid-19, virus identificado U07.1"
    ]
    df = df[~df['Causa'].str.strip().isin([g.strip() for g in glosas_prohibidas])]
    
    # 1.3 HOMOLOGACIÓN ORTOGRÁFICA: Previene fallos en el cruce de datos con el INE
    # debido a tildes o variaciones en la escritura de las comunas o regiones.
    reemplazos = {
        "Tome": "Tomé", "BíoBío": "BioBío", 
        "Región Del Bíobío": "Región del BioBío", "Región del Bíobío": "Región del BioBío"
    }
    cols_txt = ['ComunaGlosa', 'RegionGlosa', 'EstablecimientoGlosa']
    for col in cols_txt:
        if col in df.columns:
            df[col] = df[col].replace(reemplazos, regex=True)

    # 1.4 LIMPIEZA DE BASURA ESTRUCTURAL
    # Convierte celdas vacías en objetos NaN oficiales y elimina filas corruptas.
    # Luego, se descartan columnas administrativas que no aportan valor epidemiológico
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    df.dropna(inplace=True)
    cols_drop = ['EstablecimientoCodigo', 'RegionCodigo', 'ComunaCodigo', 'ServicioSaludCodigo', 
                 'DependenciaAdministrativa', 'TipoUrgencia', 'NivelComplejidad', 'OrdenCausa']
    df.drop(columns=[c for c in cols_drop if c in df.columns], inplace=True)

    # =========================================================================
    # 2. TRANSFORMACIÓN ESTRUCTURAL (MELT)
    # La base original viene en formato "ancho" (una columna por cada grupo de edad).
    # Para poder cruzarla con el INE y graficarla fácilmente, se transforma a formato
    # "largo", donde la edad pasa a ser una variable categórica en las filas.
    # =========================================================================
    print("🔄 Transformando estructura (Melt)...")
    
    cols_edad = [c for c in MAPEO_EDADES.keys() if c in df.columns]
    cols_id = [c for c in df.columns if c not in cols_edad] # Columnas que se mantendrán fijas (Año, Comuna, Centro, Causa)
    
    df_melt = df.melt(id_vars=cols_id, value_vars=cols_edad, var_name='GrupoRaw', value_name='Atenciones')
    
    # Se aplica el diccionario para estandarizar los nombres de los grupos etarios
    df_melt['grupo_etario'] = df_melt['GrupoRaw'].map(MAPEO_EDADES)
    df_melt.drop(columns=['GrupoRaw'], inplace=True)
    df_melt['Atenciones'] = df_melt['Atenciones'].fillna(0).astype(int)

    # =========================================================================
    # 3. PREPARACIÓN DE LLAVES PARA EL CRUCE DE DATOS
    # Garantiza que las "llaves" (keys) de cruce tengan exactamente el mismo tipo de 
    # dato (int o string) y sin espacios en blanco residuales, evitando falsos negativos.
    # =========================================================================
    print("🔧 Normalizando Tipos de Datos para el Cruce...")
    
    # Normalización del lado SADU (Minsal)
    df_melt['Anio'] = df_melt['Anio'].astype(int)
    df_melt['ComunaGlosa'] = df_melt['ComunaGlosa'].astype(str).str.strip()
    df_melt['grupo_etario'] = df_melt['grupo_etario'].astype(str).str.strip()

    # Carga y Normalización del lado INE
    if not os.path.exists(FILE_INE_CLEAN): print("❌ Falta archivo INE. Proceso abortado."); return
    df_ine = pd.read_parquet(FILE_INE_CLEAN)
    
    # Estandarización de nombres de columnas
    if 'anio' in df_ine.columns: df_ine.rename(columns={'anio': 'Anio'}, inplace=True)
    if 'poblacion' in df_ine.columns: df_ine.rename(columns={'poblacion': 'Poblacion'}, inplace=True)
    
    df_ine['Anio'] = df_ine['Anio'].astype(int)
    df_ine['ComunaGlosa'] = df_ine['ComunaGlosa'].astype(str).str.strip()
    df_ine['grupo_etario'] = df_ine['grupo_etario'].astype(str).str.strip()
    
    # OPTIMIZACIÓN: Se recorta la inmensa base del INE solo a las comunas que nos interesan,
    # reduciendo drásticamente el tiempo de procesamiento de la siguiente etapa.
    comunas_sadu = df_melt['ComunaGlosa'].unique()
    df_ine = df_ine[df_ine['ComunaGlosa'].isin(comunas_sadu)]
    
    print(f"   Comunas en SADU: {comunas_sadu}")
    print(f"   Comunas encontradas en INE: {df_ine['ComunaGlosa'].unique()}")

    # =========================================================================
    # 4. CRUCE DE BASES (LEFT JOIN)
    # A cada fila de atenciones del SADU se le adjunta la población correspondiente
    # del INE según su Comuna, Año y Grupo Etario.
    # =========================================================================
    print("🔗 Realizando cruce de bases...")
    df_final = pd.merge(df_melt, df_ine, on=['ComunaGlosa', 'Anio', 'grupo_etario'], how='left')

    # AUDITORÍA DE CALIDAD: Verifica si alguna atención quedó "huérfana" (sin población asignada).
    # Esto ocurre si el INE no tiene proyección para un año/comuna específica.
    sin_pob = df_final['Poblacion'].isna().sum()
    if sin_pob > 0:
        print(f"⚠️ ALERTA CRÍTICA: {sin_pob} filas no cruzaron (Población = NaN).")
        print("   -> Ejemplo de fila sin cruce:")
        print(df_final[df_final['Poblacion'].isna()][['ComunaGlosa', 'Anio', 'grupo_etario']].head(1))
    else:
        print("✅ Cruce perfecto (0 nulos).")

    # =========================================================================
    # 5. CÁLCULO DE MÉTRICA PRINCIPAL: TASA DE INCIDENCIA
    # La Tasa estandariza la carga asistencial. Permite comparar equitativamente
    # comunas pequeñas (ej. Florida) contra comunas grandes (ej. Talcahuano).
    # =========================================================================
    print("🧮 Calculando Tasa...")
    
    # Forzamos tipos flotantes para evitar errores de división en Pandas
    df_final['Poblacion'] = df_final['Poblacion'].fillna(0).astype(float)
    df_final['Atenciones'] = df_final['Atenciones'].astype(float)      
    
    df_final['Tasa'] = 0.0
    
    # FÓRMULA EPIDEMIOLÓGICA ESTÁNDAR: (Atenciones / Población Total) * 10,000 habitantes.
    # Se aplica una máscara de seguridad (`mask = Poblacion > 0`) para evitar 
    # un error matemático fatal de división por cero (ZeroDivisionError).
    mask = df_final['Poblacion'] > 0
    df_final.loc[mask, 'Tasa'] = (df_final.loc[mask, 'Atenciones'] / df_final.loc[mask, 'Poblacion']) * 10000
    
    df_final['Tasa'] = df_final['Tasa'].round(2)

    # =========================================================================
    # 6. GUARDADO Y EXPORTACIÓN
    # Sobrescribe la base final optimizada que será consumida por Streamlit.
    # =========================================================================
    print("-" * 60)
    df_final.to_parquet(OUTPUT_FINAL, index=False)
    print(f"💾 Parquet guardado: {OUTPUT_FINAL}")
    
    # Pequeño debug visual para confirmar por consola que la data final es coherente
    print("\n🔎 VERIFICACIÓN FINAL (Muestra aleatoria con datos):")
    muestra = df_final[df_final['Atenciones'] > 0].head()
    print(muestra[['ComunaGlosa', 'Anio', 'grupo_etario', 'Atenciones', 'Poblacion', 'Tasa']])

if __name__ == "__main__":
    pipeline_blindado()