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

- Filtro Media Móvil: Dado que el registro semanal es estocástico y presenta alta volatilidad (ruido de fin de semana o reportes atrasados), el sistema aplica un algoritmo de Media Móvil Centrada parametrizable. Esto suaviza la curva y permite a la directiva observar el verdadero vector geométrico de crecimiento o descenso de un brote epidémico.

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

# Hallazgos relevantes

El sistema analítico presentará los hallazgos clave correspondientes al año 2025, utilizando un conjunto de datos anual completo. Este enfoque metodológico es totalmente replicable para la proyección del año 2026.

<img width="1250" height="573" alt="image" src="https://github.com/user-attachments/assets/3667dd74-86df-462c-b266-294d428da587" />

* El análisis del canal endémico anual revela que las líneas de tendencia de la demanda asistencial se mantienen predominantemente en la zona epidemiológica de éxito.
<img width="1281" height="403" alt="image" src="https://github.com/user-attachments/assets/c1da9c43-75ed-4d12-bdd9-edf2d055284c" />

* El análisis mediante el indicador P-Score muestra que, semana a semana, existe un margen de holgura en la carga asistencial en comparación con la media histórica esperada.

<img width="1811" height="750" alt="image" src="https://github.com/user-attachments/assets/35514516-1b38-45b6-a911-97de0d4d0408" />

Utilizando las tasas poblacionales ajustadas, el análisis permite establecer el ranking de las comunas con mayor presión asistencial, obteniendo los siguientes resultados:
1° Penco con una tasa de 6.05
2° Tomé con una tasa de 3.50
3° Hualpén con una tasa de 3.19

La carga asistencial por enfermedades, quedando en:
1° IRA Alta con tasa de 17.93
2° Bronquiolitis con tasa de 10.75
3° Neumonía 1.64

y los establecimientos con mayor carga, quedando en top 3:
1° SAR Penco con tasa de 7.64
2° Hospital Las Higueras con tasa de 6.49
3° SAR Dr. Alberto Reyes con tasa de 5.48

<img width="1817" height="420" alt="image" src="https://github.com/user-attachments/assets/ce22460c-9208-48e1-b42c-91dfa2f945b4" />

Adicionalmente, el sistema permite realizar observaciones detalladas a nivel etario y por perfil clínico, contrastando en las mismas visualizaciones la carga absorbida por la atención hospitalaria versus la atención primaria de urgencia.

<img width="1811" height="551" alt="image" src="https://github.com/user-attachments/assets/e6b2df3d-4d4a-40a6-9882-6ff266464f6a" />

Las salidas del modelo predictivo se estructuran por semana epidemiológica, integrando múltiples capas analíticas en una única visualización. El gráfico contrasta el límite máximo histórico esperado (umbral Q3) con la tasa real registrada (puntos negros). Simultáneamente, la proyección de la carga asistencial anual se despliega mediante un diagrama de barras codificado por color: azul para volúmenes bajo control y rojo para advertir excesos que perforan el umbral crítico.

La información consolidada en cada visualización proporciona una visión panorámica y en tiempo real del Servicio de Salud en su totalidad. Este ecosistema analítico dota a la directiva de herramientas fundamentadas en datos para optimizar la toma de decisiones críticas, tales como la distribución eficiente de recursos financieros y humanos, la identificación temprana de las semanas peak, y la anticipación de las causas clínicas que exigirán un mayor abastecimiento de insumos y refuerzo de la dotación médica.

# Descripción del dashboard

El sistema de vigilancia de urgencia respiratoria ha sido diseñado bajo la arquitectura de un sistema de soporte a la toma de decisiones, trascendiendo la mera exposición estática de gráficos para ofrecer un entorno de exploración dinámica y multidimensional. En su capa de entrada, el sistema proporciona una visión panorámica y de diagnóstico inmediato mediante rankings territoriales y clínicos, permitiendo a la directiva identificar en segundos los nodos de la red bajo mayor estrés y los vectores virales predominantes. Al profundizar en el análisis, la plataforma despliega su motor de inteligencia epidemiológica, el cual no solo grafica las tasas de atención, sino que las somete a evaluación matemática: filtra el ruido estadístico mediante curvas suavizadas, computa el porcentaje exacto de sobrecarga operativa a través del P-Score y construye canales endémicos dinámicos que clasifican automáticamente el estado de la red (desde "Seguridad" hasta "Epidemia") basándose en la historia prepandémica.

