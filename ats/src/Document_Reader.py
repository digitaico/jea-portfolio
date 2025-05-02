import fitz # pymupdf
import docx # python-docx
import io # read files

class DocumentReader:
    """
    Methods of class Documentreader read text form documents in PDF, DOCX, TXT.
    """
    def read_pdf(self, file_obj: io.BytesIO) -> str:
        """
        Read text from PDF
        @params file_obj: io.BytesIO
        @returns str: extracted text.
        """
        text = ""
        try :
            # open the document
            doc = fitz.open(stream=file_obj.read(), filetype="pdf")
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return ""
        return text

    def read_docx(self, file_obj: io.BytesIO) -> str:
        text = ""
        try:
            document = docx.Document(file_obj)
            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX file: {e}")
            return ""
        return text

    def read_txt(self, file_obj: io.BytesIO) -> str:
        try:
            # read file must be UTF-8 encoded
            text = file_obj.read().decode('utf-8')
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            return ""
        return text

    def read_document(self, file_obj: io.BytesIO, filename: str) -> str:
        """
        Coordinator: by file extension he decides which method to call.
        """
        # Assess file type based on extension
        file_extension = filename.rsplit('.', 1)[-1].lower()
        match file_extension:
            case 'pdf':
                # Reset file pointer to beginning before reading
                file_obj.seek(0)
                return self.read_pdf(file_obj)
            case 'docx':
                file_obj.seek(0)
                return self.read_docx(file_obj)
            case 'text':
                file_obj.seek(0)
                return self.read_txt(file_obj)
            case _:
                print(f"Unsupported file type: .{file_extension}")
                return ""
