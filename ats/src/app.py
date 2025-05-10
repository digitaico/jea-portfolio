# Ya
# /mnt/disc2/local-code/jea-portfolio/ats/src/app.py

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS # You may need to install this: pip install Flask-Cors

# Relative imports for your modules - UPDATED TO SNAKE_CASE FILE NAMES
from .config import (
    get_spacy_model_name, get_embedding_model_name, get_section_weights,
    get_score_weights, get_nltk_data_paths
)
from .document_reader import DocumentReader # Changed: Document_Reader -> document_reader
from .resume_parser import ResumeParser     # Changed: Resume_Parser -> resume_parser
from .skill_extractor import SkillExtractor # Changed: Skill_Extractor -> skill_extractor
from .resume_scorer import ResumeScorer     # Changed: Resume_Scorer -> resume_scorer
from .score_aggregator import ScoreAggregator # Changed: ScoreAggregator -> score_aggregator
from .skill_comparer import SkillComparer   # Changed: SkillComparer -> skill_comparer
from .text_processor import TextProcessor   # Changed: Text_Processor -> text_processor
from .tfidf_scorer import TfidfScorer       # Changed: TfidfScorer -> tfidf_scorer

# Configure logging (before app instantiation for full coverage)
logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Global instance of orchestrator (will be set by create_app)
resume_scorer_orchestrator = None

# --- NLTK Data Download (Run once at startup) ---
def ensure_nltk_data():
    """Ensures NLTK data is downloaded if not already present."""
    nltk_data_paths = get_nltk_data_paths()
    for data_type, download_path in nltk_data_paths.items():
        try:
            # Use `find` to check if data is already downloaded
            import nltk
            nltk.data.find(download_path)
            logger.info(f"NLTK {data_type} data found locally.")
        except LookupError:
            logger.info(f"NLTK {data_type} data not found. Attempting download...")
            try:
                nltk.download(data_type, download_dir=os.path.expanduser('~/nltk_data')) # Download to user's home NLTK data dir
                logger.info(f"NLTK {data_type} data downloaded successfully to {os.path.expanduser('~/nltk_data')}.")
            except Exception as e:
                logger.error(f"Error downloading NLTK {data_type} data: {e}")
                raise # Re-raise to prevent app from running without necessary data
    logger.info("NLTK data download check/completion successful.")

# Call NLTK data download check during module import, before app factory.
# This ensures data is ready before any NLTK-dependent components initialize.
ensure_nltk_data()

# --- Orchestrator Class ---
class ResumeScorerOrchestrator: # Class name remains CamelCase
    def __init__(self, spacy_model_name, embedding_model_name, section_weights, score_weights):
        logger.info(f"--- App Initialization ({spacy_model_name}) ---")
        self.text_processor = TextProcessor(spacy_model_name)
        logger.info("Instantiating SkillExtractor...")
        self.skill_extractor = SkillExtractor(spacy_model_name)
        logger.info("Instantiating ResumeParser...")
        self.resume_parser = ResumeParser(
            skill_extractor=self.skill_extractor,
            text_processor=self.text_processor,
            section_weights=section_weights
        )
        logger.info("Instantiating DocumentReader...")
        self.document_reader = DocumentReader() # Assuming no params needed here for now
        logger.info("Instantiating TfidfScorer...")
        self.tfidf_scorer = TfidfScorer(embedding_model_name=embedding_model_name)
        logger.info("Instantiating SkillComparer...")
        self.skill_comparer = SkillComparer()
        logger.info("Instantiating ScoreAggregator...")
        self.score_aggregator = ScoreAggregator(score_weights=score_weights)
        logger.info("Instantiating ResumeScorer...")
        self.resume_scorer = ResumeScorer(
            resume_parser=self.resume_parser,
            tfidf_scorer=self.tfidf_scorer,
            skill_comparer=self.skill_comparer,
            score_aggregator=self.score_aggregator,
            skill_extractor=self.skill_extractor # Added skill_extractor for consistency
        )
        logger.info("All components initialized.")

    def score_resume(self, resume_path, job_description_path): # Function name remains snake_case
        logger.info("Received request to score resume.")
        try:
            resume_text = self.document_reader.read_document(resume_path)
            job_description_text = self.document_reader.read_document(job_description_path)

            if not resume_text or not job_description_text:
                raise ValueError("Could not read one or both documents.")

            score_details = self.resume_scorer.score_resume(resume_text, job_description_text)
            logger.info("Resume scoring complete.")
            return score_details
        except Exception as e:
            logger.exception("Error during resume scoring:")
            raise

# --- Flask App Factory ---
def create_app(): # Function name remains snake_case
    app = Flask(__name__)
    CORS(app) # Enable CORS for all origins by default

    # Load configuration values using the functions from config.py
    spacy_model_name = get_spacy_model_name()
    embedding_model_name = get_embedding_model_name()
    section_weights = get_section_weights()
    score_weights = get_score_weights()

    # Initialize the orchestrator
    orchestrator_instance = ResumeScorerOrchestrator(
        spacy_model_name, embedding_model_name, section_weights, score_weights
    )

    # Make the orchestrator accessible globally (if needed, though usually passed to routes)
    global resume_scorer_orchestrator
    resume_scorer_orchestrator = orchestrator_instance

    @app.route('/score', methods=['POST'])
    def score_resume_endpoint(): # Function name remains snake_case
        if 'resume' not in request.files or 'job_description' not in request.files:
            return jsonify({"error": "Both resume and job description files are required."}), 400

        resume_file = request.files['resume']
        job_description_file = request.files['job_description']

        # Save files temporarily or process directly from memory stream
        # For simplicity, saving to temp files for now
        resume_path = "/tmp/uploaded_resume.pdf" # Or a more robust temp file handling
        jd_path = "/tmp/uploaded_jd.pdf"

        resume_file.save(resume_path)
        job_description_file.save(jd_path)

        try:
            # Use the globally accessible orchestrator instance
            score_details = resume_scorer_orchestrator.score_resume(resume_path, jd_path)
            return jsonify(score_details), 200
        except Exception as e:
            logger.exception("API Endpoint Error:")
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up temporary files
            if os.path.exists(resume_path):
                os.remove(resume_path)
            if os.path.exists(jd_path):
                os.remove(jd_path)

    return app, orchestrator_instance # Return both app and orchestrator