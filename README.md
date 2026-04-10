# Ecosistema analtico de vigilancia epidemiolgica de urgencias respiratorias
Proyecto con base de datos publica del MINSAL que contiene los totales de consultas y hospitalizaciones por causa respiratoria provenientes del Sistema de Atención Diaria de Urgencias (SADU) por establecimiento de salud, semana epidemiológica y grupo de edad.

# Objetivo general del proyecto

Diseñar, desarrollar e implementar un Ecosistema Analítico de Vigilancia Epidemiológica de Urgencia Respiratoria para el Servicio de Salud Talcahuano (SST), mediante la integración automatizada de repositorios masivos de datos clínicos y demográficos. El sistema tiene como fin último transformar la data cruda en inteligencia sanitaria accionable, permitiendo la detección temprana de brotes, la cuantificación de la sobrecarga asistencial y la predicción de demanda estacional para optimizar la toma de decisiones estratégicas y operativas en la Red Asistencial.

# Objetivos Específicos y Pilares de Desarrollo

El proyecto se desglosa en los siguientes ejes técnicos y estratégicos:

1. Pilar de Ingeniería de Datos y Arquitectura

•	Automatización del Pipeline ETL: Implementar un flujo de extracción, transformación y carga (ETL) capaz de ingerir millones de registros del repositorio SADU-DEIS, realizando procesos de limpieza ortográfica, normalización de entidades geográficas y "unpivoting" estructural para garantizar la integridad referencial y la interoperabilidad semántica con las bases demográficas del INE.

•	Encapsulamiento y Portabilidad: Desarrollar una solución tecnológica basada en una arquitectura modular e independiente del entorno (Stand-alone), empaquetada como un artefacto ejecutable para sistemas operativos Windows, garantizando que el personal de la Unidad de Análisis pueda operar el sistema de forma local y sin dependencia de instalaciones complejas de software.

2. Pilar de Inteligencia Epidemiológica y Modelamiento Estocástico
   
•	Estandarización vía Tasas de Incidencia: Transicionar del análisis de volúmenes absolutos hacia el cálculo dinámico de tasas de consulta por cada 10.000 habitantes, permitiendo una comparación equitativa y con rigor estadístico entre territorios de distinta densidad poblacional.

•	Algoritmia de Vigilancia Avanzada: Implementar modelos de detección de exceso de demanda mediante la computación del P-Score y la construcción de Canales Endémicos dinámicos basados en cuartiles históricos prepandemia (2014-2019), estableciendo umbrales críticos de "Alarma" y "Epidemia".

•	Filtrado de Ruido Estadístico: Aplicar técnicas de suavizado mediante medias móviles centradas para aislar la varianza estocástica inter-semanal, revelando el vector de tendencia real de los brotes epidémicos.

3. Pilar de Modelamiento Predictivo

•	Desarrollo de Regresión Armónica Ponderada: Implementar un motor predictivo basado en Mínimos Cuadrados Ponderados, diseñado específicamente para capturar la estacionalidad de los virus respiratorios. Modelo predictivo desarrollado tanto para evaluación de carga asistencial como para evaluación de desarrollo anual por diagnosticos preponderantes

•	Mitigación de Sesgos Post-Pandémicos: Aplicar un esquema de ponderación diferencial que otorgue mayor relevancia estadística a la "nueva normalidad" (años 2023 en adelante) frente a la historia antigua, ajustando la magnitud de las proyecciones a la realidad inmunológica actual de la población.


4. Pilar de Visualización de Datos y UX Analítica

•	Interfaz de Alta Reactividad: Diseñar un Dashboard interactivo basado en una gramática de visualización declarativa, que permita realizar drill-down multivariable (por comuna, establecimiento, grupo etario y patología) con latencias de respuesta mínimas, facilitando una interpretación rápida en entornos de alta presión directiva.

# Fuente de datos

