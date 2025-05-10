# /mnt/disc2/local-code/jea-portfolio/ats/src/utils/config_loader.py

import yaml
import os
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

class ConfigLoader:
    _config = None
    _config_path = os.path.join(os.path.dirname(__file__), '../../config/nlp_patterns.yaml')

    @classmethod
    def _load_config(cls):
        if cls._config is None:
            logger.info(f"Attempting to load configuration from: {cls._config_path}")
            try:
                with open(cls._config_path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f)
                logger.info("Configuration loaded successfully.")
            except FileNotFoundError:
                logger.error(f"Configuration file not found at: {cls._config_path}")
                raise FileNotFoundError(f"Configuration file not found at: {cls._config_path}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML configuration file: {e}")
                raise ValueError(f"Error parsing YAML configuration file: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading config: {e}")
                raise

    @classmethod
    def get_spacy_model_name(cls, lang: str) -> str:
        cls._load_config()
        model_name = cls._config.get('languages', {}).get(lang, {}).get('spacy_model_name')
        if not model_name:
            raise ValueError(f"SpaCy model name not found for language '{lang}' in config.")
        return model_name

    @classmethod
    def get_resume_heading_patterns(cls, lang: str) -> list:
        cls._load_config()
        patterns = cls._config.get('languages', {}).get(lang, {}).get('resume_headings', []) # Corrected to match nlp_patterns.yaml structure
        if not patterns:
            logger.warning(f"Resume heading patterns not found for language '{lang}' in config.")
        return patterns
    
    @classmethod
    def get_section_weights(cls, lang: str) -> dict:
        """
        Retrieves the section weights for a given language from the configuration.
        """
        cls._load_config()
        # Corrected path: Section weights are under 'resume_parser_patterns' in config if present
        weights = cls._config.get('languages', {}).get(lang, {}).get('resume_parser_patterns', {}).get('section_weights', {})
        if not weights:
            logger.warning(f"Section weights not found for language '{lang}' in config. Defaulting to empty dictionary.")
        return weights

    @classmethod
    def get_requirement_weights(cls, lang: str) -> dict:
        """
        Retrieves the requirement weights for a given language from the configuration.
        """
        cls._load_config()
        # Assuming requirement weights are stored under 'requirement_weights' in the language section
        weights = cls._config.get('languages', {}).get(lang, {}).get('requirement_weights', {})
        if not weights:
            logger.warning(f"Requirement weights not found for language '{lang}' in config. Defaulting to empty dictionary.")
        return weights

    @classmethod
    def get_skill_patterns(cls, lang: str, domain: str, pattern_type: str) -> list:
        """
        Retrieves skill patterns for a given language, domain, and pattern type.
        Pattern types include 'core_skills', 'years_experience', etc.
        """
        cls._load_config()
        patterns = cls._config.get('languages', {}).get(lang, {}).get('skill_extraction_patterns', {}).get(domain, {}).get(pattern_type, [])
        if not patterns:
            logger.warning(f"Skill patterns of type '{pattern_type}' for language '{lang}' and domain '{domain}' not found in config. Defaulting to empty list.")
        return patterns