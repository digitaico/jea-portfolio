# Ya
# src/Skill_Extractor.py (no significant changes needed if __init__ already accepted args)

import spacy
from spacy.matcher import Matcher, PhraseMatcher
from collections import defaultdict
import sys
import os
import spacy.cli

class SkillExtractor:
    """
    Extracts structured information (requirements, skills, experience years, etc.)
    from text using spaCy Matcher and PhraseMatcher.
    Can process entire documents or specific sections if provided.
    Includes debug prints for tracing extraction process.
    """
    def __init__(self, model_name: str = 'en_core_web_md',
                 requirement_patterns: list | None = None, # These will come from config now
                 core_skill_phrases: list | None = None): # These will come from config now
        """
        Initializes the Skill_Extractor by loading the spaCy model and setting up Matchers.

        Args:
            model_name (str): The name of the spaCy model to load.
            requirement_patterns (list, optional): A list of tuples (label, patterns)
                                                   for the Matcher to find structured requirements.
            core_skill_phrases (list, optional): A list of strings representing core skills
                                                 for the PhraseMatcher.
        """
        print(f"\n--- Skill_Extractor Initialization ({model_name}) ---")
        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None
        self._functional = False

        try:
            print(f"Attempting to load spaCy model: {model_name}")
             # Ensure the spaCy model is downloaded before loading
            try:
                spacy.load(model_name)
            except OSError:
                print(f"SpaCy model '{model_name}' not found. Downloading...")
                try:
                    spacy.cli.download(model_name, "--process")
                    print(f"SpaCy model '{model_name}' downloaded successfully.")
                except Exception as download_error:
                    print(f"Error downloading spaCy model '{model_name}': {download_error}")
                    print("Please try downloading it manually from your terminal using the correct environment:")
                    print(f"python -m spacy download {model_name}")


            self.nlp = spacy.load(model_name)
            print(f"SpaCy model '{model_name}' loaded successfully.")

            self.matcher = Matcher(self.nlp.vocab)
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab)

            # Add patterns and phrases if provided (these now come from app.py -> config)
            if requirement_patterns:
                print(f"Attempting to add requirement pattern groups to Matcher (input groups: {len(requirement_patterns)}).")
                self._add_patterns_to_matcher(requirement_patterns)
            else:
                 print("No requirement patterns provided during initialization.")

            if core_skill_phrases:
                print(f"Core skill phrases provided ({len(core_skill_phrases)}). Attempting to initialize PhraseMatcher.")
                self._add_phrases_to_matcher(core_skill_phrases)
            else:
                 print("No core skill phrases provided during initialization.")


            matcher_rules_count = len(self.matcher) if self.matcher else 0
            phrase_matcher_rules_count = len(self.phrase_matcher) if self.phrase_matcher else 0

            if matcher_rules_count > 0 or phrase_matcher_rules_count > 0:
                 self._functional = True
            else:
                 self._functional = False
                 print("Warning: Skill_Extractor initialized, but no Matcher or PhraseMatcher rules were added. Functionality will be limited.")


        except OSError:
            print(f"Error: SpaCy model '{model_name}' not found after download attempt.")
            self.nlp = None
            self.matcher = None
            self.phrase_matcher = None
            self._functional = False
        except Exception as e:
            print(f"An error occurred during Skill_Extractor initialization: {e}")
            import traceback
            traceback.print_exc()
            self.nlp = None
            self.matcher = None
            self.phrase_matcher = None
            self._functional = False


        print(f"\n--- Skill_Extractor Initialization Final Status ({model_name}) ---")
        print(f"NLP Model Loaded: {self.nlp is not None}")
        print(f"Matcher Initialized: {self.matcher is not None}")
        print(f"PhraseMatcher Initialized: {self.phrase_matcher is not None}")
        print(f"Skill_Extractor Functional: {self._functional}")
        print("---------------------------------------------")


    # _add_patterns_to_matcher and _add_phrases_to_matcher methods remain the same
    def _add_patterns_to_matcher(self, requirement_patterns: list):
        """Adds patterns to the spaCy Matcher."""
        if self.matcher is None or not isinstance(requirement_patterns, list):
             print("Entering _add_patterns_to_matcher. Matcher is None or requirement_patterns is not a list. Skipping pattern addition.")
             print(f"self.matcher upon entry: {self.matcher}, requirement_patterns is: {isinstance(requirement_patterns, list)}")
             return

        print(f"Entering _add_patterns_to_matcher. self.matcher upon entry: {self.matcher}")
        print("Matcher is not None and requirement_patterns is a list. Proceeding to add patterns.")


        patterns_by_label = defaultdict(list)
        for label, pattern_list in requirement_patterns:
            if isinstance(pattern_list, list):
                print(f" Grouped {len(pattern_list)} pattern list(s) under label '{label}'.")
                patterns_by_label[label].extend(pattern_list)
            else:
                 print(f"Warning: Pattern list for label '{label}' is not a list. Skipping.")


        for label, patterns in patterns_by_label.items():
             if patterns:
                  print(f" Attempting to add {len(patterns)} pattern list(s) for unique label '{label}'.")
                  try:
                       self.matcher.add(label, patterns)
                       print(f"   DEBUG: Successfully added {len(patterns)} pattern list(s) for label '{label}'. Matcher now has {len(self.matcher)} rules.")
                       print(f" - Added patterns for label '{label}'. Matcher now has {len(self.matcher)} rules.")
                  except Exception as e:
                       print(f"Error adding patterns for label '{label}': {e}")
                       import traceback
                       traceback.print_exc()
             else:
                 print(f"No patterns found for label '{label}'. Skipping addition.")

        print(f"Total pattern list groups processed for adding to Matcher at end of method: {len(patterns_by_label)}")
        print(f"Final total rules in Matcher: {len(self.matcher)}")


    def _add_phrases_to_matcher(self, core_skill_phrases: list):
        """Adds phrases to the spaCy PhraseMatcher."""
        if self.phrase_matcher is None or self.nlp is None or not isinstance(core_skill_phrases, list):
             print("Entering _add_phrases_to_matcher. PhraseMatcher or NLP not initialized or core_skill_phrases is not a list. Skipping phrase addition.")
             print(f"self.phrase_matcher upon entry: {self.phrase_matcher is not None}, self.nlp is: {self.nlp is not None}, self.core_skill_phrases is: {isinstance(core_skill_phrases, list)}")
             return

        print(f"Entering _add_phrases_to_matcher. self.phrase_matcher upon entry: {self.phrase_matcher is not None}, self.nlp is: {self.nlp is not None}, self.core_skill_phrases is: {isinstance(core_skill_phrases, list)}")
        print("PhraseMatcher, NLP, and core_skill_phrases are available. Proceeding to add phrases.")


        phrase_patterns = [self.nlp(phrase) for phrase in core_skill_phrases if isinstance(phrase, str)]
        print(f" Created {len(phrase_patterns)} Doc patterns from phrases.")


        if phrase_patterns:
             print(" Condition 'if patterns:' is True for PhraseMatcher. Attempting to add phrases...")
             try:
                  self.phrase_matcher.add("CORE_SKILL", phrase_patterns)
                  print(f"   DEBUG: Adding {len(phrase_patterns)} phrase patterns to PhraseMatcher.")
                  print(f"   DEBUG: Successfully added phrase patterns. PhraseMatcher now has {len(self.phrase_matcher)} rules.")
                  print(f" - Added {len(phrase_patterns)} phrase patterns to PhraseMatcher under label 'CORE_SKILL'. PhraseMatcher now has {len(self.phrase_matcher)} rules.")
             except Exception as e:
                  print(f"Error adding phrases to PhraseMatcher: {e}")
                  import traceback
                  traceback.print_exc()
        else:
            print("No valid phrase patterns found to add to PhraseMatcher.")

        print(f"PhraseMatcher has {len(self.phrase_matcher)} rules after calling _add_phrases_to_matcher.")


    # extract_requirements_and_skills method remains the same
    def extract_requirements_and_skills(self, text: str, sections: list | None = None) -> dict:
        """
        Extracts requirements (from Matcher) and skills (from PhraseMatcher) from text.

        Args:
            text (str): The raw text to extract from.
            sections (list, optional): A list of dictionaries [{'heading': '...', 'content': '...'}].
                                      If provided, extraction is done section by section.
                                      If None, extraction is done on the entire text (e.g., for JD).

        Returns:
            dict: A dictionary where keys are the labels (e.g., 'REQUIRED_SKILL_PHRASE',
                  'CORE_SKILL') and values are lists of extracted items.
                  Each item in the list is a dict with 'text' and 'section' (or 'sections' if from resume).
                  Returns an empty dict if Skill_Extractor is not functional or extraction fails.
        """
        if not self._functional or self.nlp is None:
             print("Error: Skill_Extractor is not functional or NLP model not loaded. Cannot extract.")
             return {}

        if not isinstance(text, str):
             print(f"Error: Input text for Skill_Extractor is not a string, got {type(text)}. Cannot extract.")
             return {}


        extracted_items = defaultdict(list)
        is_resume = sections is not None

        print(f"\nExtracting from text (length {len(text)}).")


        if is_resume and isinstance(sections, list) and sections:
            print("Processing a Resume with sections.")
            print(f"Sections data received (count: {len(sections)}).")


            for section_data in sections:
                if isinstance(section_data, dict) and 'heading' in section_data and 'content' in section_data:
                    section_heading = section_data.get('heading', 'Unidentified').strip()
                    section_content = section_data.get('content', '')

                    if not section_content:
                        continue

                    try:
                        section_doc = self.nlp(section_content)

                        if self.matcher and len(self.matcher) > 0:
                             matcher_matches = self.matcher(section_doc)
                             for match_id, start, end in matcher_matches:
                                  span = section_doc[start:end]
                                  label = self.nlp.vocab.strings[match_id]
                                  extracted_items[label].append({'text': span.text, 'section': section_heading})


                        if self.phrase_matcher and len(self.phrase_matcher) > 0:
                             phrase_matches = self.phrase_matcher(section_doc)
                             for match_id, start, end in phrase_matches:
                                  span = section_doc[start:end]
                                  label = self.nlp.vocab.strings[match_id]
                                  extracted_items[label].append({'text': span.text, 'section': section_heading})

                    except Exception as e:
                         print(f"Error processing section '{section_heading}': {e}")
                         import traceback
                         traceback.print_exc()


                else:
                     print(f"Warning: Skipping invalid section data format: {section_data}")


        else:
            print("Processing a Job Description (no sections).")
            try:
                doc = self.nlp(text)
                print(f"Doc token count: {len(doc)}")
                print(f"First 20 tokens of doc: {[token.text for token in doc[:min(20, len(doc))]]}")

                if self.matcher and len(self.matcher) > 0:
                    print(f"Running Matcher with {len(self.matcher)} rules on Doc.")
                    matcher_matches = self.matcher(doc)
                    print(f"Result of self.matcher(doc) found {len(matcher_matches)} matches.")
                    if matcher_matches:
                        print(f"First 5 Matcher matches: {matcher_matches[:min(5, len(matcher_matches))]}")

                    if not matcher_matches:
                         print("No Matcher matches found.")

                    for match_id, start, end in matcher_matches:
                        span = doc[start:end]
                        label = self.nlp.vocab.strings[match_id]
                        extracted_items[label].append(span.text)

                if self.phrase_matcher and len(self.phrase_matcher) > 0:
                    print(f"Running PhraseMatcher with {len(self.phrase_matcher)} rules on Doc.")
                    phrase_matches = self.phrase_matcher(doc)
                    print(f"Result of self.phrase_matcher(doc) found {len(phrase_matches)} matches.")
                    if phrase_matches:
                        print(f"First 5 PhraseMatcher matches: {phrase_matches[:min(5, len(phrase_matches))]}")

                    if not phrase_matches:
                         print("No PhraseMatcher matches found.")

                    for match_id, start, end in phrase_matches:
                         span = doc[start:end]
                         label = self.nlp.vocab.strings[match_id]
                         extracted_items[label].append(span.text)


            except Exception as e:
                 print(f"Error processing entire text: {e}")
                 import traceback
                 traceback.print_exc()
                 return {}


        print("\nExtracted items BEFORE cleaning/deduplication:", extracted_items)
        cleaned_extracted_items = defaultdict(list)

        grouped_items_for_cleaning = defaultdict(lambda: defaultdict(lambda: {'text': None, 'sections': set()}))


        if isinstance(extracted_items, dict):
             for label, items_list_raw in extracted_items.items():
                  if isinstance(items_list_raw, list):
                       for item_data in items_list_raw:
                            if is_resume:
                                 if isinstance(item_data, dict) and 'text' in item_data and 'section' in item_data:
                                      item_text_raw = item_data.get('text', '')
                                      item_section = item_data.get('section', 'Unidentified')
                                      cleaned_text = item_text_raw.lower().strip()

                                      if cleaned_text:
                                           if cleaned_text not in grouped_items_for_cleaning[label]:
                                                grouped_items_for_cleaning[label][cleaned_text]['text'] = item_text_raw
                                           grouped_items_for_cleaning[label][cleaned_text]['sections'].add(item_section)
                                 else:
                                      print(f"Warning: Skipping invalid resume item_data during grouping for label '{label}': {item_data}")


                            else:
                                 if isinstance(item_data, str):
                                      item_text_raw = item_data
                                      cleaned_text = item_text_raw.lower().strip()

                                      if cleaned_text:
                                           if cleaned_text not in grouped_items_for_cleaning[label]:
                                                grouped_items_for_cleaning[label][cleaned_text]['text'] = cleaned_text


                                 else:
                                      print(f"Warning: Expected string item_data for label '{label}' during grouping, but got {type(item_data)}. Skipping.")

                  else:
                       print(f"Warning: Expected items_list_raw for label '{label}' to be a list during grouping, but got {type(items_list_raw)}. Cannot group items.")


        final_cleaned_extracted_items = defaultdict(list)
        for label, cleaned_text_data_dict in grouped_items_for_cleaning.items():
             for cleaned_text, data in cleaned_text_data_dict.items():
                  if is_resume:
                       final_cleaned_extracted_items[label].append({
                            'text': data['text'] if data['text'] is not None else cleaned_text,
                            'sections': list(data['sections'])
                       })
                  else:
                       final_cleaned_extracted_items[label].append(cleaned_text)


        print("Final extracted_items AFTER cleaning/deduplication:", final_cleaned_extracted_items)
        print("---------------------------------------------")

        return dict(final_cleaned_extracted_items)


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Skill_Extractor.py directly for testing.")

    # Import config for the example usage
    from .config import (
        get_spacy_model_name,
        get_requirement_patterns,
        get_core_skill_phrases
    )

    # Instantiate the Skill_Extractor using config
    skill_extractor_instance = SkillExtractor(
        model_name=get_spacy_model_name(),
        requirement_patterns=get_requirement_patterns(),
        core_skill_phrases=get_core_skill_phrases()
    )

    if not hasattr(skill_extractor_instance, '_functional') or not skill_extractor_instance._functional:
         print("\nSkipping extraction examples due to non-functional Skill_Extractor.")
         sys.exit("Skill_Extractor not functional for example.")


    print("\n--- Example 1: Extracting from JD text ---")
    example_jd_text = """
    We are looking for a Backend Developer. Required skill is Python.
    Must have 5 years of experience. Bachelor's degree required.
    Knowledge of Docker is a plus. Familiarity with Flask and SQL.
    Experience with AWS and Git is beneficial.
    """
    extracted_from_jd = skill_extractor_instance.extract_requirements_and_skills(text=example_jd_text, sections=None)
    print("\nExtracted from JD:", extracted_from_jd)
    print("-------------------------------------------")


    print("\n--- Example 2: Extracting from Resume text WITH sections ---")
    example_resume_raw_text = """
    SUMMARY
    Experienced developer.

    SKILLS
    Python, SQL, Docker.

    EXPERIENCE
    Worked on Python projects for 3 years. Used Docker.
    CERTIFICATIONS
    AWS Certified Developer.
    """

    # Dummy Resume_Parser to simulate providing sections
    class DummyResumeParserForExtractor:
         def parse_sections(self, text):
              # Manually define sections based on the example_resume_raw_text
              sections = [
                   {'heading': 'SUMMARY', 'content': 'Experienced developer.'},
                   {'heading': 'SKILLS', 'content': 'Python, SQL, Docker.'},
                   {'heading': 'EXPERIENCE', 'content': 'Worked on Python projects for 3 years. Used Docker.'},
                   {'heading': 'CERTIFICATIONS', 'content': 'AWS Certified Developer.'} # Added CERTIFICATIONS
              ]
              print("DummyResumeParserForExtractor parsed sections (simulated):", sections)
              return sections

    dummy_parser = DummyResumeParserForExtractor()
    example_resume_sections = dummy_parser.parse_sections(example_resume_raw_text)
    extracted_from_resume = skill_extractor_instance.extract_requirements_and_skills(text=example_resume_raw_text, sections=example_resume_sections)

    print("\nExtracted from Resume (with sections):", extracted_from_resume)
    print("----------------------------------------------")