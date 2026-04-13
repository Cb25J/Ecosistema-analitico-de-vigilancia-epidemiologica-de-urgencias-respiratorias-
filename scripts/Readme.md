# RECORDATORIO
Para ejecutar el proceso completo, se debe descargar la base de datos SADU en crudo desde https://datos.gob.cl/dataset/atenciones-de-urgencia-causas-respiratorias
Si es la primera vez que se ejecuta, primero se descarga la base de datos en crudo, luego se ejecuta el script PipelineServicioTalcahuanoCompleto para crear la base de datos cruzada entre el dataset de salud y el dataset del INE. La base de datos resultante tendrá como nombre base_talcahuano_final_tasa_ok.parquet
El dataset SADU se actualiza cada miercoles

El dataset INE es siempre el mismo, no tiene cambios y se subio listo para cualquier aplicación y adecuación al proyecto
