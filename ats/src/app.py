# Ya
# /mnt/disc2/local-code/jea-portfolio/ats/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS 
import spacy
import os
import logging
import sys
import nltk

# Ensure project root is in sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.resume_parser import ResumeParser
from src.skill_extractor import SkillExtractor
from src.skill_comparer import SkillComparer
from src.score_aggregator import ScoreAggregator
from src.utils.file_converter import convert_pdf_to_text, convert_docx_to_text
from src.utils.config_loader import ConfigLoader

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

# Disable spaCy's default logger if it's too verbose
logging.getLogger('spacy').setLevel(logging.WARNING)

# Global instances (will be initialized dynamically based on request)
nlp_models = {}
resume_parsers = {}
skill_extractors = {}


# Function to ensure NLTK data is downloaded
def download_nltk_data():
    logger.info("Attempting to perform NLTK data downloads (punkt, stopwords)...")
    try:
        nltk.data.find('tokenizers/punkt')
        logger.info("NLTK punkt tokenizer data found locally.")
    except nltk.downloader.DownloadError:
        logger.warning("NLTK punkt tokenizer data not found. Attempting to download...")
        nltk.download('punkt', quiet=True)
        logger.info("NLTK punkt tokenizer data downloaded successfully.")
    
    try:
        nltk.data.find('corpora/stopwords')
        logger.info("NLTK stopwords data found locally.")
    except nltk.downloader.DownloadError:
        logger.warning("NLTK stopwords data not found. Attempting to download...")
        nltk.download('stopwords', quiet=True)
        logger.info("NLTK stopwords data downloaded successfully.")
    
    logger.info("NLTK data download check/completion successful.")


# Function to get or create NLP components for a given language
def get_or_create_nlp_components(lang: str):
    global nlp_models, resume_parsers, skill_extractors

    # Load config for the specified language
    try:
        spacy_model_name = ConfigLoader.get_spacy_model_name(lang)
        # Assuming get_resume_heading_patterns and get_skill_patterns methods are available
        resume_heading_patterns = ConfigLoader.get_resume_heading_patterns(lang)
        skill_patterns = {
            'REQUIRED_SKILL_PHRASE': ConfigLoader.get_skill_patterns(lang, 'common', 'required_skill_phrase'),
            'YEARS_EXPERIENCE': ConfigLoader.get_skill_patterns(lang, 'common', 'years_experience'),
            'KNOWLEDGE_OF': ConfigLoader.get_skill_patterns(lang, 'common', 'knowledge_of'),
            'QUALIFICATION_DEGREE': ConfigLoader.get_skill_patterns(lang, 'common', 'qualification_degree'),
            # CORRECTED: Add core_skills to skill_patterns dictionary
            'CORE_SKILL': ConfigLoader.get_skill_patterns(lang, 'common', 'core_skills') 
        }

        requirement_weights = ConfigLoader.get_requirement_weights(lang) # Get all requirement weights
        section_weights = ConfigLoader.get_section_weights(lang) # Get section weights

    except Exception as e:
        logger.error(f"Failed to load configuration for language '{lang}': {e}")
        raise ValueError(f"Configuration error for language '{lang}': {e}")


    # Load spaCy model
    if lang not in nlp_models:
        logger.info(f"\n--- App Initialization ({spacy_model_name}) ---")
        logger.info(f"Attempting to load spaCy model: {spacy_model_name}")
        try:
            nlp = spacy.load(spacy_model_name)
            nlp_models[lang] = nlp
            logger.info(f"SpaCy model '{spacy_model_name}' loaded successfully.")
        except OSError:
            logger.error(f"SpaCy model '{spacy_model_name}' not found. Attempting to download and install...")
            try:
                # Ensure pip is installed/available in the environment
                import subprocess
                subprocess.check_call([sys.executable, "-m", "spacy", "download", spacy_model_name])
                nlp = spacy.load(spacy_model_name)
                nlp_models[lang] = nlp
                logger.info(f"SpaCy model '{spacy_model_name}' downloaded and loaded successfully.")
            except Exception as e:
                logger.critical(f"Failed to download and load spaCy model '{spacy_model_name}': {e}")
                raise RuntimeError(f"SpaCy model '{spacy_model_name}' not available. Please install it using 'python -m spacy download {spacy_model_name}'")
        logger.info("---------------------------------------------")


    nlp = nlp_models[lang]

    # Initialize SkillExtractor
    if lang not in skill_extractors:
        logger.info("Instantiating Skill_Extractor...")
        # Pass the loaded nlp model and requirement patterns to SkillExtractor
        # CORRECTED: Pass the consolidated skill_patterns dictionary.
        skill_extractors[lang] = SkillExtractor(
            nlp=nlp,
            requirement_patterns=skill_patterns
        )
        logger.info("Skill_Extractor instantiated.")

    # Initialize ResumeParser
    if lang not in resume_parsers:
        logger.info("Instantiating Resume_Parser...")
        # Create a Matcher for resume headings for the ResumeParser
        heading_matcher = spacy.matcher.Matcher(nlp.vocab)
        for pattern_list in resume_heading_patterns:
            # Assuming each pattern_list in resume_heading_patterns is for a single label like 'SECTION_HEADING'
            # You might need to adjust this if your config supports multiple labels for headings
            # For simplicity, let's assume a generic 'SECTION_HEADING' label or pass patterns directly
            # For this example, let's assume ResumeParser handles its own matcher setup
            # based on injected patterns. So we don't pass the matcher here directly,
            # but rather the patterns for the ResumeParser to set up its internal matcher.
            # Correct approach: ResumeParser should receive the pre-configured Matcher.
            # Let's move the matcher creation and pattern addition into this function.
            heading_matcher.add("RESUME_SECTION_HEADING", resume_heading_patterns) # Add all patterns under one label

        resume_parsers[lang] = ResumeParser(
            nlp=nlp,
            matcher=heading_matcher, # Pass the pre-configured heading matcher
            section_weights=section_weights # Pass section weights
        )
        logger.info("Resume_Parser instantiated.")
    
    logger.info("All NLP components initialized or retrieved.")
    return skill_extractors[lang], resume_parsers[lang], requirement_weights, section_weights


