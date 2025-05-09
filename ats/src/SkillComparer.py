# SkillComparer.py
# SkillComparer.py

from collections import defaultdict
import re # Still useful for potential string cleaning/normalization
import sys # For debugging output

# Import the dependencies this class will use
# Use try-except for robustness during development
try:
    from Skill_Extractor import Skill_Extractor
except ImportError:
    print("Warning: Could not import Skill_Extractor in SkillComparer. Using dummy.")
    class Skill_Extractor:
         def __init__(self, model_name=None, requirement_patterns=None, core_skill_phrases=None):
              self.nlp = None # Ensure nlp is None if not loaded
              self.matcher = None
              self.phrase_matcher = None
              self._functional = False
              print("Dummy Skill_Extractor initialized for SkillComparer.")
         def extract_requirements_and_skills(self, text, sections=None):
             print("Dummy Skill_Extractor extract_requirements_and_skills called by SkillComparer.")
             return {} # Always return empty

try:
    from Resume_Parser import Resume_Parser
except ImportError:
    print("Warning: Could not import Resume_Parser in SkillComparer. Using dummy.")
    class Resume_Parser:
         def __init__(self, model_name=None):
              self.nlp = None
              print("Dummy Resume_Parser initialized for SkillComparer.")
         def parse_sections(self, text):
              print("Dummy Resume_Parser parse_sections called by SkillComparer.")
              return []