Más allá del monitoreo en tiempo real, el sistema dota a los gestores de herramientas operativas granulares que posibilitan perfilar el flujo de pacientes, contrastando, por ejemplo, la presión absorbida por la Atención Primaria frente a la complejidad de los recintos hospitalarios, e identificando con precisión cómo distintos grupos etarios saturan la red según patologías específicas. Este enfoque territorial y demográfico desmitifica el sesgo de los volúmenes absolutos, evidenciando mediante tasas ajustadas poblacionalmente qué comunas periféricas requieren intervenciones urgentes a pesar de presentar números totales aparentemente menores. Finalmente, la plataforma culmina su ciclo de valor mediante un módulo de proyección, que utiliza algoritmos de regresión armónica ponderada para anticipar el comportamiento futuro de la curva epidémica. Esta capacidad predictiva, desglosable incluso por enfermedades específicas como la Neumonía o la Bronquiolitis, actúa como un radar a futuro que evalúa márgenes de error estadístico y levanta alertas tempranas sobre colapsos inminentes, asegurando que la gestión de camas, la reconversión de unidades y el abastecimiento de insumos críticos se ejecuten de manera proactiva y basada íntegramente en evidencia.

# Ejecución del proyecto

La ejecución y puesta en marcha, cuenta con dos vertientes, la primera es mediante la implementacion con Pyinstaller de un archivo .Exe empaquetado con todas las librerias y bases de datos necesarias. Para utilizar esta variable, solo es necesario dar doble click al archivo de ejecución y se desplegará el sistema en su totalidad.

La segunda vertiente mas modular, es mediante la ejecucion del script de lanzamiento del dashboard mediante con los codigos en python. La linea de acción es la siguiente:

1° Instalar las dependencias necesarias: pip install streamlit pandas numpy altair duckdb requests pyarrow
2° Si se procesan desde 0 las bases de datos (en caso de reproducibilidad para otro servicio de salud que no sea Talcahuano) se deben ejecutar los scripts en el siguiente orden:
   1-> PipelineServicioTalcahuanoCompleto.py - Este script hara la limpieza y la unificación de la base de datos del INE (proyecciones poblacionales para el       calculo de tasas) y el dataset SADU. El dataset SADU se limpiara y se adaptara, el dataset INE ya esta perfecto tal cual se sube en este proyecto para cualquier comuna
   2-> pruebaPSCORELOESSyREGRESIONARMONICA.py - Solo es necesario ejecutar este script para el lanzamiento del dashboard, ya que el actualizador y el arrancar_sistema son complementarios y se llaman para cumplir funciones.
3° La linea en consola de comandos de ejecución del dashboard es la siguiente streamlit run pruebaPSCORELOESSyREGRESIONARMONICA.py - Se debe navegar hasta la carpeta en donde se encuentren los scripts y las bases de datos

# Supuestos y limitaciones

* Calidad y Cobertura de los Datos

  El ecosistema analítico se fundamenta en el cruce determinista de la base de Atenciones de Urgencia y las proyecciones demográficas del INE, lo que conlleva ciertas limitaciones inherentes que deben considerarse al interpretar los resultados. En primer lugar, respecto a la cobertura territorial e institucional, el sistema mapea de forma exclusiva los establecimientos formalmente integrados a la red pública de urgencias del Servicio de Salud Talcahuano, abarcando Hospitales, SAPU, SAR y SUR. Al no incorporar la carga asistencial absorbida por la red privada de salud ni las atenciones derivadas del sistema mutual, el volumen total reflejado en el dashboard subestima inevitablemente la presión viral real que circula en la población total. Por lo tanto, el sistema debe comprenderse como una herramienta que mide de manera estricta y exclusiva el estrés operativo que recae sobre la infraestructura pública, y no como un censo absoluto de morbilidad respiratoria.

  La calidad e integridad del dato clínico presenta un margen de desviación asociado al contexto en que se genera el registro. Aunque la plataforma asume la base SADU como su fuente oficial de verdad, la tipificación del diagnóstico se realiza habitualmente durante el proceso en el box de atención inicial. En este entorno de alta presión asistencial, la categorización tiende a ser sindromática; un paciente puede ser ingresado rápidamente bajo el rótulo de "IRA Alta" inespecífica, a pesar de que el cuadro clínico subyacente —confirmado días después mediante imagenología o laboratorio— pudiese ser una Neumonía o una infección por Sincicial. Por consiguiente, las proporciones patológicas y perfiles que despliega la herramienta deben ser interpretados por la directiva médica como motivos de sospecha inicial y demanda de atención aguda, y no necesariamente como diagnósticos de egreso confirmados.

  La dinámica temporal de la ingesta de datos y el comportamiento social frente a la enfermedad introducen variables adicionales al análisis. Desde el punto de vista técnico, los repositorios de datos abiertos del Minsal operan mediante procesos de carga por lotes de frecuencia semanal, lo que introduce una latencia natural en el sistema; el escenario más actualizado del dashboard reflejará siempre el comportamiento de la semana epidemiológica inmediatamente anterior, requiriendo que las decisiones tácticas intradía se complementen con información local del recinto. A esto se suma el fenómeno del subregistro oculto por ausentismo clínico, ya que el modelo algorítmico cuantifica las interacciones efectivas con la red de salud, pero no a las personas enfermas que optan por el autocuidado o la automedicación. Derivado de esto, las caídas abruptas en la curva de atenciones deben analizarse con cautela, pues pueden responder a factores ambientales que desincentivan el traslado a la urgencia, como frentes de mal tiempo o feriados prolongados, en lugar de evidenciar una verdadera disminución en la circulación del virus.

