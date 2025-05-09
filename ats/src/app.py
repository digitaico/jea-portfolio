# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import os
import sys # Import sys to check execution context for NLTK printing

# Import your classes with capitalized filenames
from Resume_Scorer import Text_Processor, Resume_Scorer
from Document_Reader import Document_Reader
from Skill_Extractor import Skill_Extractor
from Resume_Parser import Resume_Parser


# --- Configuration Constants ---
# Define your weights, model names, patterns, and section multipliers here.
# These can come from environment variables, a config file, or be hardcoded as constants.
# Using constants here based on our discussion.

SPACY_MODEL_NAME = os.environ.get('SPACY_MODEL', 'en_core_web_md') # Using 'en_core_web_md' as requested

# Scoring Weights (ensure sum <= 1.0)
TFIDF_SCORE_WEIGHT = float(os.environ.get('TFIDF_WEIGHT', 0.3))
SKILL_MATCH_SCORE_WEIGHT = float(os.environ.get('SKILL_WEIGHT', 0.7))

# Requirement Weights (align keys with Skill_Extractor pattern labels)
# These determine the base value of matching an item from this category in the JD.
REQUIREMENT_WEIGHTS_CONFIG = {
    "REQUIRED_SKILL_PHRASE": 1.5,
    "YEARS_EXPERIENCE": 1.2,
    "QUALIFICATION_DEGREE": 1.0,
    "KNOWLEDGE_OF": 0.8,
    "CORE_SKILL": 1.0, # Label used for PhraseMatcher matches in Skill_Extractor
    "Unidentified": 0.2, # Lower weight for patterns matched in unidentified sections
    # Add weights for any other custom pattern labels you add in Skill_Extractor
}

# Section Multiplier Weights (align keys with Resume_Parser headings)
# These multipliers adjust the base item weight based on the section(s) where it was found in the resume.
# Multiplier of 1.0 means no change to the base weight. > 1.0 increases, < 1.0 decreases.
SECTION_MULTIPLIERS_CONFIG = {
     "Experience": 1.5, # Items in Experience get 50% bonus multiplier
     "Skills": 1.0,     # Items in Skills get base multiplier
     "Education": 0.8,  # Items in Education get 20% less multiplier
     "Projects": 1.1,   # Small bonus for items in Projects
     "Summary": 0.9,    # Slightly lower
     "Unidentified (Header)": 0.5, # Low multiplier for items before first heading
     "Unidentified (Footer)": 0.5, # Low multiplier for items after last heading
     "Unidentified (Full Document)": 0.5, # Low multiplier if no sections found
     "Unidentified": 0.5, # Fallback if section is labeled "Unidentified" by parser/extractor
     # Add multipliers for other section headings Resume_Parser identifies
}

