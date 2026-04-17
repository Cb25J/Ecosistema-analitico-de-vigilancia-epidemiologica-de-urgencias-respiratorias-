# Descripción General

El presente proyecto constituye un Ecosistema Analítico y Sistema de Soporte a la Toma de Decisiones diseñado para la vigilancia epidemiológica avanzada de la red de urgencias del Servicio de Salud Talcahuano.

La finalidad es analizar la evolución temporal y territorial de la demanda de consultas de urgencia respiratoria con un estricto enfoque en la gestión sanitaria y la optimización de recursos hospitalarios.

El sistema propone una metodología basada en inteligencia de datos, estructurada sobre tres pilares analíticos:

* 1° Inteligencia Territorial y Equidad Estadística: Transiciona del conteo de pacientes al cálculo de Tasas de Incidencia Ajustadas (por cada 10.000 habitantes), integrando bases clínicas del Minsal (SADU) con proyecciones demográficas del INE. Esto permite identificar la presión real per cápita que sufren los recintos de atención primaria (SAPU/SAR) y hospitalaria, revelando focos de estrés en comunas periféricas que los números brutos suelen ocultar.

* 2° Vigilancia Algorítmica: Automatiza la construcción de Canales Endémicos históricos y el cálculo del P-Score (porcentaje de exceso de demanda). Esto otorga a la red la capacidad de clasificar objetivamente si una semana estadística se encuentra en fase de éxito, seguridad, alarma o epidemia declarada.

* 3° Modelamiento Predictivo: Implementa un motor de Regresión Armónica Ponderada capaz de aprender el ciclo estacional de los virus respiratorios y proyectar la carga asistencial a las semanas epidemiologicas anuales.

En su conjunto, este desarrollo metodológico transforma repositorios masivos de datos crudos en herramientas visuales reactivas, dotando a la plana directiva y a los equipos de epidemiología de la capacidad para anticipar el colapso de la red, reconvertir camas de manera oportuna y focalizar financieramente la dotación de insumos y personal médico allí donde la predicción matemática y la evidencia territorial lo exijan.

# Ingeniería y Limpieza de Datos

El repositorio de datos abiertos del Ministerio de Salud presenta alta variabilidad en su calidad de registro, lo que impedía inicialmente su integración algorítmica. Para transformar este conjunto de datos, en un conjunto auditable, se diseñó un pipeline iterativo que resuelve problemas de integridad estructural, ortográfica y semántica.

Otro problema grave que se presentó cuando el desarrollo ya llevaba un alto porcentaje de avance fue que el dataset cambió sin previo aviso en algunas de sus glosas, incorporando más faltas de ortografía y modificando nombres tanto en columnas técnicas como en diagnósticos. Esto generó un retroceso en los tiempos de desarrollo, ya que fue necesario auditar nuevamente el dataset para identificar las nuevas circunstancias. Se espera que este fenómeno no vuelva a ocurrir durante un largo período de tiempo; sin embargo, de suceder, será necesario volver a adaptar el script de limpieza de datos.

El dataset presenta un total de 25 columnas, las cuales son: EstablecimientoCodigo, EstablecimientoGlosa, RegionCodigo, RegionGlosa, ComunaCodigo, ComunaGlosa, ServicioSaludCodigo, ServicioSaludGlosa, TipoEstablecimiento, DependenciaAdministrativa, NivelAtencion, TipoUrgencia, Latitud, Longitud, NivelComplejidad, Anio, SemanaEstadistica, OrdenCausa, Causa, NumTotal, NumMenor1Anio, Num1a4Anios, Num5a14Anios, Num15a64Anios, Num65oMas

Las columnas EstablecimientoCodigo, RegionCodigo, ComunaCodigo, EstablecimientoCodigo, OrdenCausa se eliminaron físicamente a modo de limpieza del dataset, ya que no entregan valor alguno al sistema.

Durante las fases iniciales de exploración, se detectó que los registros brutos contenían anomalías que alteraban significativamente las métricas, destacando la presencia de filas correspondientes a "Totales Generales" precalculados que generaban duplicidad matemática en las sumatorias. Para resolver esto, el sistema integró un filtro de exclusión por glosa clínica que purga estas redundancias. Adicionalmente, dado que el objetivo metodológico del modelo predictivo es evaluar la estacionalidad tradicional de la Campaña de Invierno, se excluyeron deliberadamente los registros cuyo único diagnóstico era COVID-19, aislando de esta forma el comportamiento endémico y cíclico de virus clásicos como el Sincicial, la Influenza y el Adenovirus.

