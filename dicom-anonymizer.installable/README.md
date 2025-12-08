# ANONIMIZADOR DICOM

Este paquete existe para Anonimizer imagenes medicas en formato DICOM en `Bulk` o en lote.

Se puede instalar en cualquier sistema operativo siempre que este instalado `Python 3.8+`. 

Uso:

    `python dicom_anonymizer.py --folder /path/to/dicom/folder --store /path/to/output/folder`


### _Campos reemplazados_
- PatientID
- PatientName
- PatientAddress
- PatientTelephoneNumbers

### _Campos preservados_
- PatientAge
- PatientSex
- Todos los demas datos, imagenes y estructura permanecen sin cambios.

Autor: Jorge Eduardo Ardila
Santa Marta
2025-09-17
jea.data@gmail.com
