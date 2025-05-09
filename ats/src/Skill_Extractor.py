# Ya
# Skill_Extractor.py

import spacy
# Ensure both Matcher and PhraseMatcher are imported
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
import re
import sys
import os # Import os for environment variable check
from collections import defaultdict # Add this line

# Import Resume_Parser to use its output structure in examples/debugging
# Assuming your Resume_Parser file is named exactly 'Resume_Parser.py'
# Use a try-except in case Resume_Parser.py isn't fully ready yet,
# allowing Skill_Extractor itself to be generated.
try:
    from Resume_Parser import Resume_Parser
except ImportError:
    print("Warning: Could not import Resume_Parser in Skill_Extractor example usage.")
    # Define a dummy class or handle this as needed if running Skill_Extractor standalone
    class Resume_Parser:
        def __init__(self, model_name=None): self.nlp = None
        def parse_sections(self, text): return []

# Import Text_Processor for example usage
try:
    from Text_Processor import Text_Processor
except ImportError:
    print("Warning: Could not import Text_Processor in Skill_Extractor example usage.")
    class Text_Processor:
         def __init__(self, language='english'): pass
         def process_text(self, text): return text
         def tokenize(self, text): return text.split()


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
                                                   Expected format: List[Tuple[str, List[List[Dict]]]]
            core_skill_phrases (list, optional): A list of core skill strings for PhraseMatcher.
                                                  If None, uses default phrases defined here.
                                                  Expected format: List[str]
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
        self._functional = False # Flag to indicate if initialization was successful

        try:
            print(f"\n--- Skill_Extractor Initialization ({self.model_name}) ---")
            print(f"Attempting to load spaCy model: {model_name}")
            # Use the same check as in Resume_Parser for Flask reloader
            if '__main__' in sys.modules or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
                 # In debug mode reloader, spaCy might already be loaded in the parent process.
                 # Checking if it's already loaded might prevent issues,
                 # but simple load is often fine. Explicitly load here.
                 pass # Proceed to load below


            self.nlp = spacy.load(model_name)
            print(f"SpaCy model '{model_name}' loaded successfully.")

            # Check if nlp model is successfully loaded before initializing matchers
            if self.nlp:
                 self.matcher = Matcher(self.nlp.vocab)
                 # --- Print BEFORE adding patterns ---
                 print(f"Attempting to add requirement pattern groups to Matcher (input groups: {len(self.requirement_patterns) if isinstance(self.requirement_patterns, list) else 0}).")
                 self._add_patterns_to_matcher() # Add patterns from the provided list
                 # --- Print AFTER adding patterns ---
                 print(f"Matcher has {len(self.matcher) if self.matcher else 0} rules after calling _add_patterns_to_matcher.")


                 # Initialize PhraseMatcher if core phrases are provided and not empty
                 if self.core_skill_phrases and isinstance(self.core_skill_phrases, list) and len(self.core_skill_phrases) > 0:
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

                 # If NLP loaded and matchers were initialized, set functional flag
                 if self.matcher is not None or self.phrase_matcher is not None:
                     self._functional = True
                 else:
                      print("Warning: NLP model loaded, but neither Matcher nor PhraseMatcher were initialized.")


            else: # If nlp failed to load
                self.matcher = None
                self.phrase_matcher = None
                print("NLP model failed to load. Skill_Extractor initialized without matchers.")


        except OSError:
            print(f"\nERROR: spaCy model '{model_name}' not found during Skill_Extractor init.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # Handle model loading failure
            self.matcher = None
            self.phrase_matcher = None
            self._functional = False
            print("Skill_Extractor initialized without a functional spaCy model or matchers.")
        except Exception as e:
             print(f"\nAn unexpected error occurred during Skill_Extractor initialization: {e}")
             import traceback
             traceback.print_exc()
             self.nlp = None
             self.matcher = None
             self.phrase_matcher = None
             self._functional = False


        # --- Print statements at the very end of __init__ ---
        print(f"\n--- Skill_Extractor Initialization Final Status ({self.model_name}) ---")
        print(f"NLP Model Loaded: {self.nlp is not None}")
        print(f"Matcher Initialized: {self.matcher is not None}")
        print(f"PhraseMatcher Initialized: {self.phrase_matcher is not None}")
        print(f"Skill_Extractor Functional: {self._functional}")
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
         # Ensure each item in the outer list is a TUPLE (label, patterns_for_label)
         # Ensure patterns_for_label is always a LIST of pattern lists (even if only one pattern)
         return [
             ("REQUIRED_SKILL_PHRASE", [pattern_required_skill, pattern_must_have]), # Tuple (label, [pattern1, pattern2])
             ("YEARS_EXPERIENCE", [pattern_years_experience]), # Tuple (label, [pattern1])
             ("KNOWLEDGE_OF", [pattern_knowledge_of]), # Tuple (label, [pattern1])
             ("QUALIFICATION_DEGREE", [pattern_degree]), # Tuple (label, [pattern1])
             # Add other default patterns here following the (label, [pattern_list1, pattern_list2]) format
             # Example of adding a general pattern that might catch various capitalized terms (use with caution)
             # ("PROPER_NOUN_SKILL", [{"POS": "PROPN", "OP": "+"}]) # Single pattern List[Dict] inside a List
         ]


    def _define_default_core_skill_phrases(self):
        """Defines default core skill phrases for PhraseMatcher."""
        # Example core skills - expand this list based on common tech terms or job descriptions!
        return ["Python", "Java", "SQL", "AWS", "Flask", "Django", "React", "Docker", "Git", "Node.js", "C#", "RESTful APIs", "web services", "microservices architecture", "Back-End Developer", "Computer Science", "Software Engineering"]


    def _add_patterns_to_matcher(self):
        """Adds patterns (provided to __init__) to the spaCy Matcher. Includes debug prints."""
        # --- Print at start of method ---
        print(f"Entering _add_patterns_to_matcher. self.matcher upon entry: {self.matcher}")

        # Check if matcher and patterns list are available
        if self.matcher is not None and isinstance(self.requirement_patterns, list):
            print("Matcher is not None and requirement_patterns is a list. Proceeding to add patterns.")

            # --- Group patterns by label ---
            patterns_by_label = {}
            # self.requirement_patterns is expected to be a list of (label, list_of_pattern_lists) tuples
            for item in self.requirement_patterns: # Iterate through the initial config list
                if isinstance(item, tuple) and len(item) == 2:
                    label, patterns_list_for_label = item
                    if not isinstance(label, str):
                         print(f"Warning: Pattern group item is not a string label. Skipping: {item}")
                         continue

                    # patterns_list_for_label should be List[List[Dict]]
                    # Validate the structure of patterns_list_for_label
                    is_valid_patterns_list = isinstance(patterns_list_for_label, list) and \
                                              all(isinstance(p, list) and \
                                                  all(isinstance(d, dict) for d in p) \
                                                  for p in patterns_list_for_label)

                    if is_valid_patterns_list:
                         if label not in patterns_by_label:
                             patterns_by_label[label] = []
                         patterns_by_label[label].extend(patterns_list_for_label) # Add all pattern lists for this label
                         print(f"  Grouped {len(patterns_list_for_label)} pattern list(s) under label '{label}'.")
                    else:
                         print(f"Warning: Patterns for label '{label}' are not in the expected List[List[Dict]] format. Skipping this label.")
                         # Print the received patterns for debugging
                         print(f"  Patterns received for grouping: {patterns_list_for_label}")
                else:
                    print(f"Warning: Item in requirement_patterns is not a (label, patterns) tuple. Skipping: {item}")


            patterns_added_count = 0 # Counts number of pattern lists added
            total_matcher_rules_after_adds = 0 # Tracks total rules in matcher

            # --- Add patterns to matcher, once per unique label ---
            if patterns_by_label: # Check if any patterns were successfully grouped
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

            else:
                 print("Warning: No patterns were successfully grouped by label. Matcher will have 0 rules.")


            # --- Modify this print to show total added pattern lists and final rule count ---
            print(f"Total pattern list groups processed for adding to Matcher at end of method: {patterns_added_count}")
            print(f"Final total rules in Matcher: {len(self.matcher) if self.matcher else 0}") # Report actual final size


        else: # If matcher is None or requirement_patterns is not a list
            print("Matcher is None or requirement_patterns is not a list upon entering _add_patterns_to_matcher. Cannot add patterns.")
            print(f"  Matcher status: {self.matcher is not None}, requirement_patterns is list: {isinstance(self.requirement_patterns, list)}")


    def _add_phrases_to_matcher(self):
         """Adds core skill phrases (provided to __init__) to the PhraseMatcher. Includes debug prints."""
         # --- Print at start of method ---
         print(f"Entering _add_phrases_to_matcher. self.phrase_matcher upon entry: {self.phrase_matcher}, self.nlp is: {self.nlp is not None}, self.core_skill_phrases is: {self.core_skill_phrases is not None and isinstance(self.core_skill_phrases, list) and len(self.core_skill_phrases) > 0}")

         # Check explicitly for None for matchers/nlp, and truthiness for the list
         is_phrase_matcher_available = self.phrase_matcher is not None
         is_nlp_available = self.nlp is not None
         are_core_phrases_available = self.core_skill_phrases is not None and isinstance(self.core_skill_phrases, list) and len(self.core_skill_phrases) > 0

         print(f"  DEBUG: Check values: PhraseMatcher available={is_phrase_matcher_available}, NLP available={is_nlp_available}, CorePhrasesAvailable={are_core_phrases_available}") # Debug print before if

         if is_phrase_matcher_available and is_nlp_available and are_core_phrases_available:
             print("PhraseMatcher, NLP, and core_skill_phrases are available. Proceeding to add phrases.")
             # Ensure core_skill_phrases is a list of strings
             if not isinstance(self.core_skill_phrases, list) or any(not isinstance(p, str) for p in self.core_skill_phrases):
                 print("Error: core_skill_phrases is not in the expected list of string format. Cannot add phrase patterns.")
                 return # Exit method if format is wrong

             patterns = []
             try:
                 for phrase in self.core_skill_phrases:
                      # Use nlp.make_doc to create a Doc object for each phrase
                      # Ensure nlp is not None before calling make_doc
                      if self.nlp:
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
                      else:
                          print("Error: self.nlp is None during phrase pattern creation. Cannot create Doc patterns.")
                          break # Exit phrase creation loop if nlp is None
             except Exception as e:
                  print(f"An unexpected error occurred during phrase pattern creation loop: {e}")
                  import traceback
                  traceback.print_exc()
                  patterns = [] # Ensure patterns is reset on error


             print(f"  Created {len(patterns)} Doc patterns from phrases.")
             if patterns: # Check if the list of Doc patterns is not empty
                  print(f"  Condition 'if patterns:' is True for PhraseMatcher. Attempting to add phrases...")
                  try:
                      print(f"    DEBUG: Adding {len(patterns)} phrase patterns to PhraseMatcher.") # Debug print before add
                      # PhraseMatcher.add expects a label (string) and a list of Doc objects
                      self.phrase_matcher.add("CORE_SKILL", patterns)
                      print(f"    DEBUG: Successfully added phrase patterns. PhraseMatcher now has {len(self.phrase_matcher)} rules.") # Debug print after add
                      # --- Modify this print to show current phrase_matcher size ---
                      print(f"  - Added {len(patterns)} phrase patterns to PhraseMatcher under label 'CORE_SKILL'. PhraseMatcher now has {len(self.phrase_matcher)} rules.")
                  except Exception as e:
                       print(f"  Error adding phrase patterns to PhraseMatcher: {e}")
                       import traceback
                       traceback.print_exc()
             else:
                  print("Warning: No valid phrase patterns created from core_skill_phrases. Skipping PhraseMatcher add.")
         else: # If the main combined check is False
             # Modify this print to show what was missing
             print(f"PhraseMatcher, NLP, or core phrases are NOT all available. Cannot add phrase patterns.")
             print(f"  Check status: PhraseMatcher available = {is_phrase_matcher_available}, NLP available = {is_nlp_available}, Core phrases list not empty = {are_core_phrases_available}") # Detailed check status


    def _get_section_for_token_index(self, token_index: int, sections_list: list) -> str:
         """
         Helper to find the section heading for a given token index.
         Checks which section's token span the token_index falls into.

         Args:
             token_index (int): The index of the token in the spaCy Doc.
             sections_list (list): A list of section dictionaries from Resume_Parser
                                   [{'heading': '...', 'start_token': X, 'end_token': Y}, ...].
                                   These spans should represent the CONTENT of the section.

         Returns:
             str: The heading of the section the token belongs to, or "Unidentified" if none found.
         """
         if not isinstance(sections_list, list):
              print("Warning: sections_list is not a list in _get_section_for_token_index.")
              return "Unidentified"

         if not sections_list: # Check if the list is empty
              # This is expected when processing a JD (sections=None is passed, becomes [] here)
              # Or if the Resume Parser found no sections
              return "Unidentified" # Default if no sections provided or found

         # Iterate through the section content spans provided by Resume_Parser
         # Assumes sections_list is like [{'heading': '...', 'start_token': X, 'end_token': Y}, ...]
         for section in sections_list:
              # Use .get for safety in case keys are missing
              # Check if token_index is within the start (inclusive) and end (exclusive) token indices of the section content
              section_start = section.get('start_token', None)
              section_end = section.get('end_token', None)

              if section_start is not None and section_end is not None and section_start <= token_index < section_end:
                   return section.get('heading', 'Unidentified') # Return the heading of the matched section

         return "Unidentified" # If the token index doesn't fall into any identified section content span


    def extract_requirements_and_skills(self, text: str, sections: list = None) -> dict:
        """
        Processes text using Matcher patterns and links extracted items to sections (for resumes).
        Includes debug prints for the extraction process.

        Args:
            text (str): The input text (Job Description or Resume).
            sections (list, optional): A list of section dictionaries from Resume_Parser
                                       [{'heading': '...', 'start_token': X, 'end_token': Y}, ...]
                                       representing CONTENT spans. Should be None if processing JD.

        Returns:
            dict: For JD: {'PATTERN_LABEL': ['item text', ...], ...}.
                  For Resume: {'PATTERN_LABEL': [{'text': 'item text', 'section': 'Section Name'}, ...], ...}.
                  Returns an empty dict if Skill_Extractor is not functional or extraction fails.
        """
        # Check if Skill_Extractor instance is functional before proceeding
        if not hasattr(self, '_functional') or not self._functional or self.nlp is None:
            print("Skill_Extractor not functional for extraction: Dependencies missing or initialization failed.")
            # Provide status check details
            print(f"Status: Skill_Extractor Functional={self._functional}, NLP Loaded={self.nlp is not None}")
            return {}

        # Check if at least one matcher has rules loaded
        matcher_rules = len(self.matcher) if self.matcher else 0
        phrase_matcher_rules = len(self.phrase_matcher) if self.phrase_matcher else 0

        if matcher_rules == 0 and phrase_matcher_rules == 0:
             print("Skill_Extractor functional, but no rules loaded in Matcher or PhraseMatcher. Extraction will find no items.")
             return {}


        # Process the text with spaCy
        # Using try-except for robustness
        print(f"\nRunning extraction with Matcher rules: {matcher_rules}, PhraseMatcher rules: {phrase_matcher_rules}")
        try:
            doc = self.nlp(text)
        except Exception as e:
             print(f"Error creating spaCy doc from text (length {len(text)}): {e}")
             import traceback
             traceback.print_exc()
             return {}

        # If doc is empty after processing (e.g., text was weird characters), return empty
        if not doc:
             print("SpaCy doc is empty after processing. Cannot extract.")
             return {}


        # --- Existing prints after doc created ---
        print(f"\nExtracting from text (length {len(text)}). Doc token count: {len(doc)}")
        # Print first few tokens for debugging if doc is not too large
        if len(doc) > 0:
             print(f"First 20 tokens of doc: {[token.text for token in doc[:20]]}")
        else:
             print("Doc has 0 tokens.")

        is_resume = sections is not None # Flag to indicate if processing a resume
        print(f"Processing a Resume? : {is_resume}")
        if is_resume:
             print(f"Sections data received (count: {len(sections) if isinstance(sections, list) else 0}).")
        else:
             print("Processing a Job Description (no sections).")

        print("---------------------------------------------")


        # Use defaultdict to store extracted items by label
        # For JD, list of strings. For Resume, list of dicts {'text': '...', 'section': '...'}
        extracted_items = defaultdict(list)


        # Find matches using the Matcher (for requirement patterns) if initialized and has rules
        if self.matcher and matcher_rules > 0:
             print(f"Running Matcher with {matcher_rules} rules on Doc.")
             try:
                 matcher_matches = self.matcher(doc)
                 # --- Add this print after self.matcher(doc) call ---
                 print(f"Result of self.matcher(doc) found {len(matcher_matches)} matches.")
                 if len(matcher_matches) > 0:
                     # Limit printing match details if too many matches
                     print(f"First 5 Matcher matches: {matcher_matches[:min(5, len(matcher_matches))]}")
                 else:
                      print("No Matcher matches found.")

                 # Process Matcher results
                 for match_id, start, end in matcher_matches:
                     span = doc[start:end]
                     label = self.nlp.vocab.strings[match_id]

                     if is_resume: # Processing Resume
                          # Get section heading for the START token of the match span
                          section_heading = self._get_section_for_token_index(start, sections)
                          extracted_items[label].append({
                             "text": span.text,
                             "section": section_heading
                          })
                     else: # Processing JD
                         extracted_items[label].append(span.text)

             except Exception as e:
                  print(f"Error during Matcher processing: {e}")
                  import traceback
                  traceback.print_exc()
                  # Continue with PhraseMatcher even if Matcher fails

        else:
             print("Matcher not initialized or has no rules. Skipping Matcher.")


        # Find matches using the PhraseMatcher (for core skill phrases) if initialized and has rules
        if self.phrase_matcher and phrase_matcher_rules > 0:
             print(f"Running PhraseMatcher with {phrase_matcher_rules} rules on Doc.")
             try:
                 phrase_matches = self.phrase_matcher(doc)
                 # --- Add this print after self.phrase_matcher(doc) call ---
                 print(f"Result of self.phrase_matcher(doc) found {len(phrase_matches)} matches.")
                 if len(phrase_matches) > 0:
                      # Limit printing match details if too many matches
                      print(f"First 5 PhraseMatcher matches: {phrase_matches[:min(5, len(phrase_matches))]}")
                 else:
                      print("No PhraseMatcher matches found.")

                 phrase_label = "CORE_SKILL" # The label used in _add_phrases_to_matcher

                 # Process PhraseMatcher results
                 for match_id, start, end in phrase_matches: # match_id is always the same for PhraseMatcher ('CORE_SKILL')
                      span = doc[start:end]

                      if is_resume: # Processing Resume
                           # Get section heading for the START token of the match span
                           section_heading = self._get_section_for_token_index(start, sections)
                           extracted_items[phrase_label].append({
                                "text": span.text,
                                "section": section_heading
                           })
                      else: # Processing JD
                           extracted_items[phrase_label].append(span.text)

             except Exception as e:
                  print(f"Error during PhraseMatcher processing: {e}")
                  import traceback
                  traceback.print_exc()
                  # Continue even if PhraseMatcher fails

        else:
             print("PhraseMatcher not initialized or has no rules. Skipping PhraseMatcher.")


        # --- Debugging Print BEFORE cleaning/deduplication ---
        # Convert defaultdict to dict for printing to show its state
        print(f"\nExtracted items BEFORE cleaning/deduplication: {dict(extracted_items)}")
        print("---------------------------------------------")


        # --- Clean and Deduplicate ---
        # Deduplication logic needs to handle the two different output formats (JD vs Resume)
        # Initialize using a defaultdict to handle appending
        cleaned_categorized_items = defaultdict(list)

        if extracted_items: # Only process if anything was extracted
            if not is_resume: # Deduplicate for JD (based on text only)
                for label, items in extracted_items.items():
                     if isinstance(items, list): # Ensure the value is a list
                          cleaned_items = [item.lower().strip() for item in items if isinstance(item, str)] # Clean and ensure item is string
                          # Use a set for fast uniqueness check, then convert back to list
                          unique_items = list(set(cleaned_items))
                          if unique_items: cleaned_categorized_items[label].extend(unique_items) # Use extend for defaultdict
                     else:
                         print(f"Warning: Expected list of items for label '{label}' during JD cleaning, but got {type(items)}. Skipping.")

            else: # Deduplicate for Resume (based on text, keep associated sections)
                for label, items_with_sections in extracted_items.items():
                     if isinstance(items_with_sections, list): # Ensure the value is a list
                          unique_text_to_sections = {} # Use a dict to map cleaned text to a list of sections

                          for item_info in items_with_sections: # items_with_sections should be list of dicts
                               if isinstance(item_info, dict) and 'text' in item_info and 'section' in item_info:
                                    cleaned_text = item_info['text'].lower().strip()
                                    section = item_info['section'] # Raw section string

                                    if cleaned_text: # Only process if cleaned text is not empty
                                         if cleaned_text not in unique_text_to_sections:
                                              unique_text_to_sections[cleaned_text] = set() # Use a set to collect unique sections

                                         if section and isinstance(section, str): # Ensure section is a non-empty string
                                              unique_text_to_sections[cleaned_text].add(section) # Add section to the set
                                         elif section is None:
                                              # If section was None (should be 'Unidentified' but handle gracefully)
                                              unique_text_to_sections[cleaned_text].add("Unidentified")
                                         # If section is empty string or not str, it's ignored by the add


                               else:
                                   print(f"Warning: Unexpected item_info format during resume deduplication for label '{label}': {item_info}. Skipping.")


                          # Convert back to the desired output format (list of dicts) if unique items exist
                          if unique_text_to_sections:
                               cleaned_categorized_items[label].extend([
                                    {"text": text, "sections": list(sections_set)} # Convert section set back to list
                                    for text, sections_set in unique_text_to_sections.items()
                               ])
                     else:
                         print(f"Warning: Expected list of items for label '{label}' during Resume cleaning, but got {type(items_with_sections)}. Skipping.")


        # Convert defaultdict to dict for the final return
        final_extracted_items = dict(cleaned_categorized_items)


        # --- Debugging Print AFTER cleaning/deduplication ---
        print(f"Final extracted_items AFTER cleaning/deduplication: {final_extracted_items}")
        print("---------------------------------------------")


        return final_extracted_items


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Skill_Extractor.py directly for testing.")

    # Define configuration for the example usage
    # Use a smaller model for direct testing if md/lg is slow
    example_model_name = 'en_core_web_sm'

    # Define simple example patterns consistent with how they are used in Resume_Scorer example
    # Structure needs to be List[Tuple[str, List[List[Dict]]]]
    example_skill_patterns = [
         ("REQUIRED_SKILL_PHRASE", [[{"LOWER": "required"}, {"LOWER": "skill"}], [{"LOWER": "must"}, {"LOWER": "have"}]]),
         ("EXAMPLE_TECH_SKILL", [[{"LOWER": "python"}], [{"LOWER": "java"}], [{"LOWER": "flask"}]]), # Example tech skills pattern
         ("YEARS_EXPERIENCE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "years"}, {"LOWER": "of"}, {"LOWER": "experience"}]]),
         ("EXAMPLE_QUALIFICATION", [[{"LOWER": "bachelor's"}], [{"LOWER": "master's"}]]),
         # Note: PhraseMatcher uses a single label ('CORE_SKILL') and takes Doc objects created from phrases.
         # We pass the raw phrases list to Skill_Extractor init.
    ]
    # Example core phrases for PhraseMatcher
    example_core_phrases = ["Python", "Flask", "SQL"]


    # Instantiate Skill_Extractor with config
    skill_extractor = Skill_Extractor(
        model_name=example_model_name,
        requirement_patterns=example_skill_patterns, # Pass example patterns
        core_skill_phrases=example_core_phrases # Pass example phrases
    )

    # Check if the extractor is functional before proceeding with extraction examples
    # This check is based on the _functional flag set during init
    if not hasattr(skill_extractor, '_functional') or not skill_extractor._functional:
         print("\nSkipping extraction example due to non-functional extractor.")
         # No need to exit explicitly, just skip the extraction part

    else:
         # Define example JD and Resume text for extraction testing
         example_jd_text = """
         We are looking for a Python Developer. Required skills include Python and Java.
         Must have 5+ years of experience. Bachelor's degree is required.
         Knowledge of Docker is a plus. Experience with Flask and SQL databases is beneficial.
         """

         example_resume_text = """
         Summary: Experienced Developer with 6 years of experience.
         Skills: Python, Flask, SQL.
         Education: Bachelor's degree in Computer Science.
         Experience: Worked on Python and Java projects. Handled database tasks.
         """

         # Need a dummy Doc object and section data from Resume_Parser for testing Resume extraction
         # In a real app, these come from Resume_Parser(text).parse_sections()

         print("\nRunning Example Resume_Parser to get dummy sections for testing...")
         try:
              # Instantiate a temporary parser just for the example sections
              temp_parser_for_example = Resume_Parser(model_name=example_model_name)
              if temp_parser_for_example.nlp: # Check if temp parser loaded successfully
                   dummy_sections_data_for_test = temp_parser_for_example.parse_sections(example_resume_text)
                   print(f"\nExample Parser identified sections: {dummy_sections_data_for_test}")
              else:
                   print("\nWarning: Could not initialize Resume_Parser for example. Using approximate dummy section data.")
                   # Fallback dummy data if parser fails or not importable/functional
                   # Approximate based on token counts from a small model
                   dummy_sections_data_for_test = [
                      {'heading': 'Summary', 'start_token': 5, 'end_token': 11}, # Approx span of Summary content
                      {'heading': 'Skills', 'start_token': 12, 'end_token': 17}, # Approx span of Skills content
                      {'heading': 'Education', 'start_token': 18, 'end_token': 25}, # Approx span of Education content
                      {'heading': 'Experience', 'start_token': 26, 'end_token': 36}, # Approx span of Experience content
                      # Add other dummy sections if needed for testing _get_section_for_token_index coverage
                      {'heading': 'Unidentified (Header)', 'start_token': 0, 'end_token': 5} # Before first section
                   ]

         except Exception as e:
              print(f"\nAn error occurred during example Resume_Parser usage: {e}")
              import traceback
              traceback.print_exc()
              print("\nWarning: Could not get example section data. Resume extraction test may be limited.")
              dummy_sections_data_for_test = [] # Ensure it's an empty list on error


         # --- Run Extraction Examples ---

         # Extract from JD (without sections)
         print("\nExtracting from JD (without Sections) (Example):")
         jd_extracted = skill_extractor.extract_requirements_and_skills(
             text=example_jd_text, # Pass text
             sections=None # No sections for JD
         )

         print("\nJD Extracted Items (Example):")
         if jd_extracted:
              for label, items_list in jd_extracted.items():
                  print(f"- {label}: {items_list}")
         else:
              print("No items extracted from JD.")
         print("--- Example Extraction Complete ---")


         # Extract from Resume (with sections)
         print("\nExtracting from Resume (with Sections) (Example):")
         resume_extracted_with_sections = skill_extractor.extract_requirements_and_skills(
             text=example_resume_text, # Pass text
             sections=dummy_sections_data_for_test # Pass sections list (content spans)
         )

         print("\nResume Extracted Items (Example):")
         if resume_extracted_with_sections:
              for label, items_list in resume_extracted_with_sections.items():
                  print(f"- {label}:")
                  for item_info in items_list: # item_info is a dict here
                       # Use .get for safety in case keys are missing (shouldn't be with current code)
                       print(f"  - Text: '{item_info.get('text', 'N/A')}', Section: '{item_info.get('section', 'N/A')}'")
         else:
              print("No items extracted from Resume.")
         print("--- Example Extraction Complete ---")