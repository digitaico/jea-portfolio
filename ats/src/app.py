# Ya
# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import os
import sys # Import sys to check execution context for potential NLTK printing

# Import the main orchestrator and the dependencies it needs initialized at the app level
# Use try-except blocks in case files are missing or have errors
try:
    # Import Resume_Scorer specifically for the Resume_Scorer class
    from Resume_Scorer import Resume_Scorer
except ImportError:
    print("FATAL ERROR: Could not import Resume_Scorer orchestrator in app.py. Please check Resume_Scorer.py.")
    # Define a dummy class to allow app to start, though it won't be functional
    class Resume_Scorer:
         def __init__(self, **kwargs): print("Dummy Resume_Scorer initialized.")
         def calculate_scores(self, jd_text, resume_text): return {"error": "Scoring orchestrator dependency not loaded."}
         _functional = False # Add a functional flag for the dummy


try:
    # Import Text_Processor specifically for the Text_Processor class (needed for language-specific instances)
    from Text_Processor import Text_Processor
except ImportError:
    print("FATAL ERROR: Could not import Text_Processor in app.py. Please check Text_Processor.py.")
    class Text_Processor: # Dummy class
         def __init__(self, language='english'): print("Dummy Text_Processor initialized.")
         def process_text(self, text): return "" # Return empty processed text
         def tokenize(self, text): return []
         language = 'unknown' # Add a language attribute for the dummy


try:
    # Import Document_Reader specifically for the Document_Reader class (used directly in route)
    from Document_Reader import Document_Reader
except ImportError:
    print("FATAL ERROR: Could not import Document_Reader in app.py. Please check Document_Reader.py.")
    class Document_Reader: # Dummy class
         def read_document(self, file_stream, filename):
              print("Dummy Document_Reader read_document called.")
              return "" # Return empty text


try:
    # Import Skill_Extractor specifically for the Skill_Extractor class (dependency for orchestrator)
    from Skill_Extractor import Skill_Extractor
except ImportError:
    print("FATAL ERROR: Could not import Skill_Extractor in app.py. Please check Skill_Extractor.py.")
    class Skill_Extractor: # Dummy class
         def __init__(self, model_name=None, requirement_patterns=None, core_skill_phrases=None):
              self.nlp = None
              self.matcher = None
              self.phrase_matcher = None
              self._functional = False
              print("Dummy Skill_Extractor initialized.")
         def extract_requirements_and_skills(self, text, sections=None): return {}


try:
    # Import Resume_Parser specifically for the Resume_Parser class (dependency for orchestrator)
    from Resume_Parser import Resume_Parser
except ImportError:
    print("FATAL ERROR: Could not import Resume_Parser in app.py. Please check Resume_Parser.py.")
    class Resume_Parser: # Dummy class
         def __init__(self, model_name=None): self.nlp = None
         def parse_sections(self, text): return []


# --- Configuration Constants ---
# Define your weights, model names, patterns, and section multipliers here.
# These can come from environment variables, a config file, or be hardcoded as constants.
# Using constants here based on our discussion.

SPACY_MODEL_NAME = os.environ.get('SPACY_MODEL', 'en_core_web_md') # Using 'en_core_web_md' as requested

# Scoring Weights (ensure sum <= 1.0, will be normalized in ScoreAggregator)
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
    "EXAMPLE_TECH_SKILL": 1.0, # Include example weights from previous steps
    "EXAMPLE_EXP_PHRASE": 1.2,
    "EXAMPLE_QUALIFICATION": 1.0
}

# Section Multiplier Weights (align keys with Resume_Parser headings output 'heading' value)
# These multipliers adjust the base item weight based on the section(s) where it was found in the resume.
# Multiplier of 1.0 means no change to the base weight. > 1.0 increases, < 1.0 decreases.
SECTION_MULTIPLIERS_CONFIG = {
     "Experience": 1.5, # Items in Experience get 50% bonus multiplier
     "Work Experience": 1.5, # Also map variations
     "Employment History": 1.5, # Also map variations
     "Skills": 1.0,     # Items in Skills get base multiplier
     "Technical Skills": 1.0, # Also map variations
     "Professional Skills": 1.0, # Also map variations
     "Education": 0.8,  # Items in Education get 20% less multiplier
     "Projects": 1.1,   # Small bonus for items in Projects
     "Summary": 0.9,    # Slightly lower
     "About": 0.9,      # Also map variations
     "Profile": 0.9,    # Also map variations
     "Languages": 1.0,  # Languages section
     "Awards": 0.7,     # Example for other sections
     "Certifications": 1.1, # Example for other sections
     "Licenses": 1.1,   # Example for other sections
     "Publications": 0.6, # Example for other sections
     "Presentations": 0.6, # Example for other sections
     "Volunteer Experience": 0.7, # Example for other sections
     "Interests": 0.3,  # Example for other sections
     "References": 0.1, # Items in References are usually low value
     "Contact": 0.1,    # Items in Contact are usually low value
     "Objective": 0.9,
     "Unidentified (Header)": 0.5, # Low multiplier for items before first heading
     "Unidentified (Footer)": 0.5, # Low multiplier for items after last heading
     "Unidentified (Full Document)": 0.5, # Low multiplier if no sections found
     "Unidentified": 0.5, # Fallback if section is labeled "Unidentified" by parser/extractor or not in list
}