El mayor desafío estructural se presentó al intentar consolidar la información poblacional. El cruce relacional entre la base clínica del SADU y las proyecciones demográficas del INE fallaba de forma sistemática debido a la ausencia de llaves primarias unificadas y a múltiples variaciones ortográficas (como discrepancias en tildes, capitalización de letras y espacios residuales invisibles en los nombres de las comunas). Para garantizar una tasa de convergencia demográfica del 100% y evitar la pérdida de "datos huérfanos", se programó un módulo de normalización basado en Expresiones Regulares (Regex) en Python, el cual estandariza exhaustivamente la nomenclatura de ambas bases antes de autorizar cualquier operación de emparejamiento (Left Join).

Paralelamente, se abordó la inestabilidad computacional provocada por celdas vacías o con caracteres en blanco que generaban excepciones fatales en la librería Pandas al calcular las tasas de incidencia. La solución consistió en rastrear estas anomalías sintácticas y forzar su conversión al objeto nulo estándar de la computación numérica (numpy.nan). Una vez controlados los vacíos, el pipeline descarta automáticamente aquellas filas que carezcan de variables críticas de identificación territorial o clínica, asegurando la robustez de los cálculos posteriores.

Finalmente, la arquitectura misma de la base original suponía un obstáculo para el análisis multidimensional. La data del Minsal se distribuye en un formato "ancho", donde cada rango etario ocupa una columna independiente; una disposición que imposibilita la agrupación dinámica de datos y el renderizado interactivo en visualizadores modernos. Para habilitar estas capacidades en el dashboard, se ejecutó una refactorización estructural mediante la función melt, transponiendo la base y pivotando las edades hacia una sola variable categórica en las filas.

En una primera instancia, el proyecto se concebía como un análisis nacional de la información. Sin embargo, al observar la enorme cantidad de datos, los problemas ortográficos presentes en numerosas columnas y la existencia de datos ambiguos en el dataset original, se decidió reducir la cobertura al nivel de servicio de salud, con el fin de mantener un sentido de territorialidad más acotado.

Esta decisión resultó ser un gran acierto territorial, ya que permite una vigilancia supeditada al territorio y a los establecimientos que lo componen, favoreciendo una revisión minuciosa y comparativa de estos en un marco común.

# Transformaciones realizadas

Una vez que el repositorio superó las fases de limpieza e integridad relacional, el pipeline de datos ejecutó una serie de transformaciones estructurales y matemáticas. Este proceso tuvo como objetivo elevar la base de datos desde un mero registro transaccional hacia una matriz enriquecida, optimizada tanto para la visualización analítica como para el consumo de los algoritmos de predicción.

El primer gran desafío analítico consistió en la agrupación y homologación de causas respiratorias. La base cruda medica presenta una alta granularidad diagnóstica que, si bien es útil para el registro clínico individual, genera un exceso de ruido en visualizaciones ejecutivas y diluye el poder estadístico de los modelos. Para resolver esto, se diseñó un diccionario de mapeo determinista que reclasificó las descripciones técnicas largas y los códigos en categorías epidemiológicas macro. Por ejemplo, glosas complejas como "Bronquitis/bronquiolitis aguda (J20-J21)" fueron sintetizadas algorítmicamente bajo la etiqueta limpia "Bronquiolitis". Esta clusterización permitió aislar los cuatro vectores de mayor impacto en la campaña de invierno (IRA Alta, Bronquiolitis, Neumonía e Influenza), habilitando al sistema para correr proyecciones independientes por patología.

En el ámbito de la equidad territorial, se implementó la transformación estadística más importante del sistema: el cálculo de Tasas de Incidencia ajustadas por población. Evaluar la carga asistencial observando únicamente el volumen absoluto de atenciones sesga profundamente la toma de decisiones, ya que las comunas con mayor densidad poblacional (como Talcahuano) siempre dominarán los gráficos, ocultando crisis en sectores periféricos. Para neutralizar este sesgo demográfico, el código generó una nueva métrica computando la división exacta entre las atenciones semanales y la proyección poblacional específica del INE para ese grupo etario y comuna, multiplicando el resultado por un factor base de 10.000 habitantes. Durante este cálculo matricial, se inyectaron máscaras de seguridad en Python (Poblacion > 0) para evitar excepciones fatales por división por cero. El resultado de esta transformación es la variable maestra del dashboard: una tasa estandarizada que permite descubrir que recintos en comunas más pequeñas (como Tomé o Penco) a menudo soportan una presión per cápita muy superior al promedio de la red.

