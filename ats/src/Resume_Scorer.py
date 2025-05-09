# Regenerate Resume_Scorer.py completely with error print removed and all debug prints.
# Imports
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import defaultdict
import math
import sys

# Import your other classes with capitalized filenames
# Assuming Text_Processor, Skill_Extractor, Resume_Parser are in separate files
try:
    from Text_Processor import Text_Processor
except ImportError:
    print("Warning: Could not import Text_Processor.")
    # Define a dummy class or handle this as needed
    class Text_Processor:
         def __init__(self, language='english'): pass
         def process_text(self, text): return text
         def tokenize(self, text): return text.split() # Simple fallback

try:
    from Skill_Extractor import Skill_Extractor
except ImportError:
    print("Warning: Could not import Skill_Extractor.")
    class Skill_Extractor:
         def __init__(self, model_name=None, requirement_patterns=None, core_skill_phrases=None):
              self.nlp = None # Ensure nlp is None if not loaded
              self.matcher = None
              self.phrase_matcher = None
         def extract_requirements_and_skills(self, text, sections=None): return {} # Always return empty

try:
    from Resume_Parser import Resume_Parser
except ImportError:
    print("Warning: Could not import Resume_Parser.")
    class Resume_Parser:
         def __init__(self, model_name=None): self.nlp = None
         def parse_sections(self, text): return []