# Initial NLTK data download when the app starts
with app.app_context():
    download_nltk_data()


@app.route('/compare_cv', methods=['POST'])
def compare_cv():
    logger.info("Received /compare_cv request.")
    try:
        # 1. Input Validation and File Handling
        if 'job_description' not in request.form:
            raise ValueError("Job description is missing.")
        if 'resume' not in request.files:
            raise ValueError("Resume file is missing.")
        
        lang = request.form.get('lang', 'en') # Default to English

        jd_text = request.form['job_description']
        resume_file = request.files['resume']
        filename = resume_file.filename

        logger.info(f"Processing request for language: {lang}")
        logger.info(f"Job Description length: {len(jd_text)} characters.")
        logger.info(f"Resume filename: {filename}")

        # Convert resume file to text
        resume_text = ""
        if filename.endswith('.pdf'):
            logger.info("Converting PDF resume to text...")
            # Read the file content as bytes before passing to the converter
            resume_text = convert_pdf_to_text(resume_file.read())
        elif filename.endswith('.docx'):
            logger.info("Converting DOCX resume to text...")
            # Read the file content as bytes before passing to the converter
            resume_text = convert_docx_to_text(resume_file.read())
        elif filename.endswith('.txt'):
            logger.info("Reading text resume...")
            resume_text = resume_file.read().decode('utf-8')
        else:
            raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")

        if not jd_text or not resume_text:
            raise ValueError("Could not extract text from job description or resume.")

        logger.info(f"Extracted resume text length: {len(resume_text)} characters.")

        # 2. Get or Create NLP Components for the specified language
        logger.info(f"Getting or creating NLP components for language: {lang}...")
        skill_extractor, resume_parser, requirement_weights, section_weights = get_or_create_nlp_components(lang)
        logger.info("NLP components ready.")


        # 3. Parse Resume Sections (using the parsed text)
        logger.info("Parsing resume sections...")
        parsed_resume = resume_parser.parse_sections(resume_text)
        logger.info(f"Parsed {len(parsed_resume)} sections from resume.")

        # 4. Perform Skill Comparison
        logger.info("Performing skill comparison...")
        skill_comparer = SkillComparer(
            skill_extractor=skill_extractor,
            resume_parser=resume_parser, # Pass resume_parser even if not directly used by compare_skills, as its a dependency.
            requirement_weights=requirement_weights,
            section_weights=section_weights
        )
        
        # The compare_skills method is expected to return a tuple of (raw_score, achieved_score, total_possible_score, matched_items_dict, missing_items_dict)
        # UPDATED: Unpack the 5-element tuple correctly
        skill_match_raw_score, achieved_weighted_score, total_possible_weighted_score, matched_items, missing_items = skill_comparer.compare_skills(jd_text, resume_text)
        
        logger.info(f"Received skill comparison results: Achieved={achieved_weighted_score:.4f}, Possible={total_possible_weighted_score:.4f}, Matched={len(matched_items)}, Missing={len(missing_items)}")


        # 5. Aggregate Scores (if you have a ScoreAggregator)
        logger.info("Calling ScoreAggregator.aggregate_and_format_scores...")
        score_aggregator = ScoreAggregator(
            tfidf_weight=0.3, # Example weight, could be loaded from config
            skill_match_weight=0.7 # Example weight, could be loaded from config
        )
        
        # Pass the correct achieved and total possible scores
        # CORRECTED: Added 'missing_items' as a positional argument
        final_score, tfidf_score, skill_match_score = score_aggregator.aggregate_and_format_scores(
            achieved_weighted_score,
            total_possible_weighted_score,
            jd_text, # Original JD text for TF-IDF
            resume_text, # Original resume text for TF-IDF
            missing_items # Pass the missing_items list here
        )
        logger.info("Score aggregation and formatting complete...")

        response_data = {
            "match_percentage": final_score,
            "detailed_comparison": {
                "matched_skills": matched_items,
                "missing_skills": missing_items,
                "achieved_score": achieved_weighted_score, # Corrected variable name
                "total_possible_score": total_possible_weighted_score # Corrected variable name
            },
            "parsed_resume_sections": parsed_resume
        }
        logger.info("Request processed successfully. Returning response.")
        return jsonify(response_data), 200

    except ValueError as ve:
        logger.error(f"Input validation error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        logger.error(f"File conversion error: {fnfe}")
        return jsonify({"error": f"File processing error: {fnfe}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred. Please check logs for details."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)