Para dotar a la plataforma de capacidades de inteligencia operativa, se ejecutó una clasificación estructural de la red asistencial. A través de funciones de evaluación de cadenas de texto, el sistema analizó la glosa nominal de cada establecimiento de salud para generar una nueva dimensión analítica denominada Nivel de Gestión. Los centros cuyas nomenclaturas incluían los términos "SAPU", "SAR" o "SUR" fueron agrupados bajo el clúster de Atención Primaria de Urgencia, mientras que los recintos de alta complejidad fueron categorizados como Atención Hospitalaria. Esta variable transformada es la que permite al dashboard mapear la carga de pacientes, evidenciando visualmente cómo las patologías pueden congestionar cada categoria en mayor o menor medida.

Finalmente, el motor predictivo exigió una profunda ingeniería de variables temporales y cíclicas. El algoritmo de Regresión Armónica Ponderada no puede procesar fechas lineales de manera óptima si se busca modelar estacionalidad biológica. Por ello, la variable lineal de las semanas estadísticas fue sometida a Transformadas de Fourier Parciales. El script calculó el índice continuo del tiempo y generó cuatro nuevas variables trigonométricas: los senos y cosenos correspondientes a los ciclos anuales y semestrales (sin1, cos1, sin2, cos2). Esta compleja transformación geométrica del tiempo es la llave matemática que le permite al algoritmo de regresión "entender" la naturaleza cíclica del año, garantizando que el modelo proyecte de forma fluida la transición de la demanda entre la ultima semana epidemiologica del año y la semana 1 del año siguiente.

# Cálculo de indicadores

* Tasa de Incidencia Asistencial Ajustada

El uso de volúmenes absolutos de atención es metodológicamente deficiente para la comparación territorial, ya que penaliza visualmente a las comunas con mayor densidad habitacional. Para establecer un criterio de equidad estadística, el sistema convierte todas las métricas a Tasas de Incidencia.

Esta transformación se calcula dividiendo el número de consultas de urgencia por la población de riesgo específica (según proyecciones del INE para esa comuna y año), estandarizando el resultado a una base de 10.000 habitantes.

La formula sería. Tasa = (Atenciones/Poblacion)*10.000

Esta métrica es el "denominador común" de todo el ecosistema analítico, permitiendo comparar de forma simétrica la verdadera presión operativa (estrés del sistema) entre comunas demográficamente asimétricas.

* P-Score (Cuantificación del Exceso de Demanda)

Para medir matemáticamente la gravedad de un brote actual respecto a la normalidad, el dashboard implementa el cálculo del P-Score. Originado como un indicador para medir excesos de mortalidad, en este proyecto se adaptó para medir el exceso de demanda asistencial.

El P-Score evalúa la desviación porcentual de la tasa de consultas de una semana específica frente a su valor basal esperado (la mediana histórica o Q2 para esa misma semana).

Ejemplo de interpretación: Un P-Score de +50% indica que la red está absorbiendo una vez y media su carga normal. Un P-Score negativo indica holgura operativa. Esta métrica es fundamental para justificar financieramente la activación de planes de contingencia, ya que traduce la saturación clínica a un porcentaje auditable.

* Tendencias Suavizadas

La recolección diaria/semanal de datos en urgencias está altamente contaminada por ruido estocástico o administrativo: caídas abruptas de atención durante feriados largos, tormentas climáticas que impiden el traslado, o picos de atención los días lunes. Si un modelo o un analista observa la curva "cruda", este ruido puede interpretarse erróneamente como el fin o el inicio de un brote.Para aislar la "señal" real del virus, el sistema aplica un algoritmo de Media Móvil Centrada. Este suavizado matemático promedia dinámicamente una ventana de semanas (n semanas hacia atrás y hacia adelante), absorbiendo la volatilidad y revelando el vector geométrico real (crecimiento o decaimiento) de la curva epidémica, lo que resulta vital para la toma de decisiones directivas sin caer en falsas alarmas.

* Construcción del Canal Endémico

El núcleo de la vigilancia estratégica del sistema es el Canal Endémico. Esta es una herramienta gráfica y matemática que define científicamente la "frontera de normalidad" del Servicio de Salud, calculando umbrales de riesgo basados en la historia prepandémica (2014-2019).

El algoritmo agrupa la serie de tiempo histórica por semana epidemiológica (1 a 53) y calcula tres percentiles clave, dividiendo el comportamiento del virus en cuatro zonas de riesgo automatizadas:

Cuartil 1 (Q1 - 25%): Zona de Éxito. Las tasas actuales se encuentran por debajo del 25% de los inviernos históricos. Holgura total en la red.

Cuartil 2 (Q2 - 50%): Mediana (Zona de Seguridad). Comportamiento viral habitual y completamente manejable por la dotación estándar del hospital.

