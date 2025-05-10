# /mnt/disc2/local-code/jea-portfolio/ats/src/skill_extractor.py

import spacy
from spacy.matcher import Matcher
import logging

logger = logging.getLogger(__name__)

class SkillExtractor:
    def __init__(self, nlp, requirement_patterns: dict):
        """
        Initializes the SkillExtractor.
        Args:
            nlp: The pre-loaded spaCy Language model instance.
            requirement_patterns (dict): A dictionary where keys are skill labels (e.g., 'REQUIRED_SKILL_PHRASE', 'CORE_SKILL')
                                        and values are lists of spaCy token patterns.
        """
        logger.info("\n--- SkillExtractor Initialization ---")
        self.nlp = nlp
        self.matcher = Matcher(nlp.vocab)
        self.requirement_patterns = requirement_patterns
        self._add_patterns_to_matcher()
        logger.info("SkillExtractor initialized and patterns added to matcher.")
        logger.info("------------------------------------")

    def _add_patterns_to_matcher(self):
        """Adds all configured requirement patterns to the spaCy Matcher."""
        logger.info(f"SkillExtractor: Attempting to add requirement pattern groups to Matcher (input groups: {len(self.requirement_patterns)}).")
        if self.matcher is None:
            logger.error("SkillExtractor: Matcher is not initialized. Cannot add patterns.")
            return

        for label, patterns_list in self.requirement_patterns.items():
            if patterns_list: # Only add if patterns are not empty
                # Ensure patterns are in the correct format (list of lists of dicts)
                # If it's a simple list of patterns, wrap it in a list of lists.
                # Assuming patterns_list is already in the correct format: [[{...}], [{...}]]
                try:
                    self.matcher.add(label, patterns_list)
                    logger.info(f"SkillExtractor: Grouped {len(patterns_list)} pattern list(s) under label '{label}'.")
                except ValueError as e:
                    logger.error(f"SkillExtractor: Error adding patterns for label '{label}': {e}. Patterns: {patterns_list}")
            else:
                logger.warning(f"SkillExtractor: No patterns found for label '{label}'. Skipping.")
        logger.info("SkillExtractor: Finished adding patterns to matcher.")


    def extract_skills(self, text: str, is_jd: bool = False) -> list:
        """
        Extracts skills from the given text using spaCy and configured patterns.
        Args:
            text (str): The input text (either Job Description or Resume).
            is_jd (bool): True if the text is a Job Description, False if a Resume.
                          This can be used for conditional logic (e.g., different pattern sets or logging).
        Returns:
            list: A list of dictionaries, each representing an extracted skill with its label and text.
        """
        if not text:
            logger.warning("SkillExtractor: Input text is empty. Returning empty list.")
            return []

        logger.info(f"SkillExtractor: Extracting skills from {'JD' if is_jd else 'Resume'} text (length: {len(text)})...")
        doc = self.nlp(text)
        extracted_items = []

        matches = self.matcher(doc)

        for match_id, start, end in matches:
            label_id = self.nlp.vocab.strings[match_id]  # Get string representation of the label
            span = doc[start:end]  # The matched span of text
            
            # Basic cleaning for consistency
            cleaned_text = span.text.strip().lower()

            extracted_items.append({
                'label': label_id,
                'text': span.text, # Original text
                'cleaned_text': cleaned_text # Cleaned version for easier comparison later
            })
            logger.debug(f"SkillExtractor DEBUG: Extracted '{span.text}' (Cleaned: '{cleaned_text}') with label '{label_id}' from {'JD' if is_jd else 'Resume'}.")
        
        logger.info(f"SkillExtractor: Finished extracting {len(extracted_items)} skills from {'JD' if is_jd else 'Resume'}.")
        return extracted_items