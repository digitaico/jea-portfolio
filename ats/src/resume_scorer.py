# Orchestrator
# Resume_Scorer.py

import sys
import os

# Import the newly created scoring components
# Use try-except blocks in case these files are not yet created or named correctly
try:
    from src.tfidf_scorer import TfidfScorer
except ImportError:
    print("FATAL ERROR: Could not import TfidfScorer in Resume_Scorer. Please check TfidfScorer.py.")
    class TfidfScorer: # Dummy class
         def __init__(self, text_processor): pass
         def calculate_similarity(self, text1, text2): return 0.0

try:
    from src.skill_comparer import SkillComparer
except ImportError:
    print("FATAL ERROR: Could not import SkillComparer in Resume_Scorer. Please check SkillComparer.py.")
    class SkillComparer: # Dummy class
         def __init__(self, skill_extractor, resume_parser, requirement_weights, section_weights): pass
         def compare_skills(self, job_description, resume_text): return 0.0, 0.0, {}, {}

try:
    from src.score_aggregator import ScoreAggregator
except ImportError:
    print("FATAL ERROR: Could not import ScoreAggregator in Resume_Scorer. Please check ScoreAggregator.py.")
    class ScoreAggregator: # Dummy class
         def __init__(self, tfidf_weight, skill_match_weight): pass
         def aggregate_and_format_scores(self, tfidf_raw_score, achieved_weighted_skill_score, total_possible_weighted_skill_score, matched_items, missing_items):
              return {"error": "Aggregator dependency not loaded."}

# Import original dependencies that Resume_Scorer still needs to pass along or use directly
# Use try-except blocks
try:
    from text_processor import TextProcessor
except ImportError:
    print("FATAL ERROR: Could not import Text_Processor in Resume_Scorer. Please check Text_Processor.py.")
    class Text_Processor: # Dummy class
         def __init__(self, language='english'): pass
         def process_text(self, text): return text.lower().strip() if isinstance(text, str) else ""
         language = 'unknown'

try:
    from skill_extractor import SkillExtractor
except ImportError:
    print("FATAL ERROR: Could not import Skill_Extractor in Resume_Scorer. Please check Skill_Extractor.py.")
    class Skill_Extractor: # Dummy class
         def __init__(self, model_name=None, requirement_patterns=None, core_skill_phrases=None):
              self.nlp = None
              self._functional = False
         def extract_requirements_and_skills(self, text, sections=None): return {}


try:
    from resume_parser import ResumeParser
except ImportError:
    print("FATAL ERROR: Could not import Resume_Parser in Resume_Scorer. Please check Resume_Parser.py.")
    class Resume_Parser: # Dummy class
         def __init__(self, model_name=None): self.nlp = None
         def parse_sections(self, text): return []


