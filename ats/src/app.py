from flask import Flask, request, jsonify
from flask_cors import CORS
import io

# import methods from class ResumeScorrer
from Resume_Scorer import TextProcessor, ResumeScorer
# import class DocumentReader
from Document_Reader import DocumentReader
from Skill_Extractor import SkillExtractor

app = Flask(__name__)
CORS(app)

text_processor_app_instance = TextProcessor(language='english')
skill_extractor_app_instance = SkillExtractor(model_name='en_core_web_md')

# check if spaCy model failed to load
if skill_extractor_app_instance.nlp is None:
    print(f"FATAL ERROR: spaCy model failed to load. JEMATS cannot start.")
    spaCy_load_error = True
else:
    spaCy_load_error = False


@app.route('/score', methods=['POST'])
def get_score():
    """
    API Endpoint to receive file upload, job description text and language
    return score
    multipart/form-data
    text data comes from request.form
    file comes from request.files
    """
    if spaCy_load_error:
        return jsonify({"error":"Backend is not fully configures. spaCy model failed to load."}), 503 # service unavalilable

    job_description = request.form.get('job_description')
    resume_file = request.files.get('resume_file')
    language = request.form.get('language', 'english')

    # validation
    if not job_description or not resume_file:
        return jsonify({"error":"Missing job description or resume file."}), 400

    if resume_file.filename == '':
        return jsonify({"error": "No file was uploaded"}), 400

    # Extract text
    reader = DocumentReader()
    resume_text = reader.read_document(resume_file, resume_file.filename)

    if not resume_text:
        return jsonify({"error": "Could not read text from uploaded file. Check file type supported files: .pdf, .docx, .txt or check possible file corruption!"}), 400

# -- use ResumeScorrer for scoring ---
    try:
        # Instantiate TextProcessor and ResumeScorer
        text_processor_instance_per_request = TextProcessor(language=language)

        scorer_instance = ResumeScorer(
            text_processor=text_processor_instance_per_request,
            skill_extractor = skill_extractor_app_instance,
            language=language
        )
        print(f"ResumeScorer instance created : {scorer_instance}")
        
        scores = scorer_instance.calculate_scores(job_description, resume_text)
        #print(f"Score calculated: {scores}")

        return jsonify(scores)

    except Exception as e:
        print(f"An error occurred during score calculation: {e}")
        # error message for Node server - UI
        return jsonify({"error": "An error occurred during scoring. Please check server logs"}), 500

if __name__ == "__main__":
    app.run(debug=True)
