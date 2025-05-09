# Skill_Extractor.py

import spacy
# Ensure both Matcher and PhraseMatcher are imported
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
import re
import sys

# Removed module-level spaCy loading

# Import Resume_Parser to use its output structure in examples/debugging
# Assuming your Resume_Parser file is named exactly 'Resume_Parser.py'
try:
    from Resume_Parser import Resume_Parser
except ImportError:
    print("Warning: Could not import Resume_Parser. Example usage may fail.")
    # Define a dummy class or handle this as needed if running Skill_Extractor standalone
    class Resume_Parser:
        def parse_sections(self, text): return []


class Skill_Extractor:
    """
    A class to extract potential skills and requirements using spaCy Matcher,
    configurable with model name, patterns, and core phrases. Includes extensive debug prints.
    """
    def __init__(self, model_name: str = 'en_core_web_sm', requirement_patterns: list = None, core_skill_phrases: list = None):
        """
        Initializes the Skill_Extractor by loading a spaCy model and setting up matchers.
        Includes debug prints for initialization status.

        Args:
            model_name (str): The name of the spaCy model to load.
            requirement_patterns (list, optional): A list of (label, pattern_list) tuples for the Matcher.
                                                   If None, uses default patterns defined here.
            core_skill_phrases (list, optional): A list of core skill strings for PhraseMatcher.
                                                  If None, uses default phrases defined here.
        """
        self.model_name = model_name
        # Define default patterns and phrases within the class
        self._default_requirement_patterns = self._define_default_requirement_patterns()
        self._default_core_skill_phrases = self._define_default_core_skill_phrases()

        # Use provided patterns/phrases or defaults
        self.requirement_patterns = requirement_patterns if requirement_patterns is not None else self._default_requirement_patterns
        self.core_skill_phrases = core_skill_phrases if core_skill_phrases is not None else self._default_core_skill_phrases

        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None

        try:
            print(f"\n--- Skill_Extractor Initialization ({self.model_name}) ---")
            print(f"Attempting to load spaCy model: {model_name}")
            self.nlp = spacy.load(model_name)
            print(f"SpaCy model '{model_name}' loaded successfully.")

            self.matcher = Matcher(self.nlp.vocab)
            # --- Print BEFORE adding patterns ---
            print(f"Attempting to add requirement pattern groups to Matcher (total groups: {len(self.requirement_patterns) if self.requirement_patterns else 0}).")
            self._add_patterns_to_matcher() # Add patterns from the provided list
            # --- Print AFTER adding patterns ---
            print(f"Matcher has {len(self.matcher) if self.matcher else 0} rules after calling _add_patterns_to_matcher.")


            # Initialize PhraseMatcher if core phrases are provided and not empty
            if self.core_skill_phrases and len(self.core_skill_phrases) > 0:
                 print(f"Core skill phrases provided ({len(self.core_skill_phrases)}). Attempting to initialize PhraseMatcher.")
                 self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
                 # --- Print BEFORE adding phrases ---
                 print(f"Attempting to add {len(self.core_skill_phrases)} core skill phrases to PhraseMatcher.")
                 self._add_phrases_to_matcher()
                 # --- Print AFTER adding phrases ---
                 print(f"PhraseMatcher has {len(self.phrase_matcher) if self.phrase_matcher else 0} rules after calling _add_phrases_to_matcher.")
            else:
                 self.phrase_matcher = None
                 print("No core skill phrases provided or empty list. PhraseMatcher not used.")


        except OSError:
            print(f"\nERROR: spaCy model '{model_name}' not found.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # Handle model loading failure
            self.matcher = None
            self.phrase_matcher = None
            print("Skill_Extractor initialized without a functional spaCy model or matchers.")
        except Exception as e:
             print(f"\nAn unexpected error occurred during Skill_Extractor initialization: {e}")
             import traceback
             traceback.print_exc()
             self.nlp = None
             self.matcher = None
             self.phrase_matcher = None


        # --- Print statements at the very end of __init__ ---
        print(f"\n--- Skill_Extractor Initialization Final Status ({self.model_name}) ---")
        print(f"NLP Model Loaded: {self.nlp is not None}")
        print(f"Matcher Initialized: {self.matcher is not None}")
        print(f"PhraseMatcher Initialized: {self.phrase_matcher is not None}")
        # Prints of counts will be included by the ones inside the add methods and after the calls
        print("---------------------------------------------")


    def _define_default_requirement_patterns(self):
         """Defines default spaCy Matcher patterns."""
         # Example patterns (replace with your full set from Stage 3, Part 1)
         # These patterns look for phrases indicating requirements or specific entities
         pattern_required_skill = [{"LOWER": "required"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
         pattern_must_have = [{"LOWER": "must"}, {"LOWER": "have"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
         # Updated YEARS_EXPERIENCE pattern to potentially match "X years experience" as well
         pattern_years_experience = [{"POS": "NUM", "OP": "+"}, {"LOWER": "+", "OP": "?"}, {"LOWER": "years"}, {"LOWER": "of", "OP": "?"}, {"LOWER": "experience"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}]

         pattern_knowledge_of = [{"LOWER": "knowledge"}, {"LOWER": "of"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}]
         pattern_degree = [{"LOWER": {"IN": ["bachelor's", "master's", "bachelor", "master", "bs", "ms"]}}, {"LOWER": "degree", "OP": "?"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] # Added BS/MS variations

         # Return a list of (label, list_of_pattern_lists) tuples
         # Matcher.add expects List[List[Dict]] for the patterns argument
         return [
             ("REQUIRED_SKILL_PHRASE", [pattern_required_skill, pattern_must_have]), # List containing two pattern lists
             ("YEARS_EXPERIENCE", [pattern_years_experience]), # List containing one pattern list
             ("KNOWLEDGE_OF", [pattern_knowledge_of]), # List containing one pattern list
             ("QUALIFICATION_DEGREE", [pattern_degree]), # List containing one pattern list
             # Add other default patterns here following the (label, [pattern_list1, pattern_list2]) format
         ]


    def _define_default_core_skill_phrases(self):
        """Defines default core skill phrases for PhraseMatcher."""
        # Example core skills - expand this list in your app.py config!
        return ["Python", "Java", "SQL", "AWS", "Flask", "Django", "React", "Docker", "Git", "Node.js", "C#", "RESTful APIs", "web services", "microservices architecture"]


    def _add_patterns_to_matcher(self):
        """Adds patterns (provided to __init__) to the spaCy Matcher. Includes debug prints."""
        # --- Print at start of method ---
        print(f"Entering _add_patterns_to_matcher. self.matcher upon entry: {self.matcher}")

        # Existing print: print(f"Attempting to add ...")

        if self.matcher is not None: # Check explicitly for None
            print("Matcher is not None. Proceeding to add patterns.")

            # --- Group patterns by label ---
            patterns_by_label = {}
            # requirement_patterns is a list of (label, list_of_pattern_lists) tuples
            if isinstance(self.requirement_patterns, list):
                 for label, patterns_list_for_label in self.requirement_patterns:
                     if not isinstance(label, str):
                         print(f"Warning: Pattern group item is not a string label. Skipping: {label}")
                         continue
                     if label not in patterns_by_label:
                         patterns_by_label[label] = []

                     # patterns_list_for_label should be List[List[Dict]]
                     if isinstance(patterns_list_for_label, list) and all(isinstance(p, list) and all(isinstance(d, dict) for d in p) for p in patterns_list_for_label):
                         patterns_by_label[label].extend(patterns_list_for_label) # Add all pattern lists for this label
                         print(f"  Grouped {len(patterns_list_for_label)} pattern list(s) under label '{label}'.")
                     else:
                          print(f"Warning: Patterns for label '{label}' are not in the expected List[List[Dict]] format. Skipping this label.")
                          print(f"  Patterns received for grouping: {patterns_list_for_label}")
            else:
                 print("Warning: requirement_patterns is not a list. Cannot group patterns.")


            patterns_added_count = 0 # Counts number of pattern lists added
            total_matcher_rules_after_adds = 0 # Tracks total rules in matcher

            # --- Add patterns to matcher, once per unique label ---
            for label, all_patterns_for_label in patterns_by_label.items(): # Iterate through grouped patterns
                if all_patterns_for_label: # Check if there are any pattern lists for this label
                    print(f"  Attempting to add {len(all_patterns_for_label)} pattern list(s) for unique label '{label}'.")
                    try:
                        # --- THIS IS THE CORRECTED ADD CALL ---
                        # We are passing the list of pattern lists (List[List[Dict]]) directly
                        # Matcher.add expects List[List[Dict]] as the patterns argument
                        self.matcher.add(label, all_patterns_for_label) # Add all patterns for this label at once

                        patterns_added_count += len(all_patterns_for_label) # Count total pattern lists added across all unique labels
                        total_matcher_rules_after_adds = len(self.matcher) # Get the current total rule count after this add

                        print(f"    DEBUG: Successfully added {len(all_patterns_for_label)} pattern list(s) for label '{label}'. Matcher now has {total_matcher_rules_after_adds} rules.")
                        # --- Modify this print to show current matcher size ---
                        print(f"  - Added patterns for label '{label}'. Matcher now has {total_matcher_rules_after_adds} rules.")
                    except Exception as e:
                         print(f"  Error adding patterns for label '{label}': {e}")
                         import traceback
                         traceback.print_exc()
                         print(f"    DEBUG: Failed to add patterns for label '{label}'. Patterns were: {all_patterns_for_label}")
                else:
                     print(f"  Warning: No pattern lists collected for unique label '{label}'. Skipping add.")


            # --- Modify this print to show total added pattern lists and final rule count ---
            print(f"Total pattern list groups added to Matcher at end of method: {patterns_added_count}")
            print(f"Final total rules in Matcher: {len(self.matcher) if self.matcher else 0}") # Report actual final size


        else: # Check explicitly for None
            print("Matcher is None upon entering _add_patterns_to_matcher. Cannot add patterns.") # Modify print


    def _add_phrases_to_matcher(self):
         """Adds core skill phrases (provided to __init__) to the PhraseMatcher. Includes debug prints."""
         # --- Print at start of method ---
         print(f"Entering _add_phrases_to_matcher. self.phrase_matcher upon entry: {self.phrase_matcher}, self.nlp is: {self.nlp is not None}, self.core_skill_phrases is: {self.core_skill_phrases is not None and len(self.core_skill_phrases) > 0}")

         # Existing print: print(f"Attempting to add ...")

         # --- Modified Check and prints ---
         # Check explicitly for None for matchers/nlp, and truthiness for the list
         is_phrase_matcher_available = self.phrase_matcher is not None
         is_nlp_available = self.nlp is not None
         are_core_phrases_available = self.core_skill_phrases is not None and len(self.core_skill_phrases) > 0

         print(f"  DEBUG: Check values: PhraseMatcher available={is_phrase_matcher_available}, NLP available={is_nlp_available}, CorePhrasesAvailable={are_core_phrases_available}") # Debug print before if

         if is_phrase_matcher_available and is_nlp_available and are_core_phrases_available:
             print("PhraseMatcher, NLP, and core_skill_phrases are available. Proceeding to add phrases.")
             # Ensure core_skill_phrases is a list of strings
             if not isinstance(self.core_skill_phrases, list) or any(not isinstance(p, str) for p in self.core_skill_phrases):
                 print("Error: core_skill_phrases is not in the expected list of string format. Cannot add phrase patterns.")
                 return # Exit method if format is wrong

             patterns = []
             for phrase in self.core_skill_phrases:
                 try:
                     doc_pattern = self.nlp.make_doc(phrase)
                     if doc_pattern and len(doc_pattern) > 0: # Ensure make_doc creates a non-empty doc
                         patterns.append(doc_pattern)
                     else:
                         print(f"  Warning: nlp.make_doc('{phrase}') resulted in an empty or zero-length Doc. Skipping.")
                 except Exception as e:
                      print(f"  Error creating Doc for phrase '{phrase}': {e}")
                      import traceback
                      traceback.print_exc()

             print(f"  Created {len(patterns)} Doc patterns from phrases.")
             if patterns: # Check if the list of Doc patterns is not empty
                  print(f"  Condition 'if patterns:' is True for PhraseMatcher. Attempting to add phrases...")
                  try:
                      print(f"    DEBUG: Adding {len(patterns)} phrase patterns to PhraseMatcher.") # Debug print before add
                      self.phrase_matcher.add("CORE_SKILL", patterns)
                      print(f"    DEBUG: Successfully added phrase patterns. PhraseMatcher now has {len(self.phrase_matcher)} rules.") # Debug print after add
                      # --- Modify this print to show current phrase_matcher size ---
                      print(f"  - Added {len(patterns)} phrase patterns to PhraseMatcher under label 'CORE_SKILL'. PhraseMatcher now has {len(self.phrase_matcher)} rules.")
                  except Exception as e:
                       print(f"  Error adding phrase patterns: {e}")
                       import traceback
                       traceback.print_exc()
             else:
                  print("Warning: No phrase patterns created from core_skill_phrases. Skipping PhraseMatcher.")
         else: # If the main combined check is False
             # Modify this print to show what was missing
             print(f"PhraseMatcher, NLP, or core phrases are NOT all available. Cannot add phrase patterns.")
             print(f"  Check status: PhraseMatcher available = {is_phrase_matcher_available}, NLP available = {is_nlp_available}, Core phrases list not empty = {are_core_phrases_available}") # Detailed check status


    def _get_section_for_token_index(self, token_index: int, sections_list: list) -> str:
         """
         Helper to find the section heading for a given token index.
         """
         if not sections_list: # Check if the list is empty or None
              return "Unidentified" # Default if no sections provided (e.g., processing JD)

         # Iterate through the sections provided by Resume_Parser
         # Assumes sections_list is like [{'heading': '...', 'start_token': X, 'end_token': Y}, ...]
         for section in sections_list:
              # Use .get for safety in case keys are missing (though parser should provide them)
              if section.get('start_token', -1) <= token_index < section.get('end_token', -1):
                   return section.get('heading', 'Unidentified') # Return the heading of the matched section

         return "Unidentified" # If the token index doesn't fall into any identified section


    def extract_requirements_and_skills(self, text: str, sections: list = None) -> dict:
        """
        Processes text using Matcher patterns and links extracted items to sections.
        Includes debug prints for the extraction process.

        Args:
            text (str): The input text (Job Description or Resume).
            sections (list, optional): A list of section dictionaries from Resume_Parser
                                       [{'heading': '...', 'start_token': X, 'end_token': Y}, ...].
                                       Should be None if processing JD.

        Returns:
            dict: For JD: {'PATTERN_LABEL': ['item text', ...], ...}.
                  For Resume: {'PATTERN_LABEL': [{'text': 'item text', 'sections': ['Section Name']}, ...], ...}.
                  Returns an empty dict if spaCy or matchers are not loaded or no patterns/phrases are added.
        """
        # Check if core dependencies are functional and have rules
        matcher_rules = len(self.matcher) if self.matcher else 0
        phrase_matcher_rules = len(self.phrase_matcher) if self.phrase_matcher else 0

        if self.nlp is None or (self.matcher is None and self.phrase_matcher is None) or \
           (self.matcher and matcher_rules == 0 and self.phrase_matcher and phrase_matcher_rules == 0):
            print("Skill_Extractor not fully functional for extraction: Dependencies missing or no rules loaded.")
            print(f"Status: NLP Loaded={self.nlp is not None}, Matcher={self.matcher is not None} ({matcher_rules} rules), PhraseMatcher={self.phrase_matcher is not None} ({phrase_matcher_rules} rules).")
            # Additional checks to see if the matchers are None even if init said they weren't
            print(f"Debug check within extract: self.matcher is {self.matcher}, self.phrase_matcher is {self.phrase_matcher}")
            return {}

        # Process the text with spaCy
        print(f"\nRunning extraction with Matcher rules: {matcher_rules}, PhraseMatcher rules: {phrase_matcher_rules}")
        try:
            doc = self.nlp(text)
        except Exception as e:
             print(f"Error creating spaCy doc from text (length {len(text)}): {e}")
             import traceback
             traceback.print_exc()
             return {}


        # --- Existing prints after doc created ---
        print(f"\nExtracting from text (length {len(text)}). Doc token count: {len(doc)}")
        print(f"First 20 tokens of doc: {[token.text for token in doc[:20]]}")
        print(f"Sections data received (for Resume?): {sections is not None and len(sections) > 0}")
        print("---------------------------------------------")

        # Return empty if doc is empty (e.g., failed text reading)
        if len(doc) == 0:
             print("SpaCy doc is empty. Cannot extract.")
             return {}


        extracted_items = {}

        # Find matches using the Matcher (for requirement patterns) if initialized and has rules
        if self.matcher and matcher_rules > 0:
             print(f"Running Matcher with {matcher_rules} rules on Doc.")
             matcher_matches = self.matcher(doc)
             # --- Add this print after self.matcher(doc) call ---
             print(f"Result of self.matcher(doc) found {len(matcher_matches)} matches.")
             if len(matcher_matches) > 0:
                 print(f"First 5 Matcher matches: {matcher_matches[:5]}")
             for match_id, start, end in matcher_matches:
                 span = doc[start:end]
                 label = self.nlp.vocab.strings[match_id]

                 if label not in extracted_items:
                     if sections is None: extracted_items[label] = []
                     else: extracted_items[label] = []

                 section_heading = self._get_section_for_token_index(start, sections)

                 if sections is None: # Processing JD
                     extracted_items[label].append(span.text)
                 else: # Processing Resume
                      extracted_items[label].append({
                         "text": span.text,
                         "section": section_heading
                      })
        else:
             print("Matcher not initialized or has no rules. Skipping Matcher.")


        # Find matches using the PhraseMatcher (for core skill phrases) if initialized and has rules
        if self.phrase_matcher and phrase_matcher_rules > 0:
             print(f"Running PhraseMatcher with {phrase_matcher_rules} rules on Doc.")
             phrase_matches = self.phrase_matcher(doc)
             # --- Add this print after self.phrase_matcher(doc) call ---
             print(f"Result of self.phrase_matcher(doc) found {len(phrase_matches)} matches.")
             if len(phrase_matches) > 0:
                 print(f"First 5 PhraseMatcher matches: {phrase_matches[:5]}")
             phrase_label = "CORE_SKILL" # The label used in _add_phrases_to_matcher

             if phrase_label not in extracted_items:
                  if sections is None: extracted_items[phrase_label] = []
                  else: extracted_items[phrase_label] = []


             for match_id, start, end in phrase_matches:
                  span = doc[start:end]
                  section_heading = self._get_section_for_token_index(start, sections) # Get section for phrase match

                  if sections is None: # Processing JD
                      extracted_items[phrase_label].append(span.text)
                  else: # Processing Resume
                       extracted_items[phrase_label].append({
                            "text": span.text,
                            "section": section_heading
                       })
        else:
             print("PhraseMatcher not initialized or has no rules. Skipping PhraseMatcher.")


        # --- Existing print BEFORE cleaning/deduplication ---
        print(f"\nExtracted items BEFORE cleaning/deduplication: {extracted_items}")
        print("---------------------------------------------")


        # --- Clean and Deduplicate ---
        # Deduplication logic needs to handle the two different output formats (JD vs Resume)
        cleaned_categorized_items = {} # Initialize here

        if extracted_items: # Only process if anything was extracted
            if sections is None: # Deduplicate for JD (based on text)
                for label, items in extracted_items.items():
                     cleaned_items = [item.lower().strip() for item in items if isinstance(item, str)] # Ensure item is string
                     unique_items = list(set(cleaned_items))
                     if unique_items: cleaned_categorized_items[label] = unique_items
            else: # Deduplicate for Resume (based on text, keep associated sections)
                for label, items_with_sections in extracted_items.items():
                     unique_text_to_sections = {}
                     for item_info in items_with_sections: # items_with_sections should be list of dicts
                          if isinstance(item_info, dict) and 'text' in item_info and 'section' in item_info:
                               cleaned_text = item_info['text'].lower().strip()
                               section = item_info['section']
                               if cleaned_text not in unique_text_to_sections:
                                    unique_text_to_sections[cleaned_text] = []
                               if section and section not in unique_text_to_sections[cleaned_text]:
                                    unique_text_to_sections[cleaned_text].append(section)
                          else:
                              print(f"Warning: Unexpected item_info format during resume deduplication: {item_info}")

                     if unique_text_to_sections: # Convert back to the desired output format if unique items exist
                          cleaned_categorized_items[label] = []
                          for text, sections_list in unique_text_to_sections.items():
                               cleaned_categorized_items[label].append({
                                    "text": text,
                                    "sections": sections_list
                               })


        # --- Existing print BEFORE final return ---
        print(f"Final extracted_items AFTER cleaning/deduplication: {cleaned_categorized_items}")
        print("---------------------------------------------")


        return cleaned_categorized_items


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Skill_Extractor.py directly for testing.")

    # Define configuration for the example usage
    # Use a smaller model for direct testing if md/lg is slow
    example_model_name = 'en_core_web_sm'
    example_requirement_patterns = [
         ("EXAMPLE_TECH_SKILL", [{"LOWER": "python"}, {"LOWER": "java"}, {"LOWER": "flask"}]),
         ("EXAMPLE_EXP_PHRASE", [{"POS": "NUM", "OP": "+"}, {"LOWER": "years"}, {"LOWER": "of"}, {"LOWER": "experience"}]),
         ("EXAMPLE_QUALIFICATION", [{"LOWER": {"IN": ["bachelor's", "master's"]}}, {"LOWER": "degree"}])
    ]
    example_core_skill_phrases = ["Python", "Flask", "SQL"]


    # Instantiate Skill_Extractor with config
    skill_extractor = Skill_Extractor(
        model_name=example_model_name,
        requirement_patterns=example_requirement_patterns,
        core_skill_phrases=example_core_skill_phrases # Pass phrases if using PhraseMatcher
    )

    # Need a dummy Doc object and section data from Resume_Parser for testing
    # In a real app, these come from Resume_Parser(text).parse_sections() and nlp(text)

    resume_text_for_test = """
    Summary
    Experienced Python Developer.

    Experience
    Worked on Python projects using Flask. 5+ years of experience.

    Skills
    Python, Flask, SQL.

    Education
    Bachelor's degree in Computer Science.
    """

    # Check if the extractor is functional before proceeding with extraction examples
    matcher_rules_example = len(skill_extractor.matcher) if skill_extractor.matcher else 0
    phrase_matcher_rules_example = len(skill_extractor.phrase_matcher) if skill_extractor.phrase_matcher else 0

    if skill_extractor.nlp is None or ((skill_extractor.matcher is None or matcher_rules_example == 0) and (skill_extractor.phrase_matcher is None or phrase_matcher_rules_example == 0)):
         print("\nSkipping extraction example due to non-functional extractor or no rules loaded.")
         # No need to exit explicitly, just skip the extraction part

    else:
         # Manually create dummy section data based on token indices (approximate for demo)
         # Need to process the text to get accurate token indices if Resume_Parser is not available
         try:
             parser_for_example = Resume_Parser(model_name=example_model_name)
             if parser_for_example.nlp is not None:
                 dummy_sections_data_for_test = parser_for_example.parse_sections(resume_text_for_test)
                 print(f"\nExample Parser identified sections: {dummy_sections_data_for_test}")
             else:
                  print("\nWarning: Could not initialize Resume_Parser for example. Using dummy section data.")
                  # Fallback dummy data if parser fails
                  dummy_sections_data_for_test = [
                     {'heading': 'Summary', 'start_token': 1, 'end_token': 5},
                     {'heading': 'Experience', 'start_token': 6, 'end_token': 17},
                     {'heading': 'Skills', 'start_token': 18, 'end_token': 23},
                     {'heading': 'Education', 'start_token': 24, 'end_token': 31}
                  ]

             # Extract with section linking (for Resume)
             print("\nExtracting from Resume with Sections (Example):")
             resume_extracted_with_sections = skill_extractor.extract_requirements_and_skills(
                 text=resume_text_for_test, # Pass text
                 sections=dummy_sections_data_for_test # Pass sections list
             )

             if resume_extracted_with_sections:
                 for label, items_list in resume_extracted_with_sections.items():
                     print(f"- {label}:")
                     for item_info in items_list:
                          # Item info is now a dict like {'text': '...', 'sections': ['...']}
                          print(f"  - Text: '{item_info['text']}', Sections: {item_info['sections']}")
             else:
                 print("No items extracted from Resume.")

             # Extract without section linking (for JD)
             job_description_text_for_test = """
             Required skills: Python, Java. Must have 3+ years of experience. Knowledge of Docker is a plus.
             """
             print("\nExtracting from JD (without Sections) (Example):")
             jd_extracted = skill_extractor.extract_requirements_and_skills(
                 text=job_description_text_for_test,
                 sections=None # No sections for JD
             )
             if jd_extracted:
                  for label, items_list in jd_extracted.items():
                      print(f"- {label}: {items_list}")
             else:
                  print("No items extracted from JD.")

         except Exception as e:
              print(f"\nAn error occurred during the example usage: {e}")
              import traceback
              traceback.print_exc()