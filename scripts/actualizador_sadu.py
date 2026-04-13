import os
import sys
import requests
import PipelineServicioTalcahuanoCompleto

# =============================================================================
# MÓDULO DE ACTUALIZACIÓN Y ORQUESTACIÓN (ACTUALIZADOR SADU)
# Este script actúa como el "Controlador" (Backend) del dashboard. 
# Sus dos responsabilidades principales son:
# 1. Descargar la base de datos cruda desde el portal del Minsal de forma segura.
# 2. Orquestar (llamar) al script de limpieza y cruce de datos (ETL).
# =============================================================================

def obtener_directorio_raiz():
    """
    Detecta dinámicamente el entorno de ejecución del programa.
    Es una función crítica para la portabilidad del sistema cuando se compila con PyInstaller.
    
    Retorna:
        str: La ruta absoluta de la carpeta raíz donde debe operar el sistema.
    """
    # Si 'sys.frozen' existe y es True, el código se está ejecutando como un '.exe' compilado.
    if getattr(sys, 'frozen', False):
        # sys.executable devuelve la ruta exacta donde el usuario hizo doble clic al .exe
        # Esto asegura que los archivos .parquet se descarguen junto al programa 
        # y no en carpetas temporales ocultas de Windows.
        return os.path.dirname(sys.executable)
    else:
        # Si se ejecuta desde la consola en modo desarrollo (ej. streamlit run...),
        # __file__ devuelve la ruta de este script de Python.
        return os.path.dirname(os.path.abspath(__file__))

def descargar_y_guardar_dataset():
    """
    Descarga la base de datos SADU desde datos.gob.cl utilizando una estrategia de
    'descarga segura' (Safe Download) y reemplazo atómico para evitar corrupción de datos.
    No requiere intervención del usuario (sin ventanas emergentes).
    
    Retorna:
        tuple: (bool, str) -> (Éxito/Fallo, Mensaje explicativo para la UI)
    """
    # URL directa (Raw Data) del repositorio oficial de Datos Abiertos del Gobierno de Chile
    url = "https://datos.gob.cl/dataset/606ef5bb-11d1-475b-b69f-b980da5757f4/resource/ae6c9887-106d-4e98-8875-40bf2b836041/download/at_urg_respiratorio_semanal.parquet"
    
    try:
        carpeta_raiz = obtener_directorio_raiz()
        archivo_final = os.path.join(carpeta_raiz, 'at_urg_respiratorio_semanal.parquet')
        
        # Se define un archivo temporal. Si la descarga se corta a la mitad por fallo de internet,
        # el archivo original de la semana pasada no se daña.
        archivo_temporal = os.path.join(carpeta_raiz, 'temp_descarga.parquet')

        # 1. DESCARGA EN BLOQUES (STREAMING)
        # requests.get(stream=True) evita cargar todo el archivo pesado en la memoria RAM de golpe.
        respuesta = requests.get(url, stream=True)
        respuesta.raise_for_status() # Lanza una excepción si el servidor responde con error (ej. 404 o 500)

        # Escribimos la descarga en el disco duro en fragmentos (chunks) de 8 KB.
        with open(archivo_temporal, 'wb') as f:
            for chunk in respuesta.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. REEMPLAZO SEGURO (ATOMIC SWAP)
        # Solo llegamos a este punto si el archivo temporal se descargó al 100%.
        if os.path.exists(archivo_final):
            try:
                # Destruimos la base de datos vieja
                os.remove(archivo_final)
            except PermissionError:
                # Mecanismo de defensa: Si Excel, PowerBI o DuckDB tienen el archivo tomado/bloqueado.
                return False, "Error: El archivo original está abierto en otro programa. Ciérrelo e intente de nuevo."
        
        # Renombramos el archivo temporal para que asuma su identidad final.
        os.rename(archivo_temporal, archivo_final)

        return True, "Base de datos descargada y reemplazada automáticamente."

    except Exception as e:
        # 3. ROLLBACK (Manejo de Errores)
        # Si hubo un corte de luz o caída de red durante la descarga,
        # el bloque 'except' atrapa el error, borra el archivo corrupto temporal
        # y permite que el dashboard siga funcionando con la data antigua.
        if os.path.exists(archivo_temporal):
            try:
                os.remove(archivo_temporal)
            except:
                pass # Silencia posibles errores de borrado durante el pánico
        return False, f"Error en la descarga de red: {e}"

def ejecutar_pipeline_limpieza():
    """
    Función 'puente' (Wrapper) que comunica el botón del Dashboard (interfaz gráfica)
    con el motor de procesamiento de datos (PipelineServicioTalcahuanoCompleto.py).
    
    Retorna:
        tuple: (bool, str) -> Para que Streamlit muestre un globo de éxito (Toast) o error.
    """
    try:
        # Llama a la orquestación principal del archivo vecino.
        # Esto cruzará SADU con INE y generará el 'base_talcahuano_final_tasa_ok.parquet'
        PipelineServicioTalcahuanoCompleto.pipeline_blindado()
        
        return True, "Pipeline ejecutado correctamente. Base final actualizada."
    except Exception as e:
        # Captura cualquier error de sintaxis, falta de columnas o fallos de Pandas
        # para mostrarlo elegantemente en la pantalla web en lugar de crashear el .exe
        return False, f"Error durante la limpieza y cruce de datos: {e}"