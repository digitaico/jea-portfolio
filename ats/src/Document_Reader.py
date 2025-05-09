# Document_Reader.py
# ya

import io
import os
import docx
# Using pdfminer.six for PDF text extraction as developed during debugging
from pdfminer.high_level import extract_text as extract_text_from_pdf # Alias to avoid name conflict


class Document_Reader:
    """
    A class to read text content from different document types (PDF, DOCX, TXT).
    Currently supports basic text extraction.
    """
    def read_document(self, file_stream: io.BytesIO, filename: str) -> str:
        """
        Reads text content from a file stream based on its filename extension.

        Args:
            file_stream (io.BytesIO): A BytesIO stream containing the file content.
            filename (str): The original name of the file, including extension.

        Returns:
            str: The extracted text content, or an empty string if reading fails or type is unsupported.
        """
        # Get the file extension in lowercase
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()

        text_content = ""

        # Ensure file_stream is a valid BytesIO object before proceeding
        if not isinstance(file_stream, io.BytesIO):
             print(f"Error: Invalid file stream provided for {filename}. Expected BytesIO.")
             return ""


        try:
            if file_extension == '.pdf':
                # Use pdfminer.six to extract text from PDF stream
                # pdfminer.six expects a file-like object
                file_stream.seek(0) # Ensure stream is at the beginning
                text_content = extract_text_from_pdf(file_stream)
            elif file_extension == '.docx':
                # Use python-docx to extract text from DOCX stream
                # python-docx needs a file-like object that supports seek and read
                file_stream.seek(0) # Ensure stream is at the beginning
                document = docx.Document(file_stream)
                paragraphs = [p.text for p in document.paragraphs]
                text_content = "\n".join(paragraphs)
            elif file_extension == '.txt':
                # Read plain text file
                # Assume UTF-8 encoding for text files
                file_stream.seek(0) # Ensure stream is at the beginning
                text_content = file_stream.getvalue().decode('utf-8')
            else:
                print(f"Warning: Unsupported file type for reading: {file_extension}")
                text_content = "" # Return empty string for unsupported types

        except Exception as e:
            # Log the error for debugging
            print(f"Error reading file {filename} with extension {file_extension}: {e}")
            text_content = "" # Return empty string on error

        return text_content.strip() # Return stripped text


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Document_Reader.py directly for testing.")

    # Create dummy file streams for testing
    dummy_txt_content = b"This is a plain text file.\nIt has two lines."
    # Note: Creating a dummy docx requires more complex structure than simple bytes
    # This example focuses on demonstrating the method call, actual docx reading
    # would require a valid docx byte stream. Skipping live docx generation in example.
    # For a basic pdfminer.six test, a simple PDF structure can be used.
    dummy_pdf_content = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj 4 0 obj<</Length 20>>stream\nBT /F1 12 Tf 72 712 Td (Hello World) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000107 00000 n\n0000000178 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n198\n%%EOF"


    # Instantiate the reader
    reader = Document_Reader()

    # Test reading a .txt file
    txt_stream = io.BytesIO(dummy_txt_content)
    txt_filename = "test.txt"
    txt_content = reader.read_document(txt_stream, txt_filename)
    print(f"\nReading {txt_filename}:")
    print(txt_content)

    # Test reading a dummy .pdf file (basic example, requires pdfminer.six)
    try:
        # Attempt to import a pdfminer module to check if it's installed
        from pdfminer.high_level import extract_text as _check_import
        pdf_stream = io.BytesIO(dummy_pdf_content)
        pdf_filename = "test.pdf"
        pdf_content = reader.read_document(pdf_stream, pdf_filename)
        print(f"\nReading {pdf_filename}:")
        print(pdf_content)
    except ImportError:
         print("\nSkipping PDF read test: pdfminer.six not installed (pip install pdfminer.six).")
    except Exception as e:
         print(f"\nError during dummy PDF test (ensure pdfminer.six is installed): {e}")


    # Test reading an unsupported file type
    unsupported_stream = io.BytesIO(b"dummy content")
    unsupported_filename = "test.jpg"
    unsupported_content = reader.read_document(unsupported_stream, unsupported_filename)
    print(f"\nReading {unsupported_filename}:")
    print(f"Content: '{unsupported_content}' (Expected empty string)")

    # Test reading an empty stream
    empty_stream = io.BytesIO(b"")
    empty_filename = "empty.txt"
    empty_content = reader.read_document(empty_stream, empty_filename)
    print(f"\nReading {empty_filename}:")
    print(f"Content: '{empty_content}' (Expected empty string)")

    # Test reading None input (should handle gracefully)
    none_content = reader.read_document(None, "test.txt")
    print(f"\nReading None stream:")
    print(f"Content: '{none_content}' (Expected empty string)")