# Skill_Extractor Matcher Patterns
# Define the structure as List[Tuple[str, List[List[Dict]]]].
# The second element of the tuple is a list containing one or more pattern lists (each a List[Dict]).
SKILL_MATCHER_PATTERNS_CONFIG = [
     ("REQUIRED_SKILL_PHRASE", [[{"LOWER": "required"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] , [{"LOWER": "must"}, {"LOWER": "have"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] ]), # Label with two patterns
     ("YEARS_EXPERIENCE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "+", "OP": "?"}, {"LOWER": "years"}, {"LOWER": "of", "OP": "?"}, {"LOWER": "experience"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}] ]), # Label with one pattern
     ("KNOWLEDGE_OF", [[{"LOWER": "knowledge"}, {"LOWER": "of"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}] ]), # Label with one pattern
     ("QUALIFICATION_DEGREE", [[{"LOWER": {"IN": ["bachelor's", "master's", "bachelor", "master", "bs", "ms"]}}, {"LOWER": "degree", "OP": "?"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] ]), # Label with one pattern
     # Add other custom patterns here following the same (label, [pattern_list1, pattern_list2]) format
]

# Core Skill Phrases for PhraseMatcher
# These are exact phrases to match as core skills. Add more from the JD text provided earlier.
CORE_SKILL_PHRASES_CONFIG = ["Python", "Java", "SQL", "AWS", "Flask", "Django", "React", "Docker", "Git", "Node.js", "C#", "RESTful APIs", "web services", "microservices architecture", "Back-End Developer", "Computer Science", "Software Engineering"]


# --- Flask App Setup ---

app = Flask(__name__)
CORS(app) # Enable CORS (Cross-Origin Resource Sharing)


# Instantiate dependencies once when the app starts
# Pass configuration constants during instantiation
# Text_Processor needs to be language-aware per request, but instantiate a default app instance
text_processor_app_instance = Text_Processor(language='english') # App instance uses a default language


# --- Add these print statements BEFORE instantiating Skill_Extractor ---
print("\n--- Debugging Skill_Extractor Configuration from app.py ---")
print(f"SKILL_MATCHER_PATTERNS_CONFIG being passed: {SKILL_MATCHER_PATTERNS_CONFIG}")
print(f"CORE_SKILL_PHRASES_CONFIG being passed: {CORE_SKILL_PHRASES_CONFIG}")
print("---------------------------------------------")


skill_extractor_app_instance = Skill_Extractor(
    model_name=SPACY_MODEL_NAME,
    requirement_patterns=SKILL_MATCHER_PATTERNS_CONFIG, # Pass patterns config
    core_skill_phrases=CORE_SKILL_PHRASES_CONFIG # Pass core phrases config
)

resume_parser_app_instance = Resume_Parser(model_name=SPACY_MODEL_NAME) # Pass model name config


# Check if dependencies are functional (especially spaCy models loaded correctly)
# Access the .nlp attribute from the instantiated dependencies
if skill_extractor_app_instance.nlp is None or resume_parser_app_instance.nlp is None:
     print("\n---")
     print("FATAL ERROR: One or more spaCy models failed to load in dependencies.")
     print(f"Ensure spaCy model '{SPACY_MODEL_NAME}' is downloaded.")
     print(f"Run: python -m spacy download {SPACY_MODEL_NAME}")
     print("---")
     app_functional = False # Set a flag
else:
     print(f"\n--- JEMATS Backend Starting ---")
     print(f"SpaCy model loaded: {SPACY_MODEL_NAME}")
     print(f"TF-IDF Weight: {TFIDF_SCORE_WEIGHT}")
     print(f"Skill Weight: {SKILL_MATCH_SCORE_WEIGHT}")
     print(f"Total Score Weight: {TFIDF_SCORE_WEIGHT + SKILL_MATCH_SCORE_WEIGHT}")
     # print(f"Requirement Weights: {REQUIREMENT_WEIGHTS_CONFIG}") # Optional: print full config
     # print(f"Section Multipliers: {SECTION_MULTIPLIERS_CONFIG}") # Optional: print full config
     print("-" * 25)
     app_functional = True


@app.route('/score', methods=['POST'])
def get_score():
    """
    API endpoint to receive file upload, job description text, and language.
    Expects multipart/form-data. Returns multiple scores and details.
    """
    # Check the app_functional flag before processing requests
    if not app_functional:
         # Return a Service Unavailable status if the app is not functional
         return jsonify({"error": "JEMATS backend is not fully initialized due to dependency loading errors. Please check server logs."}), 503


    # --- 1. Get data from the incoming request ---
    job_description = request.form.get('job_description')
    # Get language from form data, default to 'english' if not provided
    language = request.form.get('language', 'english')
    resume_file = request.files.get('resume_file')

    # --- 2. Validate essential inputs ---
    if not job_description or not resume_file:
        return jsonify({"error": "Missing job description or resume file in the request."}), 400

    if resume_file.filename == '':
         return jsonify({"error": "No selected resume file was provided."}), 400

    # --- 3. Use Document_Reader to extract text from the resume file ---
    # Document_Reader is stateless, instantiate per request is fine.
    reader = Document_Reader()
    resume_file.seek(0) # Ensure file pointer is at the beginning
    resume_text = reader.read_document(io.BytesIO(resume_file.read()), resume_file.filename)


    if not resume_text:
        # Return a specific error if text extraction failed
        return jsonify({"error": f"Could not read text from the uploaded file '{resume_file.filename}'. Please check the file type (.pdf, .docx, .txt supported) or ensure it's not corrupted."}), 400

    # --- 4. Use Resume_Scorer for calculating scores ---
    try:
        # Instantiate Text_Processor per request for language awareness based on user selection
        text_processor_instance_per_request = Text_Processor(language=language)

        # Instantiate Resume_Scorer with all app-level dependencies and configuration
        # Pass functional instances of Skill_Extractor and Resume_Parser
        scorer_instance = Resume_Scorer(
            text_processor=text_processor_instance_per_request, # Use request-level Text_Processor
            skill_extractor=skill_extractor_app_instance,      # Use app-level Skill_Extractor
            resume_parser=resume_parser_app_instance,          # Use app-level Resume_Parser
            tfidf_weight=TFIDF_SCORE_WEIGHT,                   # Pass weights from config constants
            skill_match_weight=SKILL_MATCH_SCORE_WEIGHT,
            requirement_weights=REQUIREMENT_WEIGHTS_CONFIG,    # Pass requirement weights config
            section_weights=SECTION_MULTIPLIERS_CONFIG         # Pass section weights config
        )

        # Calculate scores using the raw texts (Resume_Scorer handles parsing/extraction internally)
        # Ensure the scorer instance is functional before calling calculate_scores
        if not hasattr(scorer_instance, '_functional') or not scorer_instance._functional:
             return jsonify({"error": "Scoring engine is not functional due to upstream dependency issues."}), 500


        scores = scorer_instance.calculate_scores(job_description, resume_text)

        # --- 5. Return the results as JSON ---
        # scores dictionary contains: tfidf_score, prioritized_skill_score, combined_score, matched_items, missing_items
        return jsonify(scores)


    except Exception as e:
        # Log the error details for debugging on the server side
        print(f"An unexpected error occurred during scoring request:")
        import traceback
        traceback.print_exc() # Print full traceback to the console

        # Return a more generic error message to the frontend
        return jsonify({"error": "An internal error occurred during scoring. Please check the server logs for details."}), 500


# --- Main execution block ---
if __name__ == '__main__':
    # Run the Flask app in debug mode
    # debug=True provides helpful error pages and auto-reloading during development
    # In production, debug should be False
    app.run(debug=True)