class ResumeScorer:
    """
    Orchestrates the resume scoring process by utilizing dedicated modules
    for TF-IDF calculation, skill comparison, and score aggregation.
    Initializes and holds instances of TfidfScorer, SkillComparer, and ScoreAggregator.
    Requires Text_Processor, Skill_Extractor, and Resume_Parser dependencies during initialization
    to pass to the specialized scoring modules.
    """
    def __init__(self, text_processor: Text_Processor, skill_extractor: Skill_Extractor, resume_parser: Resume_Parser,
                 tfidf_weight: float = 0.5, skill_match_weight: float = 0.5,
                 requirement_weights: dict = None, section_weights: dict = None):
        """
        Initializes the Resume_Scorer and its component scoring modules.

        Args:
            text_processor (Text_Processor): An instance of Text_Processor.
            skill_extractor (Skill_Extractor): An instance of Skill_Extractor.
            resume_parser (Resume_Parser): An instance of Resume_Parser.
            tfidf_weight (float): The weight for the TF-IDF similarity score (0.0 to 1.0).
            skill_match_weight (float): The weight for the prioritized skill match score (0.0 to 1.0).
            requirement_weights (dict, optional): Dictionary mapping skill labels to their base weights.
                                                  If None, uses defaults.
            section_weights (dict, optional): Dictionary mapping resume section headings to score multipliers.
                                              If None, uses defaults.
        """
        print("\n--- Resume_Scorer (Orchestrator) Initialization ---")
        # Store essential dependencies (passed to components)
        self.text_processor = text_processor
        self.skill_extractor = skill_extractor
        self.resume_parser = resume_parser

        # Store configuration weights (passed to components)
        self.tfidf_weight = tfidf_weight
        self.skill_match_weight = skill_match_weight
        # Define default weights if not provided (these are passed to SkillComparer and ScoreAggregator)
        self.requirement_weights = requirement_weights if requirement_weights is not None else self._define_default_requirement_weights()
        self.section_weights = section_weights if section_weights is not None else self._define_default_section_weights()


        # --- Instantiate Scoring Component Modules ---
        self.tfidf_scorer = None
        self.skill_comparer = None
        self.score_aggregator = None

        # Check if base dependencies are valid instances before instantiating scoring components
        is_base_deps_valid = isinstance(self.text_processor, Text_Processor) and \
                             isinstance(self.skill_extractor, Skill_Extractor) and \
                             isinstance(self.resume_parser, Resume_Parser)

        if is_base_deps_valid:
             try:
                 # Instantiate TfidfScorer
                 self.tfidf_scorer = TfidfScorer(text_processor=self.text_processor) # Pass Text_Processor

                 # Instantiate SkillComparer
                 self.skill_comparer = SkillComparer(
                     skill_extractor=self.skill_extractor, # Pass Skill_Extractor
                     resume_parser=self.resume_parser,     # Pass Resume_Parser
                     requirement_weights=self.requirement_weights, # Pass weights config
                     section_weights=self.section_weights        # Pass weights config
                 )

                 # Instantiate ScoreAggregator
                 self.score_aggregator = ScoreAggregator(
                     tfidf_weight=self.tfidf_weight,        # Pass weights config
                     skill_match_weight=self.skill_match_weight
                 )

                 # Check if component modules initialized successfully (they have their own _functional checks)
                 is_tfidf_functional = hasattr(self.tfidf_scorer, 'calculate_similarity') # Basic check for method existence
                 is_skill_functional = hasattr(self.skill_comparer, '_functional') and self.skill_comparer._functional
                 is_aggregator_functional = hasattr(self.score_aggregator, 'aggregate_and_format_scores') # Basic check for method existence


                 # Resume_Scorer is functional only if all component modules and base dependencies are functional
                 self._functional = is_base_deps_valid and is_tfidf_functional and is_skill_functional and is_aggregator_functional

                 if self._functional:
                      print("Resume_Scorer (Orchestrator) and scoring components initialized successfully.")
                      # Report functional status of components
                      print(f"Component Status: TfidfScorer Functional={is_tfidf_functional}, SkillComparer Functional={is_skill_functional}, ScoreAggregator Functional={is_aggregator_functional}")
                 else:
                      print("Warning: Resume_Scorer (Orchestrator) initialized but one or more scoring components are not fully functional.")
                      print(f"Component Status: TfidfScorer Functional={is_tfidf_functional}, SkillComparer Functional={is_skill_functional}, ScoreAggregator Functional={is_aggregator_functional}")
                      # If not functional, set weights to 0 to ensure 0 scores are returned
                      self.tfidf_weight = 0.0
                      self.skill_match_weight = 0.0


             except Exception as e:
                  print(f"Error during Resume_Scorer component initialization: {e}")
                  import traceback
                  traceback.print_exc()
                  self._functional = False
                  print("Resume_Scorer (Orchestrator) initialized but is NOT functional due to component initialization errors.")
                  # Set weights to 0 if components fail to initialize
                  self.tfidf_weight = 0.0
                  self.skill_match_weight = 0.0

        else:
             print("Fatal Error: Resume_Scorer (Orchestrator) could not initialize due to invalid base dependencies (Text_Processor, Skill_Extractor, or Resume_Parser).")
             print("Please check the imports and initialization of these base dependencies in app.py.")
             self._functional = False
             # Set weights to 0 if base dependencies are invalid
             self.tfidf_weight = 0.0
             self.skill_match_weight = 0.0


        print("------------------------------------------------")


    def _define_default_requirement_weights(self):
        """Defines default base weights for different requirement categories."""
        # Default weights if none are provided
        # Align keys with Skill_Extractor pattern labels and 'CORE_SKILL' phrase label
        return {
            "REQUIRED_SKILL_PHRASE": 1.5,
            "YEARS_EXPERIENCE": 1.2,
            "QUALIFICATION_DEGREE": 1.0,
            "KNOWLEDGE_OF": 0.8,
            "CORE_SKILL": 1.0, # Default weight for core skills matched by PhraseMatcher
            "Unidentified": 0.2, # Default weight for items matched by general patterns or in unidentified sections
            # Add weights for any other custom pattern labels you add in Skill_Extractor
        }

    def _define_default_section_weights(self):
        """Defines default score multipliers for different resume sections."""
        # Default multipliers if none are provided
        # Align keys with potential section headings from Resume_Parser
        # Use lower() or normalized forms in keys if Resume_Parser outputs variations
        return {
             "Experience": 1.5,
             "Work Experience": 1.5, # Also map variations
             "Employment History": 1.5, # Also map variations
             "Skills": 1.0,     # Items in Skills get base multiplier
             "Technical Skills": 1.0, # Also map variations
             "Professional Skills": 1.0, # Also map variations
             "Education": 0.8,  # Items in Education get 20% less multiplier
             "Projects": 1.1,   # Small bonus for items in Projects
             "Summary": 0.9,    # Slightly lower
             "About": 0.9,      # Also map variations
             "Profile": 0.9,    # Also map variations
             "Languages": 1.0,  # Languages section
             "Awards": 0.7,     # Example for other sections
             "Certifications": 1.1, # Example for other sections
             "Licenses": 1.1,   # Example for other sections
             "Publications": 0.6, # Example for other sections
             "Presentations": 0.6, # Example for other sections
             "Volunteer Experience": 0.7, # Example for other sections
             "Interests": 0.3,  # Example for other sections
             "References": 0.1, # Items in References are usually low value
             "Contact": 0.1,    # Items in Contact are usually low value
             "Objective": 0.9,
             "Unidentified (Header)": 0.5, # Low multiplier for items before first heading
             "Unidentified (Footer)": 0.5, # Low multiplier for items after last heading
             "Unidentified (Full Document)": 0.5, # Low multiplier if no sections found
             "Unidentified": 0.5, # Fallback if section is labeled "Unidentified" by parser/extractor or not in list
        }


    def calculate_scores(self, job_description: str, resume_text: str) -> dict:
        """
        Orchestrates the scoring process by calling methods on the component modules.

        Args:
            job_description (str): The raw text of the job description.
            resume_text (str): The raw text of the resume.

        Returns:
            dict: The final results dictionary from ScoreAggregator, or an error dictionary
                  if the Resume_Scorer or its components are not functional.
        """
        # Ensure the Resume_Scorer instance and its components are functional
        if not hasattr(self, '_functional') or not self._functional:
             print("Error: Resume_Scorer (Orchestrator) instance is not functional. Cannot calculate scores. Check initialization logs.")
             return {
                "tfidf_score": 0.0,
                "prioritized_skill_score": 0.0,
                "weighted_tfidf_score": 0.0,
                "weighted_prioritized_skill_score": 0.0,
                "combined_score": 0.0,
                "matched_items": {},
                "missing_items": {},
                "error": "Scoring orchestrator not functional."
             }

        # --- 1. Text Processing ---
        # Text processing is still handled by Text_Processor, called directly here or within TfidfScorer/SkillComparer if they need processed text
        # TfidfScorer and SkillComparer.compare_skills *should* receive raw text and handle processing internally as needed.
        # Let's adjust: The external modules should handle their own text processing via the passed Text_Processor instance.

        # --- 2. TF-IDF Similarity Score ---
        # Check if the tfidf_scorer component is functional before using
        if self.tfidf_scorer and hasattr(self.tfidf_scorer, 'calculate_similarity'):
             print("Calling TfidfScorer.calculate_similarity...")
             tfidf_raw_score = self.tfidf_scorer.calculate_similarity(job_description, resume_text) # Pass raw texts
             print(f"Received TF-IDF raw score: {tfidf_raw_score:.4f}")
        else:
             print("Warning: TfidfScorer component is not functional. TF-IDF score will be 0.")
             tfidf_raw_score = 0.0 # Default to 0 if component is not ready


        # --- 3. Prioritized Skill Match Score ---
        # Check if the skill_comparer component is functional before using
        if self.skill_comparer and hasattr(self.skill_comparer, 'compare_skills') and hasattr(self.skill_comparer, '_functional') and self.skill_comparer._functional:
             print("Calling SkillComparer.compare_skills...")
             # Pass raw texts; SkillComparer handles parsing and extraction internally
             achieved_weighted_skill_score, total_possible_weighted_skill_score, matched_items, missing_items = self.skill_comparer.compare_skills(job_description, resume_text)
             print(f"Received skill comparison results: Achieved={achieved_weighted_skill_score:.4f}, Possible={total_possible_weighted_skill_score:.4f}, Matched={len(matched_items)}, Missing={len(missing_items)}")
        else:
             print("Warning: SkillComparer component is not functional. Skill match score will be 0.")
             achieved_weighted_skill_score = 0.0
             total_possible_weighted_skill_score = 0.0
             matched_items = {}
             missing_items = {}


        # --- 4. Aggregate and Format Scores ---
        # Check if the score_aggregator component is functional before using
        if self.score_aggregator and hasattr(self.score_aggregator, 'aggregate_and_format_scores'):
             print("Calling ScoreAggregator.aggregate_and_format_scores...")
             # Pass the raw TF-IDF score and the results from skill comparison
             final_results = self.score_aggregator.aggregate_and_format_scores(
                 tfidf_raw_score, achieved_weighted_skill_score, total_possible_weighted_skill_score, matched_items, missing_items
             )
             print("Score aggregation and formatting complete.")
        else:
             print("Warning: ScoreAggregator component is not functional. Cannot finalize scores.")
             # Return basic info if aggregator failed
             final_results = {
                "tfidf_score": float(tfidf_raw_score),
                "prioritized_skill_score": achieved_weighted_skill_score / total_possible_weighted_skill_score if total_possible_weighted_skill_score > 0 else 0.0,
                "weighted_tfidf_score": float(tfidf_raw_score * self.tfidf_weight), # Best guess at weighted score if aggregator failed
                "weighted_prioritized_skill_score": float(achieved_weighted_skill_score * self.skill_match_weight / total_possible_weighted_skill_score if total_possible_weighted_skill_score > 0 else 0.0), # Best guess
                "combined_score": 0.0, # Cannot confidently calculate combined if aggregator failed
                "matched_items": matched_items,
                "missing_items": missing_items,
                "error": "Score aggregator component not functional. Scores may be incomplete."
             }


        # --- 5. Return Final Results ---
        return final_results


    # --- Define default weights for SkillComparer and ScoreAggregator ---
    # These methods define the default structure if no weights dicts are passed to __init__
    # They are called during Resume_Scorer.__init__ and the results are passed to component inits.
    def _define_default_requirement_weights(self):
        """Defines default base weights for different requirement categories."""
        # Default weights if none are provided
        # Align keys with Skill_Extractor pattern labels and 'CORE_SKILL' phrase label
        return {
            "REQUIRED_SKILL_PHRASE": 1.5,
            "YEARS_EXPERIENCE": 1.2,
            "QUALIFICATION_DEGREE": 1.0,
            "KNOWLEDGE_OF": 0.8,
            "CORE_SKILL": 1.0, # Default weight for core skills matched by PhraseMatcher
            "Unidentified": 0.2, # Default weight for items matched by general patterns or in unidentified sections
            # Add weights for any other custom pattern labels you add in Skill_Extractor
        }

    def _define_default_section_weights(self):
        """Defines default score multipliers for different resume sections."""
        # Default multipliers if none are provided
        # Align keys with potential section headings from Resume_Parser
        # Use lower() or normalized forms in keys if Resume_Parser outputs variations
        return {
             "Experience": 1.5,
             "Work Experience": 1.5, # Also map variations
             "Employment History": 1.5, # Also map variations
             "Skills": 1.0,     # Items in Skills get base multiplier
             "Technical Skills": 1.0, # Also map variations
             "Professional Skills": 1.0, # Also map variations
             "Education": 0.8,  # Items in Education get 20% less multiplier
             "Projects": 1.1,   # Small bonus for items in Projects
             "Summary": 0.9,    # Slightly lower
             "About": 0.9,      # Also map variations
             "Profile": 0.9,    # Also map variations
             "Languages": 1.0,  # Languages section
             "Awards": 0.7,     # Example for other sections
             "Certifications": 1.1, # Example for other sections
             "Licenses": 1.1,   # Example for other sections
             "Publications": 0.6, # Example for other sections
             "Presentations": 0.6, # Example for other sections
             "Volunteer Experience": 0.7, # Example for other sections
             "Interests": 0.3,  # Example for other sections
             "References": 0.1, # Items in References are usually low value
             "Contact": 0.1,    # Items in Contact are usually low value
             "Objective": 0.9,
             "Unidentified (Header)": 0.5, # Low multiplier for items before first heading
             "Unidentified (Footer)": 0.5, # Low multiplier for items after last heading
             "Unidentified (Full Document)": 0.5, # Low multiplier if no sections found
             "Unidentified": 0.5, # Fallback if section is labeled "Unidentified" by parser/extractor or not in list
        }


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Resume_Scorer.py (Orchestrator) directly for testing.")

    # Define configuration for the example usage (should match app.py or be consistent)
    example_model_name = 'en_core_web_sm' # Use sm for faster testing
    example_tfidf_weight = 0.3
    example_skill_weight = 0.7

    # Define weights for passing to the orchestrator (these will be passed to components)
    example_requirement_weights = {
        "REQUIRED_SKILL_PHRASE": 1.5,
        "YEARS_EXPERIENCE": 1.2,
        "QUALIFICATION_DEGREE": 1.0,
        "KNOWLEDGE_OF": 0.8,
        "CORE_SKILL": 1.0,
        "Unidentified": 0.2,
        "EXAMPLE_TECH_SKILL": 1.0,
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

    # Define example patterns and phrases for Skill_Extractor dependency
    example_skill_patterns = [
         ("REQUIRED_SKILL_PHRASE", [[{"LOWER": "required"}, {"LOWER": "skill"}], [{"LOWER": "must"}, {"LOWER": "have"}]]),
         ("EXAMPLE_TECH_SKILL", [[{"LOWER": "python"}], [{"LOWER": "java"}], [{"LOWER": "flask"}]]),
         ("YEARS_EXPERIENCE", [[{"POS": "NUM", "OP": "+"}, {"LOWER": "years"}, {"LOWER": "of", "OP": "?"}, {"LOWER": "experience"}]]),
         ("QUALIFICATION_DEGREE", [[{"LOWER": {"IN": ["bachelor's", "master's"]}}, {"LOWER": "degree"}]]),
    ]
    example_core_phrases = ["Python", "Flask", "SQL", "Java", "Docker", "Git", "AWS"]


    # --- Instantiate Base Dependencies for Example ---
    print("\n--- Initializing Base Dependencies for Resume_Scorer Example ---")
    # Text Processor needs language
    example_text_processor = Text_Processor(language='english')

    # Skill Extractor needs model and patterns/phrases config
    # Pass the example patterns and core phrases
    example_skill_extractor = Skill_Extractor(
        model_name=example_model_name,
        requirement_patterns=example_skill_patterns,
        core_skill_phrases=example_core_phrases
    )

    # Resume Parser needs model
    example_resume_parser = Resume_Parser(model_name=example_model_name)
    print("---------------------------------------------------------------")


    # Instantiate the Resume_Scorer Orchestrator
    scorer_orchestrator = ResumeScorer(
        text_processor=example_text_processor, # Pass base dependency
        skill_extractor=example_skill_extractor, # Pass base dependency
        resume_parser=example_resume_parser, # Pass base dependency
        tfidf_weight=example_tfidf_weight, # Pass weights config
        skill_match_weight=example_skill_weight,
        requirement_weights=example_requirement_weights, # Pass weights config
        section_weights=example_section_weights      # Pass weights config
    )

    # Check if the orchestrator instance is functional before running score calculation
    if not hasattr(scorer_orchestrator, '_functional') or not scorer_orchestrator._functional:
         print("\nSkipping score calculation example due to non-functional Resume_Scorer orchestrator.")
         sys.exit("Resume_Scorer orchestrator not functional for example.")


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

    print("\n--- Running Example Score Calculation via Orchestrator ---")
    # Calculate scores using the orchestrator
    scores = scorer_orchestrator.calculate_scores(example_jd_text, example_resume_text)

    # Print results
    print("\n--- Example Results from Orchestrator ---")
    import json
    # Use .get with default 0.0 or {} for safety when printing
    print(f"TF-IDF Raw Score: {scores.get('tfidf_score', 0.0):.4f}")
    print(f"Prioritized Skill Match (Raw): {scores.get('prioritized_skill_score', 0.0):.4f}")
    print(f"TF-IDF Score (Weighted): {scores.get('weighted_tfidf_score', 0.0):.4f}")
    print(f"Prioritized Skill Match (Weighted): {scores.get('weighted_prioritized_skill_score', 0.0):.4f}")
    print(f"Combined Score: {scores.get('combined_score', 0.0):.4f}")

    print("\nMatched Items:")
    matched = scores.get('matched_items', {})
    if matched:
        for label, items in matched.items():
            print(f"- {label}:")
            if isinstance(items, list):
                 for item_info in items:
                      # Use .get for safety in case keys are missing (shouldn't be with current code)
                      print(f"  - Text: '{item_info.get('text', 'N/A')}', Sections: {item_info.get('matched_in_sections', ['N/A'])}, Weight: {item_info.get('achieved_weight', 0.0):.4f}")
            else:
                 print(f"  Warning: Expected list for label '{label}' in matched items, but got {type(items)}.")

    else:
        print("No specific JD requirements matched in Resume.")

    print("\nMissing Items:")
    missing = scores.get('missing_items', {})
    if missing:
        for label, items in missing.items():
            # Items in missing_items are just strings
            if isinstance(items, list):
                 print(f"- {label}: {items}")
            else:
                 print(f"  Warning: Expected list of items for label '{label}' in missing items, but got {type(items)}.")
    else:
        print("All extracted JD items found in Resume.")

    # Print any error message returned
    if "error" in scores:
         print(f"\nAPI returned an error: {scores['error']}")

    print("-----------------------------------------")