class SkillComparer:
    """
    Compares skills extracted from a job description and a resume,
    applies weighting based on requirement types and resume sections,
    and identifies matched and missing items.
    Requires Skill_Extractor and Resume_Parser dependencies.
    Includes detailed debug prints for tracing comparison logic.
    """
    def __init__(self, skill_extractor: Skill_Extractor, resume_parser: Resume_Parser,
                 requirement_weights: dict, section_weights: dict):
        """
        Initializes the SkillComparer with dependencies and weighting configurations.

        Args:
            skill_extractor (Skill_Extractor): An instance of Skill_Extractor.
            resume_parser (Resume_Parser): An instance of Resume_Parser.
            requirement_weights (dict): Dictionary mapping skill labels to their base weights.
            section_weights (dict): Dictionary mapping resume section headings to score multipliers.
        """
        print("\n--- SkillComparer Initialized ---")
        self.skill_extractor = skill_extractor
        self.resume_parser = resume_parser # Resume_Parser is needed here to parse resume sections

        self.requirement_weights = requirement_weights # Store requirement weights
        self.section_weights = section_weights # Store section weights

        # Check if critical dependencies are functional
        # Check if they are instances of the actual classes, not dummies, and if their NLP models loaded
        is_se_functional = isinstance(self.skill_extractor, Skill_Extractor) and hasattr(self.skill_extractor, '_functional') and self.skill_extractor._functional
        is_rp_functional = isinstance(self.resume_parser, Resume_Parser) and hasattr(self.resume_parser, 'nlp') and self.resume_parser.nlp is not None # Check if parser's NLP loaded

        self._functional = is_se_functional and is_rp_functional

        if not self._functional:
             print("Warning: SkillComparer initialized but core dependencies (Skill_Extractor or Resume_Parser) are not functional. Skill comparison will not work.")
        else:
             # Further check if Skill_Extractor has rules loaded if it is functional
             matcher_has_rules = len(self.skill_extractor.matcher) if hasattr(self.skill_extractor, 'matcher') and self.skill_extractor.matcher is not None else 0
             phrase_matcher_has_rules = len(self.skill_extractor.phrase_matcher) if hasattr(self.skill_extractor, 'phrase_matcher') and self.skill_extractor.phrase_matcher is not None else 0
             if not (matcher_has_rules > 0 or phrase_matcher_has_rules > 0):
                  print("Warning: SkillComparer functional, but Skill_Extractor has no rules loaded. Skill extraction will find no items.")

        print("---------------------------------")


    def compare_skills(self, job_description: str, resume_text: str) -> tuple:
        """
        Extracts skills from JD and Resume and compares them, applying weights.

        Args:
            job_description (str): The raw text of the job description.
            resume_text (str): The raw text of the resume.

        Returns:
            tuple: Contains:
                - achieved_weighted_score (float): Sum of weighted scores for matched items.
                - total_possible_weighted_score (float): Sum of base weights for all extracted JD items.
                - matched_items (dict): Dictionary of matched items by label with details.
                - missing_items (dict): Dictionary of missing item texts by label.
                Returns (0.0, 0.0, {}, {}) if SkillComparer is not functional or comparison fails.
        """
        # Check if SkillComparer instance itself is functional before processing
        if not self._functional:
             print("Error: SkillComparer instance is not functional. Cannot compare skills. Returning zero scores and empty items.")
             return 0.0, 0.0, {}, {}

        # Check if Skill_Extractor actually loaded any rules
        matcher_has_rules = len(self.skill_extractor.matcher) if hasattr(self.skill_extractor, 'matcher') and self.skill_extractor.matcher is not None else 0
        phrase_matcher_has_rules = len(self.skill_extractor.phrase_matcher) if hasattr(self.skill_extractor, 'phrase_matcher') and self.skill_extractor.phrase_matcher is not None else 0

        if matcher_has_rules == 0 and phrase_matcher_rules == 0:
             print("Warning: SkillComparer functional, but Skill_Extractor has no rules loaded. Skipping skill extraction and comparison.")
             # Return 0s and empty lists/dicts
             return 0.0, 0.0, {}, {}


        achieved_weighted_score = 0.0
        total_possible_weighted_score = 0.0
        cleaned_matched_items = defaultdict(list)
        cleaned_missing_items = defaultdict(list)


        print("--- Running Skill Extraction and Comparison ---")
        try: # This try block encompasses the entire skill match comparison process
            # --- Extraction calls (JD and Resume) ---
            # JD extraction: pass raw text, no sections
            print("\nRunning Skill_Extractor on JD...")
            # Ensure Skill_Extractor is a valid instance before calling its method
            if not isinstance(self.skill_extractor, Skill_Extractor) or not hasattr(self.skill_extractor, 'extract_requirements_and_skills'):
                 print("Error: Skill_Extractor dependency is invalid or missing required method. Cannot extract JD skills.")
                 jd_extracted = {}
            else:
                 jd_extracted = self.skill_extractor.extract_requirements_and_skills(text=job_description, sections=None)
            print("SkillComparer DEBUG: Extracted JD items:", jd_extracted) # <-- DEBUG PRINT
            print("------------------------------")


            # Resume extraction: pass raw text and parsed sections
            # Use Resume_Parser to get sections (Parser needs raw text)
            print("\nRunning Resume_Parser on Resume...")
            # Ensure Resume_Parser dependency is a valid instance before using it
            if not isinstance(self.resume_parser, Resume_Parser) or not hasattr(self.resume_parser, 'parse_sections'):
                 print("Error: Resume_Parser dependency is invalid or missing method. Cannot parse resume sections for skill match.")
                 resume_sections = []
            else:
                 try:
                    resume_sections = self.resume_parser.parse_sections(resume_text)
                    # print(f"Resume Sections Identified by Parser: {resume_sections}") # Keep this print in parser, avoid large print here
                 except Exception as e:
                      print(f"Error during Resume_Parser execution: {e}")
                      import traceback
                      traceback.print_exc()
                      print("Proceeding with empty resume sections list.")
                      resume_sections = [] # Ensure it's empty on error

            print("------------------------------")

            print("\nRunning Skill_Extractor on Resume...")
            # Pass the sections list (containing CONTENT spans) to Skill_Extractor
            # Ensure Skill_Extractor is a valid instance before calling its method
            if not isinstance(self.skill_extractor, Skill_Extractor) or not hasattr(self.skill_extractor, 'extract_requirements_and_skills'):
                 print("Error: Skill_Extractor dependency is invalid or missing required method. Cannot extract Resume skills.")
                 resume_extracted_with_sections = {}
            else:
                 resume_extracted_with_sections = self.skill_extractor.extract_requirements_and_skills(text=resume_text, sections=resume_sections)
            print("SkillComparer DEBUG: Extracted Resume items (with sections):", resume_extracted_with_sections) # <-- DEBUG PRINT
            print("------------------------------")


            # Check if extraction yielded results for JD
            if not jd_extracted:
                print("Warning: Skill extraction returned no items for JD. Skill match score will be 0.")
                # total_possible_weighted_score remains 0, score will be 0, missing items will be empty

            # --- Collect ALL unique extracted items (text only) from Resume for easy lookup ---
            # This set is used for a quick check if a JD item *might* be in the resume.
            all_resume_extracted_flat_text_only = set()
            if resume_extracted_with_sections:
                 print("\nFlattening Resume extracted items for lookup...")
                 try:
                     for label, items_list in resume_extracted_with_sections.items():
                          # Ensure items_list is a list of dicts
                          if isinstance(items_list, list):
                               for item_info in items_list:
                                    # Ensure item_info is a dict and has the 'text' key
                                    if isinstance(item_info, dict) and 'text' in item_info:
                                         cleaned_text = item_info['text'].lower().strip()
                                         if cleaned_text: # Add only if text is not empty after cleaning
                                              all_resume_extracted_flat_text_only.add(cleaned_text)
                                    else:
                                         print(f"Warning: Unexpected item_info format during resume flattening for label '{label}': {item_info}")
                          else:
                               print(f"Warning: Unexpected items_list format for label '{label}' during resume flattening: {items_list}")

                     print(f"Flattened Resume Extracted Items (Text Only Set) created with {len(all_resume_extracted_flat_text_only)} unique items.")
                 except Exception as e:
                      print(f"Error flattening resume extracted items: {e}")
                      import traceback
                      traceback.print_exc()
                      all_resume_extracted_flat_text_only = set() # Ensure it's a set on error
                 print("------------------------------")

            print("SkillComparer DEBUG: Flattened Resume Items (Text Only Set):", all_resume_extracted_flat_text_only) # <-- DEBUG PRINT - Moved outside try/except for flattening


            # --- Compare JD items to Resume items ---
            print("\nComparing JD extracted items to Resume extracted items for scoring...")
            if jd_extracted: # Only compare if JD extraction had results
                # Iterate through the extracted requirements from the Job Description
                for jd_label, jd_items_list_raw in jd_extracted.items():
                    # Get the base weight for this category from the config
                    # Use .get with a default if label not found in config (defaults to Unidentified weight)
                    base_item_weight = self.requirement_weights.get(jd_label, self.requirement_weights.get("Unidentified", 0.1)) # Default to 0.1 if Unidentified not found


                    # Now iterate through each specific item within the JD label
                    if isinstance(jd_items_list_raw, list): # Ensure it's a list
                         for jd_item_text_raw in jd_items_list_raw:
                              if not isinstance(jd_item_text_raw, str):
                                   print(f"Warning: Expected string item for label '{jd_label}' but got {type(jd_item_text_raw)}. Skipping.")
                                   continue # Skip to the next item


                              jd_item_text = jd_item_text_raw.lower().strip() # Clean JD item text for comparison
                              if not jd_item_text: # Skip if cleaned JD text is empty
                                   print(f"Warning: Cleaned JD item text for label '{jd_label}' is empty. Skipping.")
                                   continue


                              print(f"\nSkillComparer DEBUG: Checking JD item '{jd_item_text_raw}' (Label: {jd_label}, Cleaned: '{jd_item_text}')...") # <-- DEBUG PRINT - Added newline

                              # Add the base weight of this item to the total possible score *regardless* of whether it's found.
                              # This ensures the score is a proportion of matched weight vs total JD weight.
                              if base_item_weight > 0:
                                   total_possible_weighted_score += base_item_weight
                                   print(f"SkillComparer DEBUG:   - Added base weight {base_item_weight:.2f} to total possible score. Total Possible: {total_possible_weighted_score:.2f}") # <-- DEBUG PRINT
                              else:
                                   print(f"SkillComparer DEBUG:   - JD item has base weight {base_item_weight:.2f}. Not adding to total possible score.") # <-- DEBUG PRINT


                              # --- Check if this cleaned JD item text exists in the flattened set of Resume item texts ---
                              if jd_item_text in all_resume_extracted_flat_text_only:
                                  print(f"SkillComparer DEBUG:   -> Found '{jd_item_text}' in flattened Resume set.") # <-- DEBUG PRINT
                                  # Item is potentially matched. Now find where it was matched in the Resume
                                  # to apply section weights.
                                  achieved_item_weight_for_this_item = 0.0 # Weight for this specific item match
                                  max_section_multiplier = 0.0
                                  sections_where_matched = set()

                                  # Collect all matching item_info dicts from the detailed resume extraction
                                  matching_resume_items_info = [] # Initialize here


                                  # Find the corresponding item(s) in the resume_extracted_with_sections
                                  if resume_extracted_with_sections: # Only search if resume extraction had results
                                       for resume_label, resume_items_list in resume_extracted_with_sections.items():
                                            if isinstance(resume_items_list, list): # Ensure items_list is a list
                                                 for item_info in resume_items_list: # item_info should be a dict {'text': '...', 'section': '...'}
                                                      # Ensure item_info is a dict and has the 'text' key
                                                      if isinstance(item_info, dict) and 'text' in item_info:
                                                           # Clean the text from the resume item info for comparison
                                                           cleaned_resume_item_text = item_info['text'].lower().strip()
                                                           if cleaned_resume_item_text == jd_item_text: # Match on cleaned text
                                                                matching_resume_items_info.append(item_info) # Found a match, add its info
                                                      else:
                                                           print(f"Warning: Unexpected item_info format during detailed match lookup for label '{resume_label}': {item_info}")
                                            else:
                                                 print(f"Warning: Unexpected items_list format for resume label '{resume_label}' during detailed match lookup: {resume_items_list}")


                                  print(f"SkillComparer DEBUG:   -> Detailed matches found in Resume for '{jd_item_text}':", matching_resume_items_info) # <-- DEBUG PRINT


                                  if matching_resume_items_info: # Check if any matching item_info was found in detailed search
                                      print(f"SkillComparer DEBUG:     -> Applying section weights for '{jd_item_text}'...") # <-- DEBUG PRINT
                                      # Apply section weights. Get the maximum section multiplier
                                      # from all the sections where this item was found in the resume.
                                      for item_info in matching_resume_items_info: # Iterate through all places it was found
                                           # Ensure item_info is a dict and has the 'sections' key, and 'sections' is a list
                                           if isinstance(item_info, dict) and 'sections' in item_info and isinstance(item_info['sections'], list):
                                                for section_heading in item_info['sections']: # For each section it was listed in
                                                     # Use .get for safety, default multiplier is 1.0 if section not in config
                                                     # Use .get for safety when looking up section_weights
                                                     # Note: The section heading should ideally be consistent (e.g., lowercased, normalized)
                                                     # The Skill_Extractor _get_section_for_token_index returns the *raw* heading string from the parser.
                                                     # The SECTION_MULTIPLIERS_CONFIG keys should match the possible outputs of Resume_Parser.parse_sections 'heading'.
                                                     # Let's ensure lookup is robust by trying raw and cleaned heading.
                                                     # Get the multiplier for the section, defaulting if not found
                                                     section_multiplier = self.section_weights.get(section_heading, self.section_weights.get(section_heading.lower().strip() if isinstance(section_heading, str) else "", self.section_weights.get("Unidentified", 1.0)))
                                                     max_section_multiplier = max(max_section_multiplier, section_multiplier) # Keep track of the max
                                                     sections_where_matched.add(section_heading) # Collect unique raw sections it was in
                                                     print(f"SkillComparer DEBUG:       Section '{section_heading}' has multiplier {section_multiplier:.2f}. Max multiplier so far: {max_section_multiplier:.2f}") # <-- DEBUG PRINT
                                           else:
                                                print(f"Warning: Unexpected item_info format or missing/invalid 'sections' key during section processing for item '{item_info.get('text', 'N/A')}': {item_info}. Applying Unidentified multiplier.")
                                                # If sections data is bad, treat multiplier as default
                                                section_multiplier = self.section_weights.get("Unidentified", 1.0) # Use Unidentified default
                                                max_section_multiplier = max(max_section_multiplier, section_multiplier)
                                                sections_where_matched.add("Unidentified") # Add unidentified section for reporting


                                      # Calculate the achieved weight for this specific item match
                                      # Base JD weight * maximum section multiplier where found
                                      # Ensure base_item_weight is > 0 before multiplying
                                      achieved_item_weight_for_this_item = base_item_weight * max_section_multiplier if base_item_weight > 0 else 0.0
                                      achieved_weighted_score += achieved_item_weight_for_this_item # Adding to total achieved

                                      # Record the matched item, including where it was found
                                      # Use the raw text from JD for output, not the cleaned one
                                      print(f"SkillComparer DEBUG:     -> Matched item '{jd_item_text_raw}' (Label: {jd_label}) matched with weight {achieved_item_weight_for_this_item:.4f} (Base: {base_item_weight:.2f}, Max Multiplier: {max_section_multiplier:.2f}). Sections: {list(sections_where_matched)}") # <-- DEBUG PRINT
                                      print(f"SkillComparer DEBUG:     -> Total achieved_weighted_score is now {achieved_weighted_score:.4f}") # <-- DEBUG PRINT

                                      cleaned_matched_items[jd_label].append({
                                          "text": jd_item_text_raw, # Store original JD text
                                          "matched_in_sections": list(sections_where_matched), # Convert set to list for output
                                          "achieved_weight": float(achieved_item_weight_for_this_item) # Store calculated weight
                                      })
                                      print(f"SkillComparer DEBUG:     -> Added '{jd_item_text_raw}' to cleaned_matched_items['{jd_label}']") # <-- DEBUG PRINT

                                  else:
                                       # This case should theoretically not be reached if the flat set is built correctly
                                       # and Skill_Extractor works correctly. But handle defensively.
                                       print(f"SkillComparer DEBUG:   -> Found in flat set, but NO detailed match info found for '{jd_item_text}'. Not added to matched_items.") # <-- DEBUG PRINT


                              else: # Item is missing!
                                  print(f"SkillComparer DEBUG:   -> '{jd_item_text}' NOT found in flattened Resume set.") # <-- DEBUG PRINT
                                  print(f"SkillComparer DEBUG:     -> Added to missing_items: '{jd_item_text_raw}' (Label: {jd_label})") # <-- DEBUG PRINT
                                  cleaned_missing_items[jd_label].append(jd_item_text_raw)
                              print("-" * 20) # <-- DEBUG PRINT separator for items
                         else:
                              print(f"Error: Expected string item for label '{jd_label}' but got {type(jd_item_text_raw)}. Skipping.")
                    else: # If jd_items_list_raw is not a list
                         print(f"Error: Expected jd_items_list_raw for label '{jd_label}' to be a list but got {type(jd_items_list_raw)}. Cannot iterate items.")

            else: # If jd_extracted is empty
                print("Warning: No items extracted from JD. Cannot calculate skill match score.")
                # Return 0s and empty lists/dicts in this specific sub-case
                return 0.0, 0.0, {}, {}


            print("Comparison complete for JD items.")
            print("-" * 25)

        except Exception as e: # This except must align with the main try block above
             print(f"SkillComparer ERROR: An error occurred during skill match extraction or comparison:") # <-- DEBUG PRINT - Modified this print
             import traceback
             traceback.print_exc()
             # On error during comparison, return current scores (likely 0) and empty lists/dicts
             return achieved_weighted_score, total_possible_weighted_score, {}, {} # Return empty on error


        # Convert defaultdict to regular dict for the return
        final_matched_items = dict(cleaned_matched_items)
        final_missing_items = dict(cleaned_missing_items)

        print(f"\nSkillComparer DEBUG: Final Matched Items Before Return: {final_matched_items}") # <-- DEBUG PRINT
        print(f"SkillComparer DEBUG: Final Missing Items Before Return: {final_missing_items}") # <-- DEBUG PRINT
        print("----------------------------------------") # <-- DEBUG PRINT

        return achieved_weighted_score, total_possible_weighted_score, final_matched_items, final_missing_items


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running SkillComparer.py directly for testing.")

    # Define configuration needed for dependencies in the example
    example_model_name = 'en_core_web_sm' # Use sm for faster testing

    # Define weights for the example
    example_requirement_weights = {
        "REQUIRED_SKILL_PHRASE": 1.5,
        "YEARS_EXPERIENCE": 1.2,
        "QUALIFICATION_DEGREE": 1.0,
        "KNOWLEDGE_OF": 0.8,
        "CORE_SKILL": 1.0,
        "Unidentified": 0.2,
        "EXAMPLE_TECH_SKILL": 1.0, # Weight for example tech skill pattern
    }
    example_section_weights = {
         "Experience": 1.5,
         "Skills": 1.0,
         "Education": 0.8,
         "Projects": 1.1,
         "Summary": 0.9,
         "Unidentified (Header)": 0.5,
         "Unidentified (Footer)": 0.5,
         "Unidentified (Full Document)": 0.5,
         "Unidentified": 0.5,
         "Languages": 1.0
    }

    # Define example patterns and phrases for Skill_Extractor
    example_skill_patterns = [
         ("REQUIRED_SKILL_PHRASE", [[{"LOWER": "required"}, {"LOWER": "skill"}], [{"LOWER": "must"}, {"LOWER": "have"}]]),
         ("EXAMPLE_TECH_SKILL", [[{"LOWER": "python"}], [{"LOWER": "java"}], [{"LOWER": "flask"}]]),
         ("YEARS_EXPERIENCE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "years"}, {"LOWER": "of", "OP": "?"}, {"LOWER": "experience"}]]), # Made 'of' optional
         ("QUALIFICATION_DEGREE", [[{"LOWER": {"IN": ["bachelor's", "master's"]}}, {"LOWER": "degree"}]]),
    ]
    example_core_phrases = ["Python", "Flask", "SQL", "Java", "Docker", "Git", "AWS"]


    # --- Instantiate Dependencies for Example (Needs dummy Text_Processor too) ---
    print("\n--- Initializing Dependencies for SkillComparer Example ---")
    # Need a dummy Text_Processor for the dependencies
    class DummyTextProcessorForSkillComparer:
         def process_text(self, text): return text.lower().strip() if isinstance(text, str) else ""
         def tokenize(self, text): return text.split() if isinstance(text, str) else []
         language = 'english'
         def __init__(self, language='english'):
             self.language = language
             # Simulate spaCy model loading might happen here in real TextProcessor if needed by others
             # For this dummy, we don't need complex NLP, just basic text handling.
             print("DummyTextProcessorForSkillComparer initialized.")


    # Skill Extractor needs model and patterns/phrases config
    example_skill_extractor = Skill_Extractor(
        model_name=example_model_name,
        requirement_patterns=example_skill_patterns,
        core_skill_phrases=example_core_phrases
    )

    # Resume Parser needs model
    example_resume_parser = Resume_Parser(model_name=example_model_name)

    # Instantiate dummy Text_Processor and pass it if Skill_Extractor or Resume_Parser needed it directly
    # (They don't in the current design, Text_Processor is used by Resume_Scorer and passed as dependency)
    # But SkillComparer itself doesn't directly use Text_Processor, its dependencies do.
    # So we don't need to pass DummyTextProcessor to SkillComparer __init__ itself, just ensure dependencies init.

    print("-----------------------------------------------------------")


    # Instantiate SkillComparer with dependencies and weights
    skill_comparison_engine = SkillComparer(
        skill_extractor=example_skill_extractor,
        resume_parser=example_resume_parser,
        requirement_weights=example_requirement_weights,
        section_weights=example_section_weights
    )

    # Check if the comparer is functional before running comparison example
    if not hasattr(skill_comparison_engine, '_functional') or not skill_comparison_engine._functional:
         print("\nSkipping skill comparison example due to non-functional SkillComparer.")
         sys.exit("SkillComparer not functional for example.")


    # Define example JD and Resume text
    example_jd_text = """
    We are looking for a Backend Developer. Required skills include Python and Java.
    Must have 5 years of experience. Bachelor's degree in Computer Science is required.
    Knowledge of Docker is a plus. Experience with Flask and SQL databases is beneficial.
    We use AWS and Git.
    """

    example_resume_text = """
    John Doe
    Summary: Experienced Developer with 6 years of experience.
    Skills: Python, Flask, SQL.
    Education: Bachelor's degree in Computer Science.
    Experience: Worked on Python and Java projects for 3 years. Handled database tasks.
    Projects: Built app using Docker. Used Git for version control.
    Certifications: AWS Certified.
    """

    # Perform the comparison
    print("\n--- Running Example Skill Comparison ---")
    achieved_weighted_score, total_possible_weighted_score, matched_items, missing_items = skill_comparison_engine.compare_skills(
        example_jd_text, example_resume_text
    )

    # Print results of the comparison
    print("\n--- Example Comparison Results ---")
    print(f"Achieved Weighted Score: {achieved_weighted_score:.4f}")
    print(f"Total Possible Weighted Score: {total_possible_weighted_score:.4f}")

    print("\nMatched Items:")
    if matched_items:
        for label, items in matched_items.items():
            print(f"- {label}:")
            if isinstance(items, list):
                 for item_info in items:
                      print(f"  - Text: '{item_info.get('text', 'N/A')}', Sections: {item_info.get('matched_in_sections', ['N/A'])}, Weight: {item_info.get('achieved_weight', 0.0):.4f}")
            else:
                 print(f"  Warning: Expected list for label '{label}', got {type(items)}")
    else:
        print("No items matched.")

    print("\nMissing Items:")
    if missing_items:
        for label, items in missing_items.items():
            print(f"- {label}: {items}")
    else:
        print("No items missing.")
    print("----------------------------------------")