import os
import sys
import multiprocessing
import streamlit.web.cli as stcli

# =============================================================================
# MÓDULO DE ARRANQUE (LAUNCHER)
# Este script es el punto de entrada oficial del archivo .exe generado por PyInstaller.
# Su misión es configurar el entorno, aislar los subprocesos de Windows y 
# "engañar" a Streamlit para que arranque el dashboard sin necesidad de abrir una terminal.
# =============================================================================

def main():
    """
    Configura las variables de entorno y los argumentos de consola virtuales
    para lanzar el servidor de Streamlit de forma silenciosa y estable.
    """
    
    # -------------------------------------------------------------------------
    # 1. SEDANTES
    # Streamlit por defecto tiene un File Watcher que vigila
    # la carpeta. Si detecta que un archivo cambió, reinicia toda la página web.
    # Como nuestro sistema descarga y reemplaza el archivo Parquet automáticamente,
    # debemos apagar este vigilante para que la web no parpadee ni se reinicie sola.
    # -------------------------------------------------------------------------
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false" # Apaga la telemetría para mayor velocidad y privacidad

    # -------------------------------------------------------------------------
    # 2. RESOLUCIÓN DE RUTAS DINÁMICAS
    # Cuando PyInstaller ejecuta un .exe, descomprime todo el código fuente 
    # en una carpeta temporal oculta de Windows llamada "_MEIPASS".
    # Este bloque detecta si estamos en el .exe o en desarrollo normal, 
    # y enruta el sistema hacia el archivo principal del dashboard.
    # -------------------------------------------------------------------------
    if getattr(sys, 'frozen', False):
        # Modo Producción (.exe): Usamos la ruta temporal donde PyInstaller extrajo los scripts
        base_dir = sys._MEIPASS
    else:
        # Modo Desarrollo (Consola): Usamos la ruta normal de la carpeta
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Ubicamos el archivo principal de la interfaz gráfica
    script_path = os.path.join(base_dir, 'pruebaPSCORELOESSyREGRESIONARMONICA.py')

    # -------------------------------------------------------------------------
    # 3. INYECCIÓN DE COMANDOS VIRTUALES (SYS.ARGV)
    # Reemplazamos los argumentos del sistema operativo. Es exactamente igual 
    # a escribir en la terminal negra de Windows: 
    # "streamlit run pruebaPSCORELOESSyREGRESIONARMONICA.py --server.fileWatcherType=none..."
    # -------------------------------------------------------------------------
    sys.argv = [
        "streamlit", 
        "run", 
        script_path, 
        "--global.developmentMode=false",  # Desactiva el menú de "Deploy" arriba a la derecha
        "--server.fileWatcherType=none",   # Doble seguro para apagar el vigilante de archivos
        "--browser.gatherUsageStats=false" # Doble seguro para la telemetría
    ]
    
    # Arranca el motor principal de Streamlit pasando nuestros comandos virtuales
    sys.exit(stcli.main())

if __name__ == "__main__":
    # =========================================================================
    # LÍNEA DE DEFENSA CRÍTICA PARA WINDOWS
    # multiprocessing.freeze_support() evita el "Bucle Infinito de Pestañas".
    # Windows maneja los subprocesos de los .exe de forma muy peculiar. Si una librería 
    # interna (como la que descarga datos) intenta abrir un hilo nuevo, Windows 
    # por error ejecuta el .exe completo de nuevo desde cero. 
    # Esta función congela el estado principal y le dice a Windows: "No abras más ventanas".
    # =========================================================================
    multiprocessing.freeze_support()
    
    # Llama a la función de configuración y arranque
    main()