* Periodos atípicos

   Por regla general, los virus respiratorios exhiben un comportamiento estacional cíclico y matemáticamente predecible. Sin embargo, la irrupción de la pandemia de COVID-19 representó un quiebre estructural sin precedentes en la serie de tiempo histórica del sistema. Durante el periodo comprendido entre los años 2020 y 2022, la implementación generalizada de medidas poblacionales no farmacológicas (por ejemplo: confinamientos estrictos, cierre prolongado de recintos educacionales, distanciamiento físico y uso universal de mascarillas) alteró drásticamente el ecosistema patológico. Estas intervenciones externas suprimieron casi en su totalidad la circulación endémica de los vectores respiratorios tradicionales, como el Virus Respiratorio Sincicial y la Influenza, generando un "valle" estadístico anómalo. Este escenario no obedeció a la dinámica natural de las enfermedades, sino a una interrupción artificial de la movilidad humana, lo que invalida estos datos para el cálculo de promedios o medianas de comportamiento habitual.

   Esta supresión prolongada originó un segundo fenómeno clínico conocido como "deuda inmunológica", el cual desencadenó brotes desfasados en sus fechas habituales y de una magnitud inusitada una vez que se levantaron las restricciones sanitarias, evidenciando un cambio transitorio en la susceptibilidad de la población. Para evitar que este evento disruptivo estadístico corrompa la lógica analítica de la plataforma, el código fuente incorpora un filtro metodológico de exclusión explícita. En la construcción del Canal Endémico y en el cálculo del indicador de exceso P-Score, el sistema aísla y descarta deliberadamente los datos correspondientes al trienio pandémico (2020-2022). De esta manera, el "corredor de normalidad" o línea base esperada se ancla exclusivamente en la historia prepandémica (2014-2019), garantizando que los umbrales de Alarma y Epidemia (Q3) se comparen siempre contra un estado de funcionamiento operativo de la red genuinamente estandarizado, evitando que la baja demanda de la cuarentena subestime artificialmente la capacidad real de respuesta del Servicio de Salud.

   La segregación algorítmica de estos periodos atípicos se transfiere también al motor de modelamiento predictivo. La Regresión Armónica Ponderada excluye por diseño el clúster pandémico durante su fase de entrenamiento, puesto que forzar al modelo a buscar patrones cíclicos en años donde la estacionalidad fue erradicada inyectaría un sesgo que arruinaría la convergencia del algoritmo matemático. Para compensar esta omisión y no perder de vista el comportamiento actual del virus, el sistema asimila la estructura geométrica de la curva prepandemia (con un peso estadístico de valor 1), pero implementa una matriz de ponderación que asigna un multiplicador de peso equivalente superior a los años correspondientes a la "nueva normalidad" (2023 en adelante). Mediante esta arquitectura híbrida, la plataforma mitiga exitosamente el ruido estadístico de la cuarentena, pero ajusta con precisión sus proyecciones futuras a la realidad inmunológica contemporánea de la población.

