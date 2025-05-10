# src/SkillComparer.py (no significant changes needed if __init__ already accepted args)

from collections import defaultdict
import re
import sys

# Import config for weights and multipliers
# No need to import Skill_Extractor or Resume_Parser if they are passed in __init__

# Assume Skill_Extractor and Resume_Parser classes are defined elsewhere and imported
# If you have dummy classes for standalone testing, keep them or adjust imports.
# For the main app functionality, they are passed into the constructor.

class SkillComparer:
    """
    Compares extracted skills/requirements from Job Description and Resume.
    Applies section-based weighting to resume items.
    Includes debug prints.
    """
    # Accept weights and multipliers loaded from config via app.py
    def __init__(self, skill_extractor, resume_parser, requirement_weights: dict, section_weights: dict):
        """
        Initializes SkillComparer with Skill_Extractor, Resume_Parser, and weights/multipliers.

        Args:
            skill_extractor: An instance of Skill_Extractor.
            resume_parser: An instance of Resume_Parser.
            requirement_weights (dict): Dictionary of base weights for requirement labels.
                                        Loaded from config.
            section_weights (dict): Dictionary of multipliers for resume sections.
                                    Loaded from config.
        """
        print("\n--- SkillComparer Initialized ---") # DEBUG PRINT
        self.skill_extractor = skill_extractor # Keep reference to the extractor
        self.resume_parser = resume_parser   # Keep reference to the parser
        self.requirement_weights = requirement_weights # Use weights from config
        self.section_weights = section_weights       # Use multipliers from config
        self._functional = True # Assuming functional if initialized with dependencies

        if self.skill_extractor is None or self.resume_parser is None or not isinstance(self.requirement_weights, dict) or not isinstance(self.section_weights, dict):
             print("Error: SkillComparer initialized with invalid or missing dependencies/configs.")
             self._functional = False

        # Print loaded weights and multipliers for verification (optional)
        # print("SkillComparer DEBUG: Loaded Requirement Weights:", self.requirement_weights)
        # print("SkillComparer DEBUG: Loaded Section Multipliers:", self.section_weights)

        print("---------------------------------") # DEBUG PRINT


    def get_section_multiplier(self, section_name: str) -> float:
        """
        Gets the multiplier for a given section name. Defaults to 'Unidentified' weight.
        Handles case-insensitivity and stripping whitespace for lookup.
        """
        cleaned_section_name = section_name.strip() # Clean whitespace

        # Use the defaultdict from config.py which handles missing keys and provides default
        # We just need to ensure the key used for lookup is the cleaned section name.
        return self.section_weights.get(cleaned_section_name, self.section_weights['Unidentified']) # Use .get with fallback or rely on defaultdict


    # compare_skills method remains the same, as it already uses self.requirement_weights and self.section_weights via get_section_multiplier
    def compare_skills(self, job_description: str, resume_text: str) -> tuple:
        """
        Compares extracted skills between JD and Resume, applying section weighting.
        Returns calculated scores and lists of matched/missing items.
        """
        if not self._functional:
             print("Error: SkillComparer is not functional. Cannot compare skills.")
             return 0.0, 0.0, [], []


        print("\n--- Running Skill Extraction and Comparison ---") # DEBUG PRINT

        # --- Step 1: Extract skills from Job Description ---
        # JD is processed as a single block (no sections needed from parser)
        print("\nRunning Skill_Extractor on JD...") # DEBUG PRINT
        # The Skill_Extractor method needs to correctly handle sections=None for JD
        jd_extracted_items = self.skill_extractor.extract_requirements_and_skills(text=job_description, sections=None)
        print("SkillComparer DEBUG: Extracted JD items:", jd_extracted_items) # DEBUG PRINT
        print("------------------------------") # DEBUG PRINT


        # --- Step 2: Parse Resume into Sections ---
        print("\nRunning Resume_Parser on Resume...") # DEBUG PRINT
        # This calls the method that finds headings and divides content
        resume_sections = self.resume_parser.parse_sections(resume_text)
        print("SkillComparer DEBUG: Resume sections parsed (count):", len(resume_sections)) # DEBUG PRINT
        print("------------------------------") # DEBUG PRINT


        # --- Step 3: Extract skills from Resume (section by section) ---
        # Pass the parsed sections to the Skill_Extractor
        print("\nRunning Skill_Extractor on Resume...") # DEBUG PRINT
        # The Skill_Extractor method needs to correctly handle sections=list for Resume
        resume_extracted_items = self.skill_extractor.extract_requirements_and_skills(text=resume_text, sections=resume_sections)
        print("SkillComparer DEBUG: Extracted Resume items (with sections):", resume_extracted_items) # DEBUG PRINT
        print("------------------------------") # DEBUG PRINT


        # --- Step 4: Prepare Resume items for efficient lookup ---
        # Create a set of cleaned resume item texts for fast checking if a JD item exists in the resume
        # Also, store the detailed resume items (with sections) in a way that's easy to look up by cleaned text
        print("\nFlattening Resume extracted items for lookup...") # DEBUG PRINT
        flattened_resume_texts = set()
        # Use a dict to store detailed resume items, keyed by cleaned text, grouping sections
        detailed_resume_lookup = defaultdict(lambda: defaultdict(list)) # {label: {cleaned_text: [{'text': raw, 'sections': [...]}, ...]}} # Or simpler: {label: {cleaned_text: list of raw item dicts}}

        if isinstance(resume_extracted_items, dict):
             for label, items_list in resume_extracted_items.items():
                  if isinstance(items_list, list):
                       for item_data in items_list:
                            # Resume items are expected to be dicts with 'text' and 'sections'
                            if isinstance(item_data, dict) and 'text' in item_data and 'sections' in item_data:
                                 item_text_raw = item_data.get('text', '')
                                 item_sections = item_data.get('sections', ['Unidentified']) # Ensure it's a list, default to Unidentified
                                 cleaned_text = item_text_raw.lower().strip()

                                 if cleaned_text:
                                      flattened_resume_texts.add(cleaned_text) # Add to set for quick lookup
                                      # Store the detailed item info keyed by cleaned text and label
                                      # We need the original text and all sections for weighting
                                      detailed_resume_lookup[label][cleaned_text].append({'text': item_text_raw, 'sections': item_sections})
                            # else: # This warning is handled inside Skill_Extractor now
                            #      print(f"Warning: Expected resume item to be dict with 'text' and 'sections', but got {type(item_data)}. Skipping.")
                  else:
                       print(f"Warning: Expected list of items for label '{label}' in resume_extracted_items, but got {type(items_list)}. Cannot process.")


        print(f"Flattened Resume Extracted Items (Text Only Set) created with {len(flattened_resume_texts)} unique items.") # DEBUG PRINT
        # print(f"Detailed Resume Lookup (partial): {dict(list(detailed_resume_lookup.items())[:3])}...") # DEBUG PRINT (Can be verbose)
        print("------------------------------") # DEBUG PRINT
        print("SkillComparer DEBUG: Flattened Resume Items (Text Only Set):", flattened_resume_texts) # DEBUG PRINT


        # --- Step 5: Compare and Score ---
        print("\nComparing JD extracted items to Resume extracted items for scoring...") # DEBUG PRINT

        total_possible_weighted_score = 0.0
        achieved_weighted_score = 0.0
        matched_items = defaultdict(list) # Store matched items {label: [item_dict]}
        missing_items = defaultdict(list) # Store missing items {label: [item_text]}

        # Iterate through items extracted from the Job Description
        if isinstance(jd_extracted_items, dict):
             for label, items_list in jd_extracted_items.items():
                  if isinstance(items_list, list):
                       # JD items are expected to be just strings (cleaned text)
                       for item_text_cleaned in items_list:
                            if isinstance(item_text_cleaned, str):
                                 # Get the base weight for this label from config, default to 'Unidentified' if label not found
                                 base_weight = self.requirement_weights.get(label, self.requirement_weights['Unidentified'])
                                 # print(f"SkillComparer DEBUG: Checking JD item '{item_text_cleaned}' (Label: {label}, Cleaned: '{item_text_cleaned}')...") # DEBUG PRINT

                                 # Add the base weight to the total possible score
                                 total_possible_weighted_score += base_weight
                                 # print(f"SkillComparer DEBUG:   - Added base weight {base_weight:.2f} to total possible score. Total Possible: {total_possible_weighted_score:.2f}") # DEBUG PRINT


                                 # Check if the cleaned JD item text exists in the flattened resume texts set
                                 if item_text_cleaned in flattened_resume_texts:
                                      # print(f"SkillComparer DEBUG:   -> Found '{item_text_cleaned}' in flattened Resume set.") # DEBUG PRINT

                                      # Find the detailed match(es) in the resume lookup by label and cleaned text
                                      # A skill might be found in multiple sections of the resume, resulting in multiple detailed entries.
                                      detailed_matches_in_resume = detailed_resume_lookup.get(label, {}).get(item_text_cleaned, [])

                                      if detailed_matches_in_resume:
                                           # print(f"SkillComparer DEBUG:   -> Detailed matches found in Resume for '{item_text_cleaned}': {detailed_matches_in_resume}") # DEBUG PRINT
                                           # Apply section weighting: Find the maximum multiplier across all sections where the skill was found
                                           max_section_multiplier = 0.0
                                           sections_found = []
                                           # print(f"SkillComparer DEBUG:     -> Applying section weights for '{item_text_cleaned}'...") # DEBUG PRINT
                                           for detailed_match in detailed_matches_in_resume:
                                                # detailed_match is a dict like {'text': raw_text, 'sections': list_of_sections}
                                                sections_list = detailed_match.get('sections', ['Unidentified'])
                                                for section_name in sections_list:
                                                     multiplier = self.get_section_multiplier(section_name) # Get multiplier for each section
                                                     # print(f"SkillComparer DEBUG:       Section '{section_name}' has multiplier {multiplier:.2f}.") # DEBUG PRINT
                                                     max_section_multiplier = max(max_section_multiplier, multiplier) # Keep the maximum
                                                     if section_name not in sections_found:
                                                         sections_found.append(section_name) # Collect all unique sections found


                                           # Calculate the achieved weight for this matched item
                                           achieved_item_weight = base_weight * max_section_multiplier
                                           achieved_weighted_score += achieved_item_weight
                                           # print(f"SkillComparer DEBUG:     -> Matched item '{item_text_cleaned}' (Label: {label}) matched with weight {achieved_item_weight:.4f} (Base: {base_weight:.2f}, Max Multiplier: {max_section_multiplier:.2f}). Sections: {sections_found}") # DEBUG PRINT
                                           # print(f"SkillComparer DEBUG:     -> Total achieved_weighted_score is now {achieved_weighted_score:.4f}") # DEBUG PRINT

                                           # Add the matched item to the matched_items list
                                           matched_items[label].append({
                                                'text': item_text_cleaned, # Store the cleaned text
                                                'matched_in_sections': sections_found, # Store the list of unique sections where found
                                                'achieved_weight': achieved_item_weight
                                           })
                                      else:
                                           # This case should ideally not happen if item_text_cleaned was in flattened_resume_texts
                                           # but the detailed lookup failed. Treat as missing for safety.
                                           print(f"Warning: '{item_text_cleaned}' found in flattened set but detailed lookup failed. Treating as missing.") # DEBUG PRINT
                                           missing_items[label].append(item_text_cleaned) # Add to missing

                                 else:
                                      # If not found in the resume, it's a missing item
                                      # print(f"SkillComparer DEBUG:   -> '{item_text_cleaned}' NOT found in flattened Resume set.") # DEBUG PRINT
                                      missing_items[label].append(item_text_cleaned) # Add to missing
                                      # print(f"SkillComparer DEBUG:     -> Added to missing_items: '{item_text_cleaned}' (Label: {label})") # DEBUG PRINT

                            else:
                                 print(f"Warning: Expected string item for label '{label}' in jd_extracted_items, but got {type(item_text_cleaned)}. Skipping comparison for this item.") # DEBUG PRINT

                  else:
                       print(f"Warning: Expected list of items for label '{label}' in jd_extracted_items, but got {type(items_list)}. Cannot compare.")


        # Ensure we don't divide by zero if no items were expected in the JD
        skill_match_raw_score = achieved_weighted_score / total_possible_weighted_score if total_possible_weighted_score > 0 else 0.0

        print("-------------------------") # DEBUG PRINT
        print(f"Comparison complete for JD items. Achieved Weighted Score: {achieved_weighted_score:.4f}, Total Possible Weighted Score: {total_possible_weighted_score:.4f}") # DEBUG PRINT
        print(f"Skill Match Raw Score: {skill_match_raw_score:.4f}") # DEBUG PRINT
        print("SkillComparer DEBUG: Final Matched Items Before Return:", dict(matched_items)) # DEBUG PRINT (Convert defaultdict to dict)
        print("SkillComparer DEBUG: Final Missing Items Before Return:", dict(missing_items)) # DEBUG PRINT (Convert defaultdict to dict)
        print("----------------------------------------") # DEBUG PRINT


        # Convert defaultdicts to dict for the return value
        return skill_match_raw_score, total_possible_weighted_score, dict(matched_items), dict(missing_items)


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running SkillComparer.py directly for testing.")

    # Import config for the example usage
    from .config import (
        get_spacy_model_name,
        get_requirement_weights,
        get_section_multipliers,
        get_requirement_patterns,
        get_core_skill_phrases
    )

    # Dummy Skill_Extractor and Resume_Parser instances for example
    # In the real app, these would be the fully initialized instances
    class DummySkillExtractorForComparer:
        def __init__(self, req_patterns, core_phrases):
             self._req_patterns = req_patterns
             self._core_phrases = core_phrases
             self._functional = True # Assume functional for example

        def extract_requirements_and_skills(self, text: str, sections: list | None = None) -> dict:
            print(f"\n--- DummySkillExtractor extracting from text (length {len(text)}) ---")
            print(f"  Sections provided: {sections is not None}")
            extracted = defaultdict(list)

            # Simulate extraction based on simple text checks for the example
            if sections is None: # Simulate JD extraction
                 print("  Simulating JD extraction...")
                 if "required skill Python" in text: extracted["REQUIRED_SKILL_PHRASE"].append("required skill Python")
                 if "5 years of experience" in text: extracted["YEARS_EXPERIENCE"].append("5 years of experience")
                 if "knowledge of Docker" in text: extracted["KNOWLEDGE_OF"].append("knowledge of Docker")
                 if "Python" in text: extracted["CORE_SKILL"].append("Python")
                 if "Docker" in text: extracted["CORE_SKILL"].append("Docker")
                 if "AWS" in text: extracted["CORE_SKILL"].append("AWS")
                 if "Git" in text: extracted["CORE_SKILL"].append("Git")
                 if "RESTful APIs" in text: extracted["CORE_SKILL"].append("RESTful APIs")
                 # Simulate cleaning/deduplication
                 cleaned_extracted = defaultdict(list)
                 for label, items in extracted.items():
                      seen = set()
                      for item in items:
                           cleaned_item = item.lower().strip()
                           if cleaned_item not in seen:
                                cleaned_extracted[label].append(cleaned_item)
                                seen.add(cleaned_item)
                 print("  Simulated JD extracted (cleaned):", dict(cleaned_extracted))
                 print("------------------------------------------------")
                 return dict(cleaned_extracted)

            else: # Simulate Resume extraction section by section
                 print("  Simulating Resume extraction section by section...")
                 grouped_resume_items = defaultdict(lambda: defaultdict(lambda: {'text': None, 'sections': set()}))

                 for section_data in sections:
                      if isinstance(section_data, dict) and 'heading' in section_data and 'content' in section_data:
                           heading = section_data['heading']
                           content = section_data['content']
                           print(f"    Processing section: '{heading}'")
                           # Simulate finding skills/items in section content
                           if "Python" in content:
                                cleaned = "python"
                                if cleaned not in grouped_resume_items["CORE_SKILL"]:
                                    grouped_resume_items["CORE_SKILL"][cleaned]['text'] = "Python" # Store raw text
                                grouped_resume_items["CORE_SKILL"][cleaned]['sections'].add(heading)
                           if "SQL" in content:
                                cleaned = "sql"
                                if cleaned not in grouped_resume_items["CORE_SKILL"]:
                                    grouped_resume_items["CORE_SKILL"][cleaned]['text'] = "SQL" # Store raw text
                                grouped_resume_items["CORE_SKILL"][cleaned]['sections'].add(heading)
                           if "Docker" in content:
                                cleaned = "docker"
                                if cleaned not in grouped_resume_items["CORE_SKILL"]:
                                     grouped_resume_items["CORE_SKILL"][cleaned]['text'] = "Docker" # Store raw text
                                grouped_resume_items["CORE_SKILL"][cleaned]['sections'].add(heading)
                           if "AWS Certified" in content: # Simulate a certification match
                                cleaned = "aws certified developer"
                                if cleaned not in grouped_resume_items["CORE_SKILL"]:
                                     grouped_resume_items["CORE_SKILL"][cleaned]['text'] = "AWS Certified Developer"
                                grouped_resume_items["CORE_SKILL"][cleaned]['sections'].add(heading) # Should add to CERTIFICATIONS section

                 # Convert grouped structure to final format
                 final_extracted = defaultdict(list)
                 for label, cleaned_text_data_dict in grouped_resume_items.items():
                      for cleaned_text, data in cleaned_text_data_dict.items():
                            final_extracted[label].append({
                                 'text': data['text'] if data['text'] is not None else cleaned_text,
                                 'sections': list(data['sections'])
                            })
                 print("  Simulated Resume extracted (with sections):", dict(final_extracted))
                 print("------------------------------------------------")
                 return dict(final_extracted)


    class DummyResumeParserForComparer:
         def __init__(self):
             self._functional = True # Assume functional for example

         def parse_sections(self, text):
              # Simulate parsing sections based on simple text markers for example
              print("\n--- DummyResumeParser parsing sections ---")
              sections = []
              # Simple split logic for example
              parts = text.split("###") # Use a clear marker for example
              current_pos = 0
              for i, part in enumerate(parts):
                   heading = f"Section {i+1}" if i > 0 else "Unidentified (Header)"
                   content = part.strip()
                   if content:
                        sections.append({'heading': heading, 'content': content})
                        print(f"  Simulated Section: '{heading}' (Content Length: {len(content)})")
              if not sections and text.strip(): # Handle case with no markers
                   sections.append({'heading': 'Unidentified (Full Document)', 'content': text.strip()})
                   print("  Simulated Section: 'Unidentified (Full Document)' (Content Length: {len(text.strip())})")

              print("--- DummyResumeParser finished parsing ---")
              return sections


    # Instantiate dummy dependencies
    dummy_skill_extractor = DummySkillExtractorForComparer(
         req_patterns=get_requirement_patterns(), # Pass config patterns to dummy
         core_phrases=get_core_skill_phrases()   # Pass config phrases to dummy
    )
    dummy_resume_parser = DummyResumeParserForComparer()

    # Instantiate SkillComparer using dummy dependencies and config weights
    skill_comparer_instance = SkillComparer(
        skill_extractor=dummy_skill_extractor,
        resume_parser=dummy_resume_parser,
        requirement_weights=get_requirement_weights(), # Use config weights
        section_weights=get_section_multipliers() # Use config multipliers
    )

    if not hasattr(skill_comparer_instance, '_functional') or not skill_comparer_instance._functional:
         print("\nSkipping comparison example due to non-functional SkillComparer.")
         sys.exit("SkillComparer not functional for example.")


    # Example JD and Resume text
    example_jd_text = """
    We need a developer with required skill Python.
    Must have 5 years of experience. Knowledge of Docker is essential.
    Proficiency in AWS and Git is a plus. Experience with RESTful APIs.
    """

    # Example Resume text with sections simulated by markers
    example_resume_text = """
    SUMMARY
    Experienced Python developer. Worked with Docker.
    ###SKILLS###
    Python, Docker, AWS, Git.
    ###EXPERIENCE###
    5 years of experience in Python projects. Developed RESTful APIs. Used Docker.
    ###CERTIFICATIONS###
    AWS Certified Developer.
    """
    # Note: The DummyResumeParser uses "###" as markers for simplicity, not real heading detection


    # Perform comparison
    raw_score, total_possible, matched, missing = skill_comparer_instance.compare_skills(
        job_description=example_jd_text,
        resume_text=example_resume_text
    )

    print("\n--- Comparison Results (from example) ---")
    print(f"Raw Skill Match Score: {raw_score:.4f}")
    print(f"Total Possible Weighted Score: {total_possible:.4f}")
    print("\nMatched Items:")
    for label, items in matched.items():
        print(f"  {label}:")
        for item in items:
            print(f"    - '{item['text']}' (Sections: {item['matched_in_sections']}, Achieved Weight: {item['achieved_weight']:.4f})")

    print("\nMissing Items:")
    for label, items in missing.items():
        print(f"  {label}: {items}")

    print("-----------------------------------------")