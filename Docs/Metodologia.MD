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