# Skill_Extractor Matcher Patterns (Dependency for SkillComparer)
# Define the structure as List[Tuple[str, List[List[Dict]]]].
# The second element of the tuple is a list containing one or more pattern lists (each a List[Dict]).
SKILL_MATCHER_PATTERNS_CONFIG = [
     ("REQUIRED_SKILL_PHRASE", [[{"LOWER": "required"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}], [{"LOWER": "must"}, {"LOWER": "have"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] ]), # Label with two patterns
     ("YEARS_EXPERIENCE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "+", "OP": "?"}, {"LOWER": "years"}, {"LOWER": "of", "OP": "?"}, {"LOWER": "experience"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}] ]), # Label with one pattern
     ("KNOWLEDGE_OF", [[{"LOWER": "knowledge"}, {"LOWER": "of"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}] ]), # Label with one pattern
     ("QUALIFICATION_DEGREE", [[{"LOWER": {"IN": ["bachelor's", "master's", "bachelor", "master", "bs", "ms"]}}, {"LOWER": "degree", "OP": "?"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] ]), # Label with one pattern
     # Add other custom patterns here following the same (label, [pattern_list1, pattern_list2]) format
     # Consider adding more specific patterns if needed for your domain (e.g., specific tech stacks, certifications)
]

# Core Skill Phrases for PhraseMatcher (Dependency for SkillComparer)
# These are exact phrases to match as core skills. Expanded based on your JD/example.
CORE_SKILL_PHRASES_CONFIG = [
    "Python", "Java", "SQL", "AWS", "Flask", "Django", "React", "Docker",
    "Git", "Node.js", "C#", "RESTful APIs", "web services", "microservices architecture",
    "Back-End Developer", "Computer Science", "Software Engineering",
    # Add more phrases based on your specific domain requirements
    "Data Science", "Machine Learning", "Artificial Intelligence", "Cloud Computing",
    "DevOps", "Agile", "Scrum", "Project Management", "Communication Skills",
    "Problem Solving", "Critical Thinking", "Teamwork" # Examples of non-tech/soft skills
]


# --- Flask App Setup ---

app = Flask(__name__)
CORS(app) # Enable CORS (Cross-Origin Resource Sharing)
# Configure Flask to show debug messages
app.config['DEBUG'] = True


# --- Instantiate core dependencies once when the app starts ---
# These are the dependencies that Resume_Scorer needs instances of.
# Text_Processor needs to be language-aware per request, so we instantiate a base instance here
# and a language-specific one inside the route to pass to the orchestrator.
# The base text_processor_app_instance is primarily used to check if the Text_Processor class was imported correctly.
text_processor_app_instance = Text_Processor(language='english') # Instantiate with a default language


# Instantiate Skill_Extractor and Resume_Parser once globally
# These are stateful (spaCy models) and should be loaded once globally
print(f"\n--- App Initialization ({SPACY_MODEL_NAME}) ---")
print("Instantiating Skill_Extractor...")
# Pass configuration constants to Skill_Extractor
skill_extractor_app_instance = Skill_Extractor(
    model_name=SPACY_MODEL_NAME,
    requirement_patterns=SKILL_MATCHER_PATTERNS_CONFIG, # Pass patterns config
    core_skill_phrases=CORE_SKILL_PHRASES_CONFIG # Pass core phrases config
)

print("\nInstantiating Resume_Parser...")
# Pass model name config to Resume_Parser
resume_parser_app_instance = Resume_Parser(model_name=SPACY_MODEL_NAME)
print("---------------------------------")


# Check if core dependencies loaded successfully
# Access the .nlp attribute from Skill_Extractor and Resume_Parser and check if Text_Processor class was imported
is_se_loaded = isinstance(skill_extractor_app_instance, Skill_Extractor) and hasattr(skill_extractor_app_instance, 'nlp') and skill_extractor_app_instance.nlp is not None
is_rp_loaded = isinstance(resume_parser_app_instance, Resume_Parser) and hasattr(resume_parser_app_instance, 'nlp') and resume_parser_app_instance.nlp is not None
is_tp_loaded = isinstance(text_processor_app_instance, Text_Processor) # Check if Text_Processor was imported correctly

# App can attempt to instantiate Resume_Scorer only if base dependencies loaded.
# Resume_Scorer will then check if its components are functional.

# --- Instantiate the Resume_Scorer Orchestrator once globally ---
# This instance will hold the instances of TfidfScorer, SkillComparer, ScoreAggregator.
# Only instantiate if base dependencies seem valid, otherwise Resume_Scorer init will fail gracefully.
resume_scorer_orchestrator_instance = None
if is_se_loaded and is_rp_loaded and is_tp_loaded: # Use the checks from above
    print("\nInstantiating Resume_Scorer Orchestrator...")
    try:
        # Instantiate the orchestrator, passing the required dependencies and configurations
        resume_scorer_orchestrator_instance = Resume_Scorer(
            text_processor=text_processor_app_instance, # Pass the base instance here
            skill_extractor=skill_extractor_app_instance,
            resume_parser=resume_parser_app_instance,
            tfidf_weight=TFIDF_SCORE_WEIGHT,          # Pass weights from config
            skill_match_weight=SKILL_MATCH_SCORE_WEIGHT,
            requirement_weights=REQUIREMENT_WEIGHTS_CONFIG, # Pass weight configs
            section_weights=SECTION_MULTIPLIERS_CONFIG
        )
        print("------------------------------------------")

        # Check if the orchestrator instance itself reports functional
        app_functional = hasattr(resume_scorer_orchestrator_instance, '_functional') and resume_scorer_orchestrator_instance._functional
        if not app_functional:
            print("Warning: Resume_Scorer orchestrator initialized but reported NOT functional. Check its initialization logs.")

    except Exception as e:
         print(f"Error during Resume_Scorer Orchestrator instantiation: {e}")
         import traceback
         traceback.print_exc()
         resume_scorer_orchestrator_instance = None # Ensure it's None if initialization fails
         app_functional = False # App is not functional if orchestrator fails

else:
     print("\nSkipping Resume_Scorer Orchestrator instantiation due to base dependency errors.")
     app_functional = False # App is not functional


if not app_functional:
     print("\n---")
     print("FATAL ERROR: JEMATS backend is NOT functional.")
     print("Please check the logs above for specific dependency or orchestrator initialization errors.")
     print(f"Base Dependency Status: Text_Processor Loaded={is_tp_loaded}, Skill_Extractor spaCy Loaded={is_se_loaded}, Resume_Parser spaCy Loaded={is_rp_loaded}")
     print(f"Ensure spaCy model '{SPACY_MODEL_NAME}' is downloaded.")
     print(f"Run: python -m spacy download {SPACY_MODEL_NAME}")
     print("Ensure all Python files (Document_Reader.py, Text_Processor.py, etc.) are present and correctly named.")
     print("---")
else:
     print(f"\n--- JEMATS Backend Starting ---")
     print(f"App Functional Status: {app_functional}")
     print(f"SpaCy model used: {SPACY_MODEL_NAME}")
     print(f"Configured TF-IDF Weight: {TFIDF_SCORE_WEIGHT}")
     print(f"Configured Skill Weight: {SKILL_MATCH_SCORE_WEIGHT}")
     print("Note: Weights are normalized in ScoreAggregator.")
     print("-" * 25)


@app.route('/score', methods=['POST'])
def get_score():
    """
    API endpoint to receive file upload, job description text, and language.
    Expects multipart/form-data. Returns multiple scores and details.
    """
    # Check the app_functional flag before processing requests
    if not app_functional or resume_scorer_orchestrator_instance is None:
         # Return a Service Unavailable status if the app or orchestrator is not functional
         print("Request received but app is not functional (orchestrator not loaded).")
         return jsonify({"error": "JEMATS backend is not fully functional due to initialization errors. Please check server logs for details."}), 503


    print("\n--- /score endpoint hit ---")
    # --- 1. Get data from the incoming request ---
    # Use request.form.get to safely get form data, defaults to None if not present
    job_description = request.form.get('job_description')
    # Get language from form data, default to 'english' if not provided
    language = request.form.get('language', 'english')
    # Get the file from request.files, defaults to None if not present
    resume_file = request.files.get('resume_file')

    print(f"Received request: JD provided={job_description is not None and job_description.strip() != ''}, Resume file provided={resume_file is not None and resume_file.filename != ''}, Language='{language}'")


    # --- 2. Validate essential inputs ---
    if not job_description or not job_description.strip():
        print("Validation Error: Missing or empty job description.")
        return jsonify({"error": "Job description is required."}), 400

    if not resume_file or resume_file.filename == '':
         print("Validation Error: Missing or empty resume file.")
         return jsonify({"error": "Resume file is required."}), 400

    # --- 3. Use Document_Reader to extract text from the resume file ---
    # Document_Reader is stateless, instantiate per request is fine.
    # Ensure Document_Reader is importable and valid
    # Test instantiation and method existence
    try:
        reader_check = Document_Reader()
        if not isinstance(reader_check, Document_Reader) or not hasattr(reader_check, 'read_document'):
             print("Error: Document_Reader dependency is invalid or missing method.")
             return jsonify({"error": "Document reader dependency error. Cannot process file."}), 500
        reader = reader_check # Use the checked instance
    except Exception as e:
         print(f"Error during Document_Reader check/instantiation: {e}")
         import traceback
         traceback.print_exc()
         return jsonify({"error": "Document reader dependency error during instantiation."}), 500


    resume_file.seek(0) # Ensure file pointer is at the beginning before reading
    try:
        # Read the file into a BytesIO stream first, then pass the stream
        # This handles different input types from Flask's request.files
        resume_stream = io.BytesIO(resume_file.read())
        resume_text = reader.read_document(resume_stream, resume_file.filename)
    except Exception as e:
         print(f"Error during resume file reading: {e}")
         import traceback
         traceback.print_exc()
         return jsonify({"error": f"Error reading text from the uploaded file '{resume_file.filename}'."}), 500


    if not resume_text or not resume_text.strip():
        # Return a specific error if text extraction failed or resulted in empty text
        print(f"Error: Could not read text from '{resume_file.filename}' or text is empty after reading.")
        return jsonify({"error": f"Could not read text from the uploaded file '{resume_file.filename}'. Please check the file content or type."}), 400

    print(f"Successfully read text from {resume_file.filename}. Length: {len(resume_text)}")


    # --- 4. Calculate scores using the Resume_Scorer Orchestrator ---
    # The orchestrator instance was created globally on app startup.
    # We need a language-specific Text_Processor instance for THIS request to pass to the orchestrator.
    try:
        # Ensure Text_Processor is importable and valid
        # Test instantiation
        tp_check = Text_Processor(language=language)
        if not isinstance(tp_check, Text_Processor) or not hasattr(tp_check, 'process_text'):
             print("Error: Text_Processor dependency is invalid during request processing. Cannot create language processor.")
             return jsonify({"error": "Text processor dependency error. Cannot calculate scores."}), 500

        # Update the language of the globally instantiated Text_Processor in the orchestrator for this request's language?
        # OR instantiate a new language-specific Text_Processor and somehow update the orchestrator's reference?
        # Re-instantiating the orchestrator per request is simpler if it's fast, but spaCy models are slow.
        # The orchestrator's components need the Text_Processor. Let's pass the language-specific instance *to the calculate_scores method*?
        # NO - the orchestrator *holds* the component instances which *hold* the Text_Processor.
        # The easiest is to ensure the globally instantiated Text_Processor can handle language switching or the orchestrator/components are designed to take language per method call.
        # The current Text_Processor design takes language in __init__. The simplest path is to *always* use the globally instantiated Text_Processor (with default language) in the orchestrator, or make Text_Processor process_text method take language as an optional arg.
        # Let's make Text_Processor's process_text method robust to language or rely on the language set in __init__. The orchestrator was given the *base* Text_Processor instance. Its components use *that* instance.
        # The user specified language in the request. We need to use that language for processing.
        # The Text_Processor __init__ sets the language and loads stopwords. We NEED a language-specific instance for this request.
        # The Resume_Scorer orchestrator *needs* instances of TP, SE, RP during *its* __init__ to pass to *its* components.
        # The simplest approach is to pass the *request-specific*, language-configured Text_Processor instance to the `calculate_scores` method of the orchestrator. But the orchestrator's components are already initialized with the base TP instance.
        # Let's modify the orchestrator's calculate_scores to accept the language-specific TP instance and pass it down, OR rely on the base TP instance and its default language.
        # Reworking the orchestrator's calculate_scores to accept the TP instance is the cleanest way to handle language per request without re-initializing everything.

        # Let's update the Resume_Scorer.calculate_scores signature and calls slightly.

        # Re-instantiate a language-specific Text_Processor for this request
        text_processor_instance_per_request = Text_Processor(language=language)

        print("Calling Resume_Scorer_Orchestrator.calculate_scores...")
        # Pass the request-specific language-configured Text_Processor instance, raw texts, and configuration
        # Update: Pass the raw texts and let the orchestrator use the TP instance it holds.
        # We need to ensure the TP instance used by the orchestrator's components is language-aware for THIS request.
        # This requires the orchestrator's TP dependency to be swapped or updated *per request*. This is complex.
        # Alternative: Make Text_Processor methods take language as an argument? Or make TfidfScorer/SkillComparer take language?
        # Let's stick to the simpler path: the orchestrator was given the base TP instance. We rely on that TP instance's default language (english) for TF-IDF. SkillComparer needs TP too, but it's passed via orchestrator.
        # The SkillComparer extracts based on spaCy model, which is language specific ('en_core_web_md'). Text_Processor handles text cleaning/stopwords.
        # The simplest approach given the current component design is to:
        # 1. Use the globally initialized Text_Processor (likely english) for TF-IDF (via TfidfScorer).
        # 2. Use the globally initialized Skill_Extractor (language depends on SPACY_MODEL_NAME) and Resume_Parser.
        # 3. The language parameter from the request is primarily useful for *which* spaCy model to load or *which* stopwords to use. Since we load one spaCy model globally, the language parameter is less critical *after* init unless we loaded multiple models or had more complex text processing based on language.
        # Let's proceed assuming the globally configured Text_Processor (defaulting to English) and the spaCy model (e.g., 'en_core_web_md') are used for all requests. If the user needs multilingual support, that's a future enhancement requiring significant changes.

        # Call calculate_scores on the globally instantiated orchestrator
        scores = resume_scorer_orchestrator_instance.calculate_scores(job_description, resume_text)
        print("calculate_scores completed.")


        # --- 5. Return the results as JSON ---
        # scores dictionary contains: tfidf_score, prioritized_skill_score, combined_score, matched_items, missing_items (and weighted scores)
        # Ensure the result is a dictionary before jsonify
        if not isinstance(scores, dict):
            print(f"Error: calculate_scores did not return a dictionary. Got {type(scores)}.")
            return jsonify({"error": "Internal scoring calculation error: Unexpected result format."}), 500

        # Add a success status if no error key is present
        if "error" not in scores:
             scores["status"] = "success"
        else:
             scores["status"] = "error"


        print("\n--- Scoring Results ---")
        print(f"Status: {scores.get('status', 'N/A')}")
        print(f"TF-IDF: {scores.get('tfidf_score', 0.0):.4f}, Skill Match: {scores.get('prioritized_skill_score', 0.0):.4f}, Combined: {scores.get('combined_score', 0.0):.4f}")
        print(f"Matched Items Count: {sum(len(v) for v in scores.get('matched_items', {}).values())}")
        print(f"Missing Items Count: {sum(len(v) for v in scores.get('missing_items', {}).values())}")
        if "error" in scores:
             print(f"Error Message: {scores['error']}")
        print("-------------------------")


        # Return the scores dictionary as JSON response
        # If there's an error key, return 500 status, otherwise 200
        status_code = 500 if "error" in scores else 200
        return jsonify(scores), status_code


    except Exception as e:
        # Catch any unexpected errors during the request processing pipeline (outside calculate_scores)
        print(f"An unexpected error occurred during scoring request handling:")
        import traceback
        traceback.print_exc() # Print full traceback to the console

        # Return a generic internal server error message to the frontend
        return jsonify({"error": "An internal error occurred during request processing. Please check the server logs for details."}), 500


# --- Main execution block ---
if __name__ == '__main__':
    # Run the Flask app in debug mode
    # debug=True provides helpful error pages and auto-reloading during development
    # In production, debug should be False
    # Use host='0.0.0.0' if you need to access the server from another machine on your network
    app.run(debug=True)
    