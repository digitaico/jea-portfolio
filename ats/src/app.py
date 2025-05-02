from flask import Flask, request, jsonify
from flask_cors import CORS
import io

# import methods from class ResumeScorrer
from Resume_Scorer import TextProcessor, ResumeScorer

# import class DocumentReader
from Document_Reader import DocumentReader

app = Flask(__name__)
CORS(app)

@app.route('/score', methods=['POST'])
def get_score():
    """
    API Endpoint to receive file upload, job description text and language
    return score
    multipart/form-data
    text data comes from request.form
    file comes from request.files
    """
    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume_file')

    # validation
    if not job_description or not resume_file:
        return jsonify({"error":"No job description or resume file."}), 400

    if resume_file.filename == '':
        return jsonify({"error": "No file was uploaded"}), 400

    # Extract text
    reader = DocumentReader()
    resume_text = reader.read_document(resume_file, resume_file.filename)

    if not resume_text:
        return jsonify({"error": "Could not read text from uploaded file. Check file type supported files: .pdf, .docx, .txt or check possible file corruption!"}), 400

    try:
        # Instantiate TextProcessor and ResumeScorer
        text_processor_instance = TextProcessor(language=language)
        scorer_instance = ResumeScorer(text_processor=text_processor, language = text_processor_instance.stop_words_lang)
        
        score = scorer_instance.calculate_score(job_description, resume_text)

        return jsonify({"score": score})

    except Exception as e:
        print(f"An error occurred during score calculation: {e}")
        # error message for Node server - UI
        return jsonify({"error": "An error occurred. Check server logs"}), 500

if __name__ == "__main__":
    app.run(debug=True)
