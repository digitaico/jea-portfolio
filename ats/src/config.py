# ats/src/config.py

import os
import yaml
from . import file_utils # Import your new file_utils module

# --- Configuration Loading ---
# Use file_utils to get the absolute path to ats_config.yaml
CONFIG_FILE_PATH = file_utils.get_config_filepath('ats_config.yaml')

def load_config():
    """Loads configuration from the ats_config.yaml file."""
    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_FILE_PATH}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")

# Load the configuration once when the module is imported
app_config = load_config()

# --- Configuration Access Functions ---
# These functions provide a clean interface to access configuration values.

def get_spacy_model_name():
    """Returns the spaCy model name from the configuration."""
    return app_config.get('spacy_model', 'en_core_web_md')

def get_embedding_model_name():
    """Returns the embedding model name from the configuration."""
    return app_config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')

def get_section_weights():
    """Returns the section weights for resume parsing."""
    return app_config.get('section_weights', {})

def get_score_weights():
    """Returns the scoring weights for different categories."""
    return app_config.get('score_weights', {})

def get_nltk_data_paths():
    """Returns a dictionary of NLTK data types and their download paths."""
    return app_config.get('nltk_data', {})

def get_keyword_patterns():
    """Returns keyword patterns for skill extraction."""
    return app_config.get('keyword_patterns', [])

def get_max_tokens():
    """Returns the maximum number of tokens for processing."""
    return app_config.get('max_tokens', 512)

def get_max_pages():
    """Returns the maximum number of pages for document processing."""
    return app_config.get('max_pages', 5)

def get_chunk_size():
    """Returns the chunk size for text processing."""
    return app_config.get('chunk_size', 1000)

def get_chunk_overlap():
    """Returns the chunk overlap for text processing."""
    return app_config.get('chunk_overlap', 200)

def get_google_api_key_for_document_ai():
    """Returns the Google API Key for Document AI from the configuration."""
    return app_config.get('google_api_key_for_document_ai')

def get_document_ai_processor_id():
    """Returns the Document AI processor ID from the configuration."""
    return app_config.get('document_ai_processor_id')

def get_document_ai_project_id():
    """Returns the Document AI project ID from the configuration."""
    return app_config.get('document_ai_project_id')

def get_document_ai_location():
    """Returns the Document AI location (e.g., 'us') from the configuration."""
    return app_config.get('document_ai_location')

# Example of how to access:
# SPACY_MODEL = get_spacy_model_name()
# print(f"Loaded spaCy model: {SPACY_MODEL}")