- Fuente: Base de datos publica del MINSAL que contiene data referente a números de atenciones de urgencias de causas respiratorias por semana epidemiológica
- Periodo analizado: 2014 - 2026
- Frecuencia: semanal (semana epidemiologica
- Nivel de analisis: Servicio de salud
- Dataset demográfico (INE) con proyecciones poblacionales a nivel comunal

# Metodología de Procesamiento y Análisis de Datos

El ecosistema analítico se fundamenta en un pipeline de datos robusto y una capa de modelamiento matemático diseñada para extraer el máximo valor de los registros clínicos. estas fueron las fases del procesamiento de la información:

• Limpieza y Validación de Datos

La materia prima (base SADU) requiere un estricto proceso de saneamiento para garantizar la integridad referencial antes de cualquier cálculo estadístico:

- Filtros de Dominio: Se aísla el universo de datos aplicando un filtro estricto por ServicioSaludGlosa == 'Servicio de Salud Talcahuano'.

- Depuración Clínica: Se eliminan los registros correspondientes a "Totales Generales" del sistema respiratorio para evitar el doble conteo estadístico. Asimismo, se excluyen las glosas de diagnóstico puro, tambien contenedores de totales que doblan el conteo, por COVID-19 (U07.1 y U07.2), focalizando el sistema en la vigilancia de los virus respiratorios tradicionales de la Campaña de Invierno. Se eliminan las siguientes columnas provenientes del dataset: EstablecimientoCodigo, RegionCodigo, ComunaCodigo, EstablecimientoCodigo, OrdenCausa ya que no aportaban valor al análisis objetivo y no presentaban peso técnico para elaborar algún análisis o visualización.

- Homologación Ortográfica: Para garantizar un cruce determinista con las bases del INE, se implementa un diccionario de expresiones regulares (Regex) que corrige variaciones ortográficas, tildes y mayúsculas en los nombres de comunas y regiones (Ej: "Tome" a "Tomé", "BíoBío" a "BioBío").

- Saneamiento Estructural: Se convierten las cadenas vacías o compuestas por espacios en objetos NaN nulos de Pandas, eliminando posteriormente las filas corruptas o incompletas. Las llaves de cruce (Anio, ComunaGlosa, grupo_etario) son forzadas a tipos de datos estrictos (enteros y strings sin espacios residuales).

• Transformaciones Realizadas

Para habilitar el análisis multidimensional y la compatibilidad con motores de visualización modernos, la estructura de la base de datos es mutada significativamente:

- Transformación Tidy Data (Unpivoting): La base del Minsal se distribuye nativamente en un formato "ancho" (Wide Data), donde cada rango etario es una columna. Mediante la operación matricial pd.melt(), la estructura se transpone a un formato "largo" (Long Data). La variable de edad pasa a ser un atributo categórico en las filas, permitiendo agrupaciones dinámicas (Group By).

- Integración Relacional (Left Join): Se ejecuta un cruce de bases entre el dataset clínico (SADU) y el dataset demográfico (INE). Se utilizan como llaves primarias compuestas el [Año, Comuna, Grupo Etario]. El sistema incluye un mecanismo de auditoría en tiempo de ejecución que alerta sobre la existencia de registros clínicos "huérfanos" (sin población asignada).

- Enmascaramiento de Capa Visual: En la fase de carga del Dashboard, se aplica una función de transformación en memoria (Run-time) que agrupa los Establecimientos según su capacidad resolutiva (Atención Hospitalaria vs. Atención Primaria Urgencia) y traduce los crípticos códigos de diagnóstico CIE-10 a nombres clínicos ejecutivos (ej. "J20-J21" a "Bronquiolitis"), manteniendo la base de datos subyacente intacta.

• Construcción de Indicadores

El sistema abandona el conteo de volúmenes absolutos para adoptar métricas de riesgo comparables y estandarizadas:

- Tasa de Incidencia Poblacional: Métrica principal del sistema. Calcula el riesgo real de un territorio eliminando el sesgo de densidad demográfica.
- Fórmula: (Atenciones Clínicas / Población INE del segmento) * 10.000 habitantes.
- Incluye protección algorítmica contra errores matemáticos fatales (ZeroDivisionError).

- P-Score (Desviación de Exceso): Indicador que cuantifica porcentualmente qué tan sobrecargada está la red frente a un escenario normal.
- Lógica: Compara la Tasa Actual frente a la Mediana Histórica Esperada (Q2 de la semana epidemiológica correspondiente entre 2014-2019).
- Fórmula: ((Tasa Actual - Mediana Histórica) / Mediana Histórica) * 100.

- Umbrales de Canal Endémico: Cálculo algorítmico de los límites de riesgo semanal basados en la historia prepandemia. Se dividen en Cuartil 1 (Zona de Éxito), Cuartil 2 (Mediana de Seguridad) y Cuartil 3 (Límite Epidémico o Alarma).

• Análisis Temporal

El tiempo es tratado como una variable crítica para entender la dinámica de propagación viral:

- Aislamiento de la Línea Base: Se determina analíticamente que el período 2014-2019 representa el comportamiento endémico "sano" (Línea Base). Los años 2020-2022 son excluidos de los patrones de normalidad debido a las anomalías estadísticas generadas por las cuarentenas.

- Filtro Pasa-Bajos (Media Móvil): Dado que el registro semanal es estocástico y presenta alta volatilidad (ruido de fin de semana o reportes atrasados), el sistema aplica un algoritmo de Media Móvil Centrada parametrizable. Esto suaviza la curva y permite a la directiva observar el verdadero vector geométrico de crecimiento o descenso de un brote epidémico.

• Análisis Territorial

- Focalización Relativa vs. Absoluta: Al basar el análisis territorial en "Tasas de Incidencia", el sistema evalúa la "Presión" real sobre la infraestructura local, visibilizando si una comuna pequeña o rural se encuentra bajo mayor estrés per cápita que los grandes nodos urbanos, a pesar de tener un menor volumen total de pacientes.

- Granularidad Espacial: Permite navegar sin fricción desde el análisis Macro (todo el Servicio de Salud Talcahuano), descendiendo al estrato Meso (Comuna específica), hasta llegar al estrato Micro (comportamiento intra-semanal de un Hospital o SAPU particular).

• Modelo Predictivo

Para dotar al sistema de capacidad prospectiva, se desarrolló un motor de Regresión Armónica Ponderada, diseñado específicamente para modelar epidemias respiratorias.

- Ingeniería de Características: El tiempo lineal se transforma en un espacio cíclico mediante funciones trigonométricas (senos y cosenos representando armónicos de ciclos anuales y semestrales). Esto permite al algoritmo matemático comprender la periodicidad estacional del invierno.

- Asignación de Pesos Estocásticos: Para proyectar el futuro sin caer en el sesgo de la "deuda inmunológica" del encierro, el modelo entrena con toda la historia disponible (excluyendo 2020-2022, años de pandemia y cuarentenas) pero aplica un multiplicador matricial estricto: la historia antigua (2014-2019) tiene un peso de 1x, mientras que los datos de la "nueva normalidad" (2023 en adelante) reciben un peso de 5x.

- Proyección y Evaluación: El modelo proyecta la curva esperada de las 52 semanas del año objetivo. Si el año ya cuenta con registros reales, el sistema ejecuta una auto-auditoría calculando en tiempo real el MAPE (Error Porcentual Absoluto Medio) y el MAE (Error Absoluto Medio), cruzando luego la proyección contra el límite histórico (Q3) para disparar advertencias tempranas de colapso de la red asistencial.

# Arquitectura de Indicadores y Métricas

El sistema implementa una batería de indicadores estadísticos estandarizados que transforman los datos en métricas objetivas de riesgo

- Tasa de Incidencia Ajustada (Presión Poblacional): Es el indicador primario del sistema. Permite medir el riesgo real de enfermar o consultar en un territorio determinado, independientemente de su tamaño demográfico. El sistema calcula la tasa ajustada por cada 10.000 habitantes. Tasa = (Atenciones/Poblacion)*10.000
El código implementa una máscara booleana para ignorar denominadores iguales a 0 y prevenir excepciones fatales.

Propósito: Estandarizar la carga asistencial para lograr equidad en la comparación y priorización de recursos territoriales.

Ejemplo de Aplicación en el Proyecto: Si en la semana epidemiológica 24 el Hospital Las Higueras (Talcahuano) recibe 500 consultas respiratorias y el Hospital de Tomé recibe 100, el volumen bruto sugeriría enfocar la ayuda en Talcahuano. Sin embargo, al aplicar el indicador poblacional, el dashboard revela que la Tasa de Tomé es de 85 por 10.000 hab., mientras que la de Talcahuano es de solo 30 por 10.000 hab. Esto levanta una alerta objetiva de que la red de Tomé está bajo un estrés per cápita tres veces mayor, requiriendo apoyo urgente.

- Canal Endémico (Percentiles Históricos): Herramienta calculada de forma dinámica por el sistema. Define el "corredor de normalidad" esperado para cada semana del año, basándose en la historia prepandemia (2014-2019). El sistema opta por percentiles (estadística robusta) en lugar de promedios para evitar que años con brotes anómalos distorsionen la línea base.
Formulación:
   Q1 (Percentil 25): Límite inferior (Zona de Éxito)
   Q2 (Mediana): Comportamiento central esperado (Zona de Seguridad)
   Q3 (Percentil 75): Límite superior de normalidad histórica (Umbral de Alarma/Epidemia)

Propósito: Proveer un marco de referencia visual y algorítmico que permita al sistema clasificar automáticamente si la carga actual de pacientes es normal, moderada o derechamente un brote epidémico.

Ejemplo de Aplicación en el Proyecto: En la pestaña "Visión Estratégica", el algoritmo cruza la tasa actual contra el límite Q3. Si en la semana 20 la Tasa es de 45, y el límite Q3 histórico es 40, el sistema inyecta automáticamente una tarjeta visual roja con el estado "EPIDEMIA: Activar Plan de Contingencia", sin que el epidemiólogo tenga que interpretar manualmente la curva.

* P-Score: cuantifica qué tan grave es la desviación. Es un indicador de exceso relativo que mide la sobrecarga porcentual de la red frente al escenario basal (Mediana o Q2)

$$
\text{P-Score}=\left(\frac{\text{Tasa}_{\text{Actual}}-Q2_{\text{Historico}}}{Q2_{\text{Historico}}}\right)\times 100
$$

Propósito: Medir la magnitud del estrés operativo de la red asistencial en términos porcentuales, facilitando la comunicación ejecutiva de la crisis a directivos no clínicos.

Ejemplo de Aplicación en el Proyecto: El sistema identifica automáticamente la semana con el mayor exceso. Si el indicador marca +65.2%, la dirección del hospital sabe empíricamente que la demanda actual supera en más de un 60% a la capacidad habitual de respuesta para esa fecha, justificando técnica y financieramente la apertura de camas extraordinarias o la contratación de turnos de refuerzo. Si el valor es negativo (ej. -10%), indica holgura en el sistema (Déficit de atenciones respecto a lo normal).

* Métricas de Evaluación del Modelo Predictivo

Para garantizar que el modelo de Regresión Armónica Ponderada sea confiable, el sistema integra algoritmos de auto-evaluación. Cuando el usuario visualiza un año en curso (donde existen datos reales para comparar contra lo proyectado), el sistema calcula el error predictivo.

Indicadores Utilizados:

MAPE (Mean Absolute Percentage Error):

$$
\mathrm{MAPE}=\frac{1}{n}\sum_{i=1}^{n}\left|\frac{y_i-\hat{y}_i}{y_i}\right|\times 100
$$

Mide el error en porcentaje. Es altamente intuitivo para la toma de decisiones.

MAE (Mean Absolute Error):

$$
\mathrm{MAE}=\frac{1}{n}\sum_{i=1}^{n}\left|y_i-\hat{y}_i\right|
$$

Mide el error en la misma magnitud del dato (puntos de Tasa de Incidencia).

Propósito: Proveer transparencia y auditoría continua sobre la precisión del algoritmo matemático. Evita que el equipo clínico confíe a ciegas en un modelo descalibrado.

Ejemplo de Aplicación en el Proyecto: El sistema presenta una tarjeta denominada "Desviación del Modelo". Si proyectamos el comportamiento de la Bronquiolitis y el sistema indica un MAPE de ±12% y un MAE de ±3.5 puntos, el encargado de visualización comprende que la proyección de la semana "Peak" tiene un margen de error mínimo y altamente aceptable para la planificación de camas pediátricas. Si un modelo arroja un MAPE > 40%, el sistema lo resalta en color naranja/rojo, advirtiendo que la volatilidad del virus hace que la predicción sea menos confiable.