* Limitaciones del modelo

  El modelo de Regresión Armónica Ponderada, diseñado para proyectar la carga asistencial futura, opera bajo una serie de limitaciones estructurales y matemáticas que deben ser consideradas al momento de consumir sus resultados.

  La principal restricción del modelo radica en su arquitectura univariante autoregresiva. El algoritmo fue diseñado para ser altamente portátil y autosuficiente, por lo que proyecta la demanda utilizando de manera exclusiva la variable temporal (semanas del año transformadas trigonométricamente) y la historia de atenciones de la propia red. Corolario de lo anterior, el modelo es ciego ante variables exógenas (covariables) que poseen una influencia demostrada en la propagación de enfermedades respiratorias. El sistema no ingesta datos meteorológicos (descensos bruscos de temperatura o humedad relativa), no monitorea episodios críticos de contaminación ambiental y no integra el calendario escolar. Al carecer de estos predictores externos, el modelo confía íntegramente en que el patrón estacional endémico se repetirá fielmente, lo que puede generar desviaciones si el invierno en curso presenta anomalías climáticas extremas.

  Esta limitante no es "tallada en piedra" ya que, de contar con bases de datos anexas como por ejemplo, datos meteorologicos complementarios, se podria hacer una interconexion con lo existente y modificar el modelo predictivo para tener una exactitud mayor. Lo trabajado en el presente proyecto, no cuenta con los insumos necesarios para agregar dichas variables en el contexto actual del autor.

   Una segunda limitación crítica es la sensibilidad del modelo frente a patógenos altamente mutagénicos o condicionados por la intervención humana. El supuesto de estacionalidad armónica funciona con notable precisión y bajo error para predecir brotes de Bronquiolitis o exacerbaciones de IRA Alta. Sin embargo, su desempeño se degrada significativamente al modelar el comportamiento de la Influenza. Dado que este virus presenta cepas cambiantes año a año y su curva epidemiológica puede ser aplanada drásticamente por el éxito o fracaso de las Campañas de Vacunación de Invierno, el algoritmo histórico resulta insuficiente para prever la magnitud exacta o el desplazamiento temporal de su peak.

   Finalmente, debe considerarse la degradación del intervalo de confianza en el horizonte predictivo a largo plazo. Si bien el algoritmo calcula una proyección para las semanas del año, la fiabilidad matemática de la estimación decae a medida que la proyección se aleja de la fecha actual de análisis. En su uso práctico, el modelo demuestra ser una herramienta altamente confiable para la planificación táctica de corto y mediano plazo —proyectando con precisión el comportamiento de la red a 4 u 8 semanas vista, permitiendo la reconversión oportuna de camas—, pero no debe ser interpretado como un oráculo determinista para escenarios a 6 meses, requiriendo una evaluación continua frente a los datos reales que ingresan semana a semana al sistema.

* Interpretación de los resultados

  Para evitar sesgos cognitivos o acciones operativas desproporcionadas, se establecen los siguientes lineamientos para la lectura de los resultados

  1° La Tasa no es Gravedad: Cuando el dashboard indica que una comuna específica (ej. Tomé) presenta la mayor Tasa de Incidencia poblacional, esto certifica rigurosamente que su red de urgencias está recibiendo el mayor flujo de pacientes per cápita. Sin embargo, esta métrica no infiere la complejidad o gravedad de dichos cuadros. El sistema actual contabiliza atenciones, pero no integra indicadores de categorización de riesgo ni tasas de conversión a hospitalización en unidades de cuidados intensivos

  2° Volatilidad en Comunas Menores: Al desagregar el análisis P-Score a nivel comunal o por centro de salud, se debe tener especial precaución con los territorios de baja densidad poblacional. En establecimientos pequeños, el teorema del límite central se debilita.
  
  Si un SAR rural registra históricamente 3 pacientes pediátricos por Sincicial en una semana, y en el periodo actual recibe 9 pacientes, el sistema alertará matemáticamente un P-Score del +200% (Alerta Roja). Aunque estadísticamente correcto, operativamente 9 pacientes pueden ser un volumen absorbible sin requerir planes de contingencia masivos. Toda alerta matemática debe ser siempre ponderada cualitativamente contra la capacidad resolutiva neta del recinto.

  3° El Ruido Estocástico vs. La Tendencia: La curva de datos reales suele presentar valles agudos durante los fines de semana o peaks de un solo día (ruido estocástico). Un cruce puntual de la línea cruda por sobre el umbral de Epidemia no constituye necesariamente un brote sostenido.

   La decisión de declarar un estado de emergencia o activar la apertura de camas extraordinarias debe basarse primariamente en la observación de la Línea de Tendencia Suavizada (Media Móvil). Si la línea suavizada perfora el límite Q3, se confirma que el vector geométrico de crecimiento es real y sostenido

  4° El modelo predictivo funciona como un "radar meteorológico": altamente útil para marcar la dirección de la tormenta, pero cuyos márgenes temporales exactos requieren ajuste constante a medida que se acorta la brecha de tiempo.

  La evaluación de los avisos en el modelo predictivo debe estar supeditada a un análisis de los indicadores de error MAPE y MAE.

# Reproducibilidad

La plataforma destaca por su alta reproducibilidad y adaptabilidad. Con ajustes mínimos en el código fuente —como la modificación de los territorios de análisis— el modelo puede ser replicado para otros Servicios de Salud o expandido a nivel nacional, garantizando la autonomía institucional sin dependencia del creador original del software.

Además, aunque el sistema se entrega actualmente empaquetado en un formato autoejecutable (.exe) para facilitar su uso, el equipo administrador posee total libertad para definir cómo desea gestionar, distribuir y desplegar esta herramienta tecnológica en el futuro.

# Autoría

Autor: Camilo Garcés
Dirección del proyecto: Camila Pallalever