class Resume_Scorer:
    """
    Calculates similarity and skill match scores between a job description and a resume.
    Uses Text_Processor, Skill_Extractor, and Resume_Parser dependencies.
    """
    def __init__(self, text_processor: Text_Processor, skill_extractor: Skill_Extractor, resume_parser: Resume_Parser,
                 tfidf_weight: float = 0.5, skill_match_weight: float = 0.5,
                 requirement_weights: dict = None, section_weights: dict = None):
        """
        Initializes the Resume_Scorer with its dependencies and scoring weights.

        Args:
            text_processor (Text_Processor): An instance of Text_Processor.
            skill_extractor (Skill_Extractor): An instance of Skill_Extractor.
            resume_parser (Resume_Parser): An instance of Resume_Parser.
            tfidf_weight (float): The weight for the TF-IDF similarity score (0.0 to 1.0).
            skill_match_weight (float): The weight for the prioritized skill match score (0.0 to 1.0).
                                         Ensure tfidf_weight + skill_match_weight <= 1.0.
            requirement_weights (dict, optional): Dictionary mapping skill labels to their base weights.
                                                  If None, uses defaults.
            section_weights (dict, optional): Dictionary mapping resume section headings to score multipliers.
                                              If None, uses defaults.
        """
        self.text_processor = text_processor
        self.skill_extractor = skill_extractor
        self.resume_parser = resume_parser

        # Validate and store weights
        if not (0.0 <= tfidf_weight <= 1.0 and 0.0 <= skill_match_weight <= 1.0 and (tfidf_weight + skill_match_weight) <= 1.0):
             print("Warning: Scoring weights are invalid. Using default weights (0.5 TFIDF, 0.5 Skill Match).")
             self.tfidf_weight = 0.5
             self.skill_match_weight = 0.5
        else:
             self.tfidf_weight = tfidf_weight
             self.skill_match_weight = skill_match_weight

        # Define default weights if not provided
        self.requirement_weights = requirement_weights if requirement_weights is not None else self._define_default_requirement_weights()
        self.section_weights = section_weights if section_weights is not None else self._define_default_section_weights()

        # Check if critical dependencies (with spaCy models) are functional
        # Skill_Extractor and Resume_Parser have an nlp attribute if model loaded
        self._functional = (hasattr(self.skill_extractor, 'nlp') and self.skill_extractor.nlp is not None) and \
                           (hasattr(self.resume_parser, 'nlp') and self.resume_parser.nlp is not None) and \
                           (hasattr(self.text_processor, 'language')) # Basic check for text processor


        # Further check if matchers have rules loaded in Skill_Extractor
        if self._functional:
            matcher_has_rules = hasattr(self.skill_extractor, 'matcher') and self.skill_extractor.matcher is not None and len(self.skill_extractor.matcher) > 0
            phrase_matcher_has_rules = hasattr(self.skill_extractor, 'phrase_matcher') and self.skill_extractor.phrase_matcher is not None and len(self.skill_extractor.phrase_matcher) > 0

            # Scorer is only functional for skill match if extractor has rules in at least one matcher
            if not (matcher_has_rules or phrase_matcher_has_rules):
                 print("Warning: Skill_Extractor initialized but has no rules loaded in Matcher or PhraseMatcher. Skill match score will be 0.")
                 # Set skill weight to 0 if no rules are loaded to avoid errors and signal issue
                 # Adjust total weight if skill weight becomes 0
                 if self.skill_match_weight > 0:
                      self.tfidf_weight += self.skill_match_weight # Add original skill weight to tfidf
                      self.skill_match_weight = 0.0
                      print(f"Adjusted weights: TFIDF={self.tfidf_weight}, Skill Match={self.skill_match_weight}")

            # Check if text processor language is set
            if not hasattr(self.text_processor, 'language') or not self.text_processor.language:
                 print("Warning: Text_Processor instance has no language attribute. Ensure language is set for processing.")
                 # This might affect text processing but won't make the scorer non-functional itself

        else:
             print("Warning: Core dependencies (Skill_Extractor or Resume_Parser) are not functional. TF-IDF and Skill Match scores will be 0.")
             # If dependencies are not functional, set both weights to 0 to return 0 scores
             self.tfidf_weight = 0.0
             self.skill_match_weight = 0.0


    def _define_default_requirement_weights(self):
        """Defines default base weights for different requirement categories."""
        # Default weights if none are provided
        return {
            "REQUIRED_SKILL_PHRASE": 1.5,
            "YEARS_EXPERIENCE": 1.2,
            "QUALIFICATION_DEGREE": 1.0,
            "KNOWLEDGE_OF": 0.8,
            "CORE_SKILL": 1.0, # Default weight for core skills
            "Unidentified": 0.2, # Default weight for items matched by general patterns or in unidentified sections
        }

    def _define_default_section_weights(self):
        """Defines default score multipliers for different resume sections."""
        # Default multipliers if none are provided
        return {
             "Experience": 1.5,
             "Skills": 1.0,
             "Education": 0.8,
             "Projects": 1.1,
             "Summary": 0.9,
             "Unidentified (Header)": 0.5,
             "Unidentified (Footer)": 0.5,
             "Unidentified (Full Document)": 0.5, # If no sections found by parser
             "Unidentified": 0.5, # Fallback if section is labeled "Unidentified" by parser/extractor
        }


    def calculate_scores(self, job_description: str, resume_text: str) -> dict:
        """
        Calculates the TF-IDF similarity, prioritized skill match score, and combined score.

        Args:
            job_description (str): The raw text of the job description.
            resume_text (str): The raw text of the resume.

        Returns:
            dict: A dictionary containing 'tfidf_score', 'prioritized_skill_score',
                  'combined_score', 'matched_items', and 'missing_items'.
        """
        # Ensure the scorer instance itself is functional
        if not hasattr(self, '_functional') or not self._functional:
             print("Error: Scorer instance is not functional. Returning zero scores.")
             return {
                "tfidf_score": 0.0,
                "prioritized_skill_score": 0.0,
                "combined_score": 0.0,
                "matched_items": {},
                "missing_items": {}
             }

        # --- 1. Text Processing (Language handled by Text_Processor instance) ---
        print("\n--- Running Text Processing ---")
        jd_processed = self.text_processor.process_text(job_description)
        resume_processed = self.text_processor.process_text(resume_text)
        print("------------------------------")

        # Check if processed texts are empty
        if not jd_processed or not resume_processed:
             print("Warning: Processed text is empty. Cannot calculate scores.")
             return {
                "tfidf_score": 0.0,
                "prioritized_skill_score": 0.0,
                "combined_score": 0.0,
                "matched_items": {},
                "missing_items": {}
             }


        # --- 2. TF-IDF Similarity Score ---
        # Only calculate if TF-IDF weight is positive
        tfidf_score = 0.0
        if self.tfidf_weight > 0 and jd_processed and resume_processed:
            print("--- Calculating TF-IDF Score ---")
            try:
                # TfidfVectorizer expects a list of documents
                documents = [jd_processed, resume_processed]
                tfidf_vectorizer = TfidfVectorizer()
                tfidf_matrix = tfidf_vectorizer.fit_transform(documents)

                # Calculate cosine similarity between the two documents
                # similarity_matrix is a 2x2 matrix, we need the non-identity similarity
                similarity_matrix = cosine_similarity(tfidf_matrix)
                tfidf_score = similarity_matrix[0, 1] # Similarity between doc 0 (JD) and doc 1 (Resume)
                print(f"TF-IDF Raw Score: {tfidf_score}")
            except Exception as e:
                print(f"Error calculating TF-IDF score: {e}")
                tfidf_score = 0.0 # Set score to 0 on error
            print("------------------------------")
        else:
             print("Skipping TF-IDF calculation as weight is 0 or text is empty.")


        # --- 3. Prioritized Skill Match Score ---
        # Only calculate if skill match weight is positive and dependencies are functional with rules
        skill_match_score = 0.0
        total_possible_weighted_score = 0.0
        achieved_weighted_score = 0.0

        # Use defaultdict to simplify appending items to categories
        cleaned_matched_items = defaultdict(list)
        cleaned_missing_items = defaultdict(list)

        # Check if Skill_Extractor is functional and has rules before attempting extraction
        matcher_rules = len(self.skill_extractor.matcher) if hasattr(self.skill_extractor, 'matcher') and self.skill_extractor.matcher is not None else 0
        phrase_matcher_rules = len(self.skill_extractor.phrase_matcher) if hasattr(self.skill_extractor, 'phrase_matcher') and self.skill_extractor.phrase_matcher is not None else 0

        if self.skill_match_weight > 0 and self._functional and (matcher_rules > 0 or phrase_matcher_rules > 0):
            print("--- Calculating Prioritized Skill Match Score ---")
            try:
                # --- Extract Categorized Items (Using the Skill_Extractor dependency) ---
                # JD extraction: pass raw text, no sections
                print("\nRunning Skill_Extractor on JD...")
                jd_extracted = self.skill_extractor.extract_requirements_and_skills(text=job_description, sections=None)
                print("------------------------------")

                # Resume extraction: pass raw text and parsed sections
                # Use Resume_Parser to get sections (Parser needs raw text)
                print("\nRunning Resume_Parser on Resume...")
                resume_sections = self.resume_parser.parse_sections(resume_text)
                print(f"Resume Sections Identified: {resume_sections}")
                print("------------------------------")

                print("\nRunning Skill_Extractor on Resume...")
                resume_extracted_with_sections = self.skill_extractor.extract_requirements_and_skills(text=resume_text, sections=resume_sections)
                print("------------------------------")


                # Check if extraction yielded results for JD or Resume
                if not jd_extracted and not resume_extracted_with_sections:
                    print("Warning: Skill extraction returned no items for JD or Resume.")
                    # Scores remain 0.0, matched/missing remain empty


                # --- Collect ALL unique extracted items (text only) from Resume for easy lookup ---
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
                                             all_resume_extracted_flat_text_only.add(item_info['text'].lower().strip()) # Add cleaned text to set
                                        else:
                                             print(f"Warning: Unexpected item_info format during resume flattening: {item_info}")
                              else:
                                   print(f"Warning: Unexpected items_list format for label '{label}' during resume flattening: {items_list}")

                         print(f"Flattened Resume Extracted Items (Text Only Set) created with {len(all_resume_extracted_flat_text_only)} unique items.")
                     except Exception as e:
                         print(f"Error flattening resume extracted items: {e}")
                         all_resume_extracted_flat_text_only = set() # Ensure it's a set on error
                     print("------------------------------")


                # --- Compare JD items to Resume items ---
                print("\nComparing JD extracted items to Resume extracted items...")
                if jd_extracted:
                    # Iterate through the extracted requirements from the Job Description
                    for jd_label, jd_items_list_raw in jd_extracted.items():
                        # Get the base weight for this category from the config
                        # Use .get with a default if label not found in config (defaults to Unidentified weight)
                        base_item_weight = self.requirement_weights.get(jd_label, self.requirement_weights.get("Unidentified", 0.1)) # Default to 0.1 if Unidentified not found


                        # Add to total possible weighted score if item has a positive weight
                        # Every item extracted from the JD contributes to the total possible score
                        if base_item_weight > 0 and isinstance(jd_items_list_raw, list): # Ensure it's a list
                             total_possible_weighted_score += base_item_weight * len(jd_items_list_raw)
                        elif base_item_weight <= 0 and isinstance(jd_items_list_raw, list):
                             print(f"Warning: JD items found for label '{jd_label}' but its base weight is {base_item_weight}. Not added to total possible score.")
                        elif not isinstance(jd_items_list_raw, list):
                              print(f"Warning: Expected list of JD items for label '{jd_label}' but got {type(jd_items_list_raw)}. Skipping for scoring.")
                              continue # Skip to the next JD item


                        # Now iterate through each specific item within the JD label
                        if isinstance(jd_items_list_raw, list): # Re-check type safety
                             for jd_item_text_raw in jd_items_list_raw:
                                  if not isinstance(jd_item_text_raw, str):
                                       print(f"Warning: Expected string item for label '{jd_label}' but got {type(jd_item_text_raw)}. Skipping.")
                                       continue # Skip to the next item


                                  jd_item_text = jd_item_text_raw.lower().strip() # Clean JD item text for comparison

                                  print(f"Checking JD item: '{jd_item_text}' (Label: {jd_label})...")

                                  # --- Check if this cleaned JD item text exists in the flattened set of Resume item texts ---
                                  if jd_item_text in all_resume_extracted_flat_text_only:
                                      # Item is potentially matched. Now find where it was matched in the Resume
                                      # to apply section weights.
                                      achieved_item_weight_for_this_item = 0.0 # Weight for this specific item match
                                      max_section_multiplier = 0.0
                                      sections_where_matched = set()

                                      # Collect all matching item_info dicts from the detailed resume extraction
                                      matching_resume_items_info = []


                                      # Find the corresponding item(s) in the resume_extracted_with_sections
                                      if resume_extracted_with_sections: # Only search if resume extraction had results
                                           for resume_label, resume_items_list in resume_extracted_with_sections.items():
                                                if isinstance(resume_items_list, list): # Ensure items_list is a list
                                                     for item_info in resume_items_list: # item_info should be a dict {'text': '...', 'section': '...'}
                                                          # Ensure item_info is a dict and has the 'text' key
                                                          if isinstance(item_info, dict) and 'text' in item_info and item_info['text'].lower().strip() == jd_item_text: # Match on cleaned text
                                                               matching_resume_items_info.append(item_info) # Found a match, add its info
                                                else:
                                                     print(f"Warning: Unexpected items_list format for resume label '{resume_label}' during detailed match lookup: {resume_items_list}")


                                      # --- The print statement that caused the error was previously here ---
                                      # REMOVED: print(f"  - Matched item info from Resume: {matching_resume_items_info}") # <--- This line was removed


                                      if matching_resume_items_info: # Check if any matching item_info was found
                                          print(f"  -> Found matches in Resume details ({len(matching_resume_items_info)} instances).")
                                          # Apply section weights. Get the maximum section multiplier
                                          # from all the sections where this item was found in the resume.
                                          for item_info in matching_resume_items_info: # Iterate through all places it was found
                                               # Ensure item_info is a dict and has the 'sections' key, and 'sections' is a list
                                               if isinstance(item_info, dict) and 'sections' in item_info and isinstance(item_info['sections'], list):
                                                    for section_heading in item_info['sections']: # For each section it was listed in
                                                         # Use .get for safety, default multiplier is 1.0 if section not in config
                                                         # Use .get for safety when looking up section_weights
                                                         section_multiplier = self.section_weights.get(section_heading, self.section_weights.get("Unidentified", 1.0))
                                                         max_section_multiplier = max(max_section_multiplier, section_multiplier) # Keep track of the max
                                                         sections_where_matched.add(section_heading) # Collect unique sections it was in
                                               else:
                                                    print(f"Warning: Unexpected item_info format or missing/invalid 'sections' key during section processing: {item_info}. Applying Unidentified multiplier.")
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
                                          print(f"  -> Matched item '{jd_item_text_raw}' (Label: {jd_label}) matched with weight {achieved_item_weight_for_this_item} (Base: {base_item_weight}, Max Multiplier: {max_section_multiplier}). Sections: {list(sections_where_matched)}")

                                          cleaned_matched_items[jd_label].append({
                                              "text": jd_item_text_raw, # Store original JD text
                                              "matched_in_sections": list(sections_where_matched), # Convert set to list for output
                                              "achieved_weight": float(achieved_item_weight_for_this_item) # Store calculated weight
                                          })

                                      else:
                                           print(f"  -> Item '{jd_item_text_raw}' (Label: {jd_label}) found in flat set but no detailed match info found. Not added to matched items.")
                                           # Item was in the flat set, but we couldn't find its detailed info.
                                           # This shouldn't happen if extraction is consistent, but handle defensively.
                                           # It's found, so NOT added to missing items. It just doesn't contribute to score.


                                  else: # Item is missing!
                                      print(f"  -> Item '{jd_item_text_raw}' (Label: {jd_label}) NOT found in Resume flat set. Added to missing items.")
                                      # Only add to missing if it wasn't found at all
                                      # Append the raw JD text for the missing item
                                      cleaned_missing_items[jd_label].append(jd_item_text_raw)
                        else:
                             print(f"Error: Expected jd_items_list_raw for label '{jd_label}' to be a list but got {type(jd_items_list_raw)}. Cannot iterate items.")

                else:
                    print("Warning: No items extracted from JD. Cannot calculate skill match score.")


                print("Comparison complete for JD items.")
                print("-" * 25)


            except Exception as e:
                print(f"An error occurred during skill match calculation:")
                import traceback
                traceback.print_exc() # Print full traceback to the console
                skill_match_score = 0.0 # Set score to 0 on error
                # Matched/missing items might be partially populated, or empty depending on where error occurred
                # Keep whatever was populated for debugging, or clear if preferred.
                # Clearing for consistency on error:
                cleaned_matched_items = {} # Clear on error
                cleaned_missing_items = {} # Clear on error


        else:
             print("Skipping Prioritized Skill Match calculation as weight is 0 or dependencies are not functional/have no rules.")


        # --- 4. Calculate Final Scores ---
        print("\n--- Final Score Calculation ---")
        # Ensure total_possible_weighted_score is not zero before dividing
        if total_possible_weighted_score > 0:
             skill_match_score = achieved_weighted_score / total_possible_weighted_score
             print(f"Skill Match Raw Score: {achieved_weighted_score} / {total_possible_weighted_score} = {skill_match_score}")
        elif self.skill_match_weight > 0: # If skill weight is > 0 but total possible is 0, something is off
             print("Warning: Skill match weight > 0 but total possible weighted score is 0. Skill match score is 0.")
             skill_match_score = 0.0 # Ensure it's 0

        print(f"TF-IDF Score (weighted): {tfidf_score} * {self.tfidf_weight}")
        print(f"Skill Match Score (weighted): {skill_match_score} * {self.skill_match_weight}")

        combined_score = (tfidf_score * self.tfidf_weight) + (skill_match_score * self.skill_match_weight)
        print(f"Combined Score: {combined_score}")
        print("------------------------------")

        # --- 5. Prepare Results ---
        # Convert defaultdict to regular dict for jsonify
        final_matched_items = dict(cleaned_matched_items)
        final_missing_items = dict(cleaned_missing_items)

        # Filter out empty categories from matched and missing items for cleaner output
        final_matched_items_filtered = {k: v for k, v in final_matched_items.items() if v}
        final_missing_items_filtered = {k: v for k, v in final_missing_items.items() if v}


        return {
            "tfidf_score": float(tfidf_score),
            "prioritized_skill_score": float(skill_match_score),
            "combined_score": float(combined_score),
            "matched_items": final_matched_items_filtered,
            "missing_items": final_missing_items_filtered
        }


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Resume_Scorer.py directly for testing.")

    # Define configuration for the example usage (should match app.py or be consistent)
    example_model_name = 'en_core_web_sm'
    example_tfidf_weight = 0.3
    example_skill_weight = 0.7
    example_requirement_weights = {
        "EXAMPLE_TECH_SKILL": 1.0,
        "EXAMPLE_EXP_PHRASE": 1.2,
        "EXAMPLE_QUALIFICATION": 1.0,
        "CORE_SKILL": 1.0,
        "Unidentified": 0.1,
    }
    example_section_weights = {
         "Experience": 1.5,
         "Skills": 1.0,
         "Education": 0.8,
         "Unidentified": 0.5,
    }

    # Define simple example patterns consistent with the weights
    example_skill_patterns = [
         ("EXAMPLE_TECH_SKILL", [[{"LOWER": "python"}], [{"LOWER": "java"}], [{"LOWER": "flask"}]]),
         ("EXAMPLE_EXP_PHRASE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "years"}, {"LOWER": "of"}, {"LOWER": "experience"}]]),
         ("EXAMPLE_QUALIFICATION", [[{"LOWER": "bachelor's"}], [{"LOWER": "master's"}]]),
    ]
    example_core_phrases = ["Python", "Flask"]


    # Instantiate dependencies for example
    # Text Processor doesn't need model, but requires language
    example_text_processor = Text_Processor(language='english')

    # Skill Extractor needs model and patterns/phrases
    example_skill_extractor = Skill_Extractor(
        model_name=example_model_name,
        requirement_patterns=example_skill_patterns,
        core_skill_phrases=example_core_phrases
    )

    # Resume Parser needs model
    example_resume_parser = Resume_Parser(model_name=example_model_name)


    # Instantiate Resume_Scorer with dependencies and weights
    scorer = Resume_Scorer(
        text_processor=example_text_processor,
        skill_extractor=example_skill_extractor,
        resume_parser=example_resume_parser,
        tfidf_weight=example_tfidf_weight,
        skill_match_weight=example_skill_weight,
        requirement_weights=example_requirement_weights,
        section_weights=example_section_weights
    )

    # Check if the scorer instance is functional before running score calculation
    if not hasattr(scorer, '_functional') or not scorer._functional:
         print("\nSkipping score calculation example due to non-functional scorer.")
         # Exit or return if not functional
         sys.exit("Scorer not functional for example.")


    # Define example JD and Resume text
    example_jd_text = """
    We are looking for a Python Developer. Required skills include Python and Java.
    Must have 5+ years of experience. Bachelor's degree is required. Knowledge of Docker is a plus.
    """

    example_resume_text = """
    Summary: Experienced Developer with 6 years of experience.
    Skills: Python, Flask.
    Education: Bachelor's degree in Computer Science.
    Experience: Worked on Python and Java projects.
    """

    print("\n--- Running Example Score Calculation ---")
    # Calculate scores
    scores = scorer.calculate_scores(example_jd_text, example_resume_text)

    # Print results
    print("\n--- Example Results ---")
    print(f"TF-IDF Score: {scores['tfidf_score']:.2f}%")
    print(f"Prioritized Skill Match: {scores['prioritized_skill_score']:.2f}%")
    print(f"Combined Score: {scores['combined_score']:.2f}%")

    print("\nMatched Items:")
    if scores['matched_items']:
        for label, items in scores['matched_items'].items():
            print(f"- {label}:")
            for item_info in items:
                 # item_info is now a dict with 'text', 'matched_in_sections', 'achieved_weight'
                 print(f"  - Text: '{item_info['text']}', Matched in Sections: {item_info['matched_in_sections']}, Achieved Weight: {item_info['achieved_weight']:.2f}")
    else:
        print("No specific JD requirements matched in Resume.")

    print("\nMissing Items:")
    if scores['missing_items']:
        for label, items in scores['missing_items'].items():
            print(f"- {label}: {items}")
    else:
        print("All extracted JD items found in Resume.")
    print("-------------------------")