Cuartil 3 (Q3 - 75%): Límite Endémico (Zona de Alarma). La demanda entra al 25% superior de la historia del recinto. Actúa como gatillo de alerta temprana para iniciar reconversión de camas.

Sobre Q3: Zona de Epidemia. Cuando la línea de la tasa actual o la proyección del modelo predictivo perfora el umbral Q3, el sistema decreta un exceso estadístico crítico (colapso inminente), justificando intervenciones mayores a nivel de Servicio de Salud.

# Modelamiento Predictivo

Para dotar al ecosistema de capacidades prospectivas, se diseñó e implementó un motor de predicción algorítmica. El objetivo de este módulo es proyectar la carga asistencial a semanas epidemiologicas permitiendo a los tomadores de decisiones anticipar la semana exacta del peak viral y el riesgo de colapso de la red (cuando la demanda perfora el umbral Q3).

* Tipo de Modelo Utilizado

En el ámbito clínico, la interpretabilidad del algoritmo es tan crítica como su precisión. Por ello, se descartó el uso de modelos de Machine Learning como Random Forest o Redes Neuronales, los cuales tienden a sobreajustarse en series de tiempo con alta volatilidad. Se efectuaron pruebas con estos modelos y debido a la volatilidad de los datos, estos presentaron indices de error muy altos

En su lugar, el sistema implementa un modelo de Regresión Armónica Ponderada. Este es un enfoque estadístico multivariante diseñado específicamente para capturar la estacionalidad biológica rígida de los virus respiratorios. El modelo ajusta una curva matemática fluida a través de los datos históricos utilizando Mínimos Cuadrados, pero con la particularidad de asignar "pesos" distintos a diferentes épocas del tiempo. Su principal ventaja es que resulta extremadamente ligero a nivel computacional, altamente interpretable y muy resistente al ruido diario.

* Variables

El modelo opera de manera univariante y autoregresiva, lo que significa que aprende exclusivamente del comportamiento histórico del propio virus a través del tiempo, sin requerir variables externas. Las características matemáticas procesadas en el entrenamiento son:
  
  Variable Objetivo: La Tasa de Incidencia Asistencial Ajustada (atenciones estandarizadas por cada 10.000 habitantes).

  Variable Temporal Continua: El algoritmo convierte el "Año" y la "Semana" en un índice de tiempo continuo, medido en semanas exactas transcurridas desde el inicio de la serie temporal (año base 2014)

  Componentes Armónicos (Características Exógenas): Para que el modelo pueda "entender" y predecir los ciclos repetitivos (como los inviernos), el índice de tiempo lineal es sometido a Transformadas de Fourier Parciales.

* Matriz de Ponderación

Entrenar un modelo con una serie de tiempo que incluye el evento de la pandemia de COVID-19 destruiría su capacidad predictiva, ya que las cuarentenas impusieron un comportamiento plano y anómalo (ausencia total de virus tradicionales) que no obedece a la biología estacional.

Para resolver este desafío estructural y evitar un sesgo en los estimadores matemáticos, el diseño del conjunto de entrenamiento incorpora tres reglas lógicas de Ponderación Estocástica:

1° Exclusión Absoluta: El algoritmo identifica y elimina completamente los años de la pandemia (2020, 2021 y 2022). Estos datos son declarados como valores atípicos extremos (outliers sistémicos) y no participan en la resolución de las ecuaciones.

2° Historia Base (Peso = 1.0): Se inyectan los datos correspondientes al periodo prepandémico (2014 a 2019). El modelo los utiliza para "aprender" la geometría base, la estacionalidad normal y el comportamiento cíclico tradicional de los patógenos. A estos registros se les asigna un multiplicador de impacto estándar

3° Nueva Normalidad Inmunológica (Peso = 5.0): Para garantizar que el pronóstico futuro refleje el estado inmunológico y demográfico más actual de la población, el sistema prioriza los años posteriores a la pandemia (2023 hasta la actualidad). Mediante la matriz diagonal de ponderación de la regresión WLS, a estos años recientes se les asigna matemáticamente un peso equivalente a 5 veces el de la historia antigua.

Esta arquitectura híbrida asegura que el modelo posea la robustez de un gran volumen de datos históricos, pero con la agilidad necesaria para adaptarse a los cambios virales contemporáneos.

# Supuestos

Para que las métricas y las proyecciones de este sistema sean matemáticamente válidas y operativamente útiles, el diseño asume como verdaderos los siguientes supuestos fundamentales:

* Representatividad y Validez del Registro Clínico

