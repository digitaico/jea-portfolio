# /mnt/disc2/local-code/jea-portfolio/ats/src/utils/file_converter.py

import io
import logging
from PyPDF2 import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

def convert_pdf_to_text(pdf_bytes: bytes, filename: str = "unknown.pdf") -> str:
    """
    Converts PDF bytes content to text.

    Args:
        pdf_bytes (bytes): The content of the PDF file as bytes.
        filename (str): The name of the file, used for logging purposes.

    Returns:
        str: The extracted text from the PDF.
    """
    logger.info(f"Attempting to convert PDF file: {filename}")
    text = ""
    try:
        pdf_file_obj = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file_obj)
        for page in reader.pages:
            text += page.extract_text() or ""
        logger.info(f"Successfully converted PDF file: {filename}")
    except Exception as e:
        logger.error(f"Error converting PDF file '{filename}': {e}", exc_info=True)
    return text.strip()

def convert_docx_to_text(docx_stream: io.BytesIO, filename: str = "unknown.docx") -> str:
    """
    Converts DOCX stream content to text.

    Args:
        docx_stream (io.BytesIO): The stream of the DOCX file.
        filename (str): The name of the file, used for logging purposes.

    Returns:
        str: The extracted text from the DOCX.
    """
    logger.info(f"Attempting to convert DOCX file: {filename}")
    text = ""
    try:
        document = Document(docx_stream)
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        logger.info(f"Successfully converted DOCX file: {filename}")
    except Exception as e:
        logger.error(f"Error converting DOCX file '{filename}': {e}", exc_info=True)
    return text.strip()

# You might also want a TXT converter if you foresee issues with direct read().decode()
# def convert_txt_to_text(txt_bytes: bytes, filename: str = "unknown.txt") -> str:
#     """
#     Converts TXT bytes content to text.
#
#     Args:
#         txt_bytes (bytes): The content of the TXT file as bytes.
#         filename (str): The name of the file, used for logging purposes.
#
#     Returns:
#         str: The extracted text from the TXT.
#     """
#     logger.info(f"Attempting to convert TXT file: {filename}")
#     try:
#         return txt_bytes.decode('utf-8').strip()
#     except Exception as e:
#         logger.error(f"Error converting TXT file '{filename}': {e}", exc_info=True)
#         return ""