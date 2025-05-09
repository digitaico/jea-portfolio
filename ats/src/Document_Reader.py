# Document_Reader.py

import io
import fitz # PyMuPDF
import docx
import os

class Document_Reader:
    """
    A class to read text content from different document types (PDF, DOCX, TXT).
    """
    def read_document(self, file_obj: io.BytesIO, filename: str) -> str:
        """
        Reads the text content from a file-like object based on its filename extension.

        Args:
            file_obj (io.BytesIO): A file-like object containing the document data.
            filename (str): The original name of the file, including extension.

        Returns:
            str: The extracted text content, or an empty string if reading fails or type is unsupported.
        """
        # Get the file extension in lowercase
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()

        text = ""

        try:
            if file_extension == '.pdf':
                text = self._read_pdf(file_obj)
            elif file_extension == '.docx':
                text = self._read_docx(file_obj)
            elif file_extension == '.txt':
                text = self._read_txt(file_obj)
            else:
                print(f"Unsupported file type: {file_extension}")
                # Optionally return a specific error message or None
                pass # Return empty string for unsupported types

        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            # Optionally return a specific error message or None
            text = "" # Ensure text is empty on error

        return text

    def _read_pdf(self, file_obj: io.BytesIO) -> str:
        """Reads text from a PDF file-like object."""
        text = ""
        try:
            # Open the PDF from the bytes object
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error reading PDF: {e}")
            text = ""
        return text

    def _read_docx(self, file_obj: io.BytesIO) -> str:
        """Reads text from a DOCX file-like object."""
        text = ""
        try:
            # Open the DOCX from the bytes object
            doc = docx.Document(file_obj)
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            text = ""
        return text

    def _read_txt(self, file_obj: io.BytesIO) -> str:
        """Reads text from a TXT file-like object."""
        # For text files, simply decode the bytes
        try:
            # Attempt common encodings
            text = file_obj.read().decode('utf-8')
        except UnicodeDecodeError:
             try:
                 text = file_obj.read().decode('latin-1') # Try another common one
             except Exception as e:
                 print(f"Error decoding TXT file: {e}")
                 text = ""
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            text = ""

        return text

# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Document_Reader.py directly for testing.")

    # Create dummy files for testing (requires dummy content)
    # Example: create a dummy.txt
    # with open("dummy.txt", "w") as f:
    #     f.write("This is a test text file.")

    # Example of how you might test (requires a file on disk)
    # try:
    #     with open("dummy.txt", "rb") as f:
    #         file_content = io.BytesIO(f.read())
    #         reader = Document_Reader()
    #         text = reader.read_document(file_content, "dummy.txt")
    #         print(f"\nText from dummy.txt:\n{text}")
    # except FileNotFoundError:
    #      print("\nCannot run example usage: dummy.txt not found.")
    # except Exception as e:
    #      print(f"\nAn error occurred during example usage: {e}")

    print("\nDocument_Reader class is ready to be used in the main application.")