El sistema asume que los registros de la base de datos nacional (SADU) representan de manera fidedigna la realidad epidemiológica que atraviesa la población. Esto se desglosa en dos premisas operativas:

1° Se asume que la red pública de urgencias (Hospitales, SAPU, SAR, SUR) absorbe una cuota de mercado lo suficientemente masiva como para que sus fluctuaciones sean estadísticamente válidas en relación del comportamiento viral de toda la comuna. Aunque el modelo no ingesta atenciones del sistema privado, se da por sentado que la curva de contagios en el sector público es paralela y proporcional a la carga viral total circulante.

2° Se asume que la codificación diagnóstica ingresada en la puerta de entrada de la urgencia, aunque puede no ser el diagnóstico definitivo de egreso, es "direccionalmente correcta". Es decir, si el sistema registra un alza del 40% en "IRA Alta", el modelo asume que efectivamente hay un brote de patología respiratoria alta en curso, confiando en el criterio clínico inicial como un clasificador válido para el cluster de la enfermedad.

* Estacionalidad Biológica y Tratamiento de la Anomalía Pandémica

El modelo asume matemáticamente que los virus respiratorios tradicionales poseen una naturaleza inherentemente cíclica, repitiendo sus patrones de propagación en sintonía con las estaciones del año y las bajas temperaturas.

Derivado del supuesto anterior, el sistema asume que el periodo comprendido entre 2020 y 2022 representó una anomalía artificial provocada por intervenciones humanas (cuarentenas, cierre de colegios, uso de mascarillas), y no un cambio en la biología del virus. Por lo tanto, se da por sentado que eliminar este periodo del conjunto de entrenamiento es la decisión estadísticamente correcta para no "contaminar" al algoritmo.

A partir del año 2023, la dinámica de transmisión viral retornó a su comportamiento armónico natural. Al aplicar un multiplicador de peso mayor (5x) a los años recientes, el sistema asume que la "nueva normalidad" inmunológica de la población es el predictor más fuerte del futuro, pero que la "forma" geométrica de la ola epidémica sigue obedeciendo a la historia prepandémica (2014-2019).

# Limitaciones

A pesar de la robustez de las transformaciones y el rigor matemático del motor predictivo, este ecosistema analítico opera bajo restricciones inherentes a la disponibilidad de la información y la arquitectura del modelo. Para una correcta interpretación de las alertas generadas por el sistema, se deben considerar las siguientes limitaciones estructurales:

* Sesgos Inherentes en la Captura de Datos

La base de datos SADU captura de manera exclusiva las interacciones que ocurren dentro de la red pública de salud. Al no estar integradas las atenciones de clínicas privadas, centros médicos particulares ni de la red mutual (accidentes laborales con complicaciones respiratorias), la Tasa de Incidencia calculada por el sistema representa una cota inferior de la realidad. El dashboard mide con extrema precisión el estrés de la red estatal, pero subestima el volumen total de morbilidad respiratoria de la provincia.

El registro del código se realiza habitualmente en el box de categorización inicial bajo un contexto de urgencia. Esto genera un sesgo hacia clasificaciones genéricas o sindromáticas (ej. agrupar múltiples patologías bajo el rótulo de "IRA Alta") debido a la falta de confirmación inmediata por laboratorio (paneles virales PCR). Por consiguiente, los desgloses del dashboard por causa específica deben interpretarse como tendencias de "sospecha clínica inicial" y no como confirmaciones virológicas absolutas.

* Ausencia de Covariables Exógenas

Factores Meteorológicos y Ambientales: El modelo no ingesta flujos de datos sobre temperaturas mínimas, humedad relativa ni alertas ambientales por alta concentración de material particulado, los cuales disparan directamente las crisis obstructivas y cuadros asmáticos.

Dinámica Social y Demográfica: El algoritmo no está programado para identificar cambios en la movilidad urbana ni asimilar el calendario escolar (como el inicio adelantado de las vacaciones de invierno), factores que aplanan o aceleran drásticamente la curva de contagios pediátricos.

Al carecer de estos predictores multidimensionales, el modelo confía plenamente en que el ciclo estacional se comportará de manera estándar. Si un invierno en particular presenta anomalías climáticas extremas (ej. olas de frío polar imprevistas), el algoritmo reaccionará con cierto rezago, aumentando su margen de error predictivo al no poder anticipar el impacto inmediato de dicho evento meteorológico. Para solventar esto, si a futuro se cuenta con data respecto a, por ejemplo, cambios meteorologicos, se podria generar una implementacion de dicha data y ejecutar un modelo predictivo mas preciso con una alimnetación completa de datos complementarios,

