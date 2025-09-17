#!/usr/bin/env python3
"""
Script Anonimizador de DICOM
@Author: Jorge Eduardo Ardila
2025-09-17
https://github.com/digitaico/jea-portfolio/tree/master/dicom-anonymizer

Este script anonimiza archivos DICOM en una carpeta especificada reemplazando informacion
especifica del paciente con 'Anonimo'. Procesa todos los archivos DICOM recursivamente
dentro de la carpeta, preservando todos los demas datos incluyendo imagenes y estructura.

Campos reemplazados:
- PatientID
- PatientName
- PatientAddress
- PatientTelephoneNumbers

Campos preservados:
- PatientAge
- PatientSex
- Todos los demas datos, imagenes y estructura permanecen sin cambios.

Uso:
    python anonymize_dicom.py --folder /path/to/dicom/folder --store /path/to/output/folder
"""

import argparse
import sys
from pathlib import Path
from typing import List
import pydicom
import concurrent.futures
import multiprocessing

VALOR_ANONIMO = 'Anonimo'



def find_dicom_files(folder_path: Path) -> List[Path]:
    """
    Encuentra recursivamente todos los archivos en la carpeta.

    Args:
        folder_path: Ruta a la carpeta a buscar.

    Returns:
        Lista de rutas de archivos.
    """
    all_files = list(folder_path.rglob('*'))
    return [fp for fp in all_files if fp.is_file()]


def read_dicom_file(file_path: Path) -> pydicom.Dataset:
    """
    Lee archivos DICOM incluyendo pixeles.

    Args:
        file_path: Ruta al archivo.

    Returns:
        pydicom.Dataset: Lista de datos DICOM para ser iterada.
    """
    return pydicom.dcmread(file_path)


def anonymize_patient_info(ds: pydicom.Dataset) -> None:
    """
    Anonimiza campos especificos del paciente.

    Args:
        ds: Lista a anonimizar.
    """
    fields_to_anonymize = [
        'PatientID',
        'PatientName',
        'PatientAddress',
        'PatientTelephoneNumbers'
    ]

    for field in fields_to_anonymize:
        if hasattr(ds, field) and getattr(ds, field):
            setattr(ds, field,VALOR_ANONIMO)


def save_dicom_file(ds: pydicom.Dataset, output_path: Path) -> None:
    """
    Guarda los estudios anonimizados, preservando su integridad: formato DICOM.

    Args:
        ds: Lista de datos DICOM a guardar.
        output_path: Ruta donde guardar el archivo.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ds.save_as(str(output_path), write_like_original=True)


def verify_dicom_file(file_path: Path) -> bool:
    """
    Verifica la integridad de cada archivo DICOM guardado.

    Args:
        file_path: Ruta al archivo DICOM a verificar.

    Returns:
        bool: True si es valido, False en caso contrario.
    """
    try:
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
        # Check if essential elements are present
        has_pixel_data = (0x7fe0, 0x0010) in ds
        has_patient_name = hasattr(ds, 'PatientName')
        return has_pixel_data and has_patient_name
    except Exception:
        return False


def process_dicom_file(file_path: Path, output_path: Path, verbose: bool = True) -> None:
    """
    Procesa un archivo DICOM individual: lee, anonimiza, guarda y verifica.

    Args:
        file_path: Ruta al archivo DICOM de entrada.
        output_path: Ruta para guardar el archivo anonimizado.
        verbose: Argumento para imprimir info de progreso: Debugging.
    """
    try:
        if verbose:
            print(f"Procesando {file_path}")

        ds = read_dicom_file(file_path)
        anonymize_patient_info(ds)
        save_dicom_file(ds, output_path)

        if verify_dicom_file(output_path):
            if verbose:
                print(f"💯 Procesado exitosamente {output_path}")
        else:
            print(f"⚠️ Advertencia: Verificacion fallida para {output_path}")

    except Exception as e:
        print(f"Error procesando {file_path}: {e}")


def main() -> None:
    """
    Funcion principal para leer folder, validar archivos DICOM, reemplazar valores y guardar.
    """
    parser = argparse.ArgumentParser(
        description=f"Anonimiza archivos DICOM reemplazando informacion del paciente con {VALOR_ANONIMO}."
    )
    parser.add_argument(
        '--folder',
        required=True,
        help='Ruta a la carpeta que contiene estudios DICOM a procesar.'
    )
    parser.add_argument(
        '--store',
        required=True,
        help='Ruta a la carpeta donde se guardaran los estudios DICOM anonimizados.'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Habilitar print para debugging.',
        default='store_false'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=multiprocessing.cpu_count(),
        help=f'Numero de workers en paralelo (predeterminado: {multiprocessing.cpu_count()}).' # agilizar procesamiento en paralelo.
    )

    args = parser.parse_args()

    folder_path = Path(args.folder)
    store_path = Path(args.store)

    if not folder_path.is_dir():
        print(f"⚠️ Error: '{folder_path}' no es un directorio valido.", file=sys.stderr)
        sys.exit(1)

    # Crear carpeta de almacenamiento si no existe
    store_path.mkdir(parents=True, exist_ok=True)

    dicom_files = find_dicom_files(folder_path)

    if not dicom_files:
        print(f"⚠️ No se encontraron archivos en '{folder_path}'.")
        return

    print(f"✅ Encontrados {len(dicom_files)} archivos para procesar.")

    # Preparar tareas
    tasks = []
    for file_path in dicom_files:
        relative_path = file_path.relative_to(folder_path)
        output_path = store_path / relative_path
        tasks.append((file_path, output_path, args.verbose))

    # Procesar archivos en paralelo
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_dicom_file, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                task = futures[future]
                print(f"⚠️ Error procesando {task[0]}: {exc}")

    print("🎉 Anonimizacion completa.")


if __name__ == '__main__':
    main()