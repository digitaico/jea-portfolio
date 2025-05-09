# Resume_Parser.py

import spacy
from spacy.matcher import Matcher
import re
import sys

# Removed module-level spaCy loading

class Resume_Parser:
    """
    A class to parse resume text and identify standard sections and their boundaries.
    Configurable with a spaCy model name.
    """
    def __init__(self, model_name: str = 'en_core_web_sm'):
        """
        Initializes the Resume_Parser by loading a spaCy model and setting up the Matcher.

        Args:
            model_name (str): The name of the spaCy model to load.
        """
        self.model_name = model_name
        try:
            # Load the specified spaCy model during initialization
            self.nlp = spacy.load(model_name)
            # print(f"spaCy model '{model_name}' loaded successfully for Resume_Parser.") # Keep quiet
            self.matcher = Matcher(self.nlp.vocab)
            self._add_section_patterns() # Add patterns for common section headings
        except OSError:
            print(f"spaCy model '{model_name}' not found.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # Handle model loading failure
            self.matcher = None
            print("Resume_Parser initialized without a functional spaCy model.")


    def _add_section_patterns(self):
        """
        Adds patterns to the Matcher to identify common resume section headings.
        These patterns are still hardcoded within the class for this basic implementation,
         but could also be passed in __init__ if needed for extreme flexibility.
         Uses case-insensitive matching (LOWER).
        """
        # Common section headings (case-insensitive check using LOWER)
        # Add common variations you encounter in resumes here
        section_patterns = [
            [{"LOWER": "summary"}], [{"LOWER": "objective"}],
            [{"LOWER": "experience"}], [{"LOWER": "work"}, {"LOWER": "experience"}],
            [{"LOWER": "professional"}, {"LOWER": "experience"}],
            [{"LOWER": "education"}],
            [{"LOWER": "skills"}], [{"LOWER": "technical"}, {"LOWER": "skills"}],
            [{"LOWER": "certifications"}], [{"LOWER": "projects"}],
            [{"LOWER": "publications"}], [{"LOWER": "awards"}],
            [{"LOWER": "volunteer"}, {"LOWER": "experience"}],
            [{"LOWER": "languages"}], [{"LOWER": "interests"}],
            # Add more patterns for other sections as needed
        ]
        self.matcher.add("SECTION_HEADING", section_patterns)


    def parse_sections(self, text: str) -> list[dict]:
        """
        Parses resume text to identify sections and their token boundaries.

        Args:
            text (str): The raw resume text.

        Returns:
            list[dict]: A list of dictionaries, each representing a section's content area:
                        [{'heading': '...', 'start_token': X, 'end_token': Y}, ...]
                        Returns an empty list if no sections are found or spaCy fails.
        """
        if self.nlp is None or self.matcher is None:
            # Print message already in __init__
            return []

        doc = self.nlp(text)

        # Find matches for section headings
        matches = self.matcher(doc)

        # Sort matches by their start position in the document
        matches = sorted(matches, key=lambda x: x[1])

        sections_list = []
        current_heading_end_token = 0 # Assume content before the first heading starts from token 0

        # Handle content *before* the first heading as a potential "Unidentified" section
        if matches:
            first_match_id, first_start, first_end = matches[0]
            # If the first heading is not at the very beginning (token 0)
            if first_start > 0:
                 sections_list.append({
                      'heading': 'Unidentified (Header)',
                      'start_token': 0,
                      'end_token': first_start
                 })
            current_heading_end_token = first_end # Content for the first identified section starts here


        # Process subsequent matches (headings) to define the end of the previous section's content
        for match_id, start, end in matches: # Iterate through all matches now
            span = doc[start:end] # The current matched heading span
            heading_text = span.text.strip()

            # If this is not the very first section defined (content before first heading)
            if current_heading_end_token < start:
                 # The content of the previous section ends just before the current heading starts
                 content_start_token = current_heading_end_token
                 content_end_token = start

                 sections_list.append({
                     'heading': heading_text, # The heading for THIS section's content
                     'start_token': content_start_token,
                     'end_token': content_end_token
                 })

            # Update the end token for the *next* potential content block (after the current heading)
            current_heading_end_token = end


        # After the loop, capture the content of the *last* identified section
        # This runs from the end of the last heading to the end of the document
        if current_heading_end_token < len(doc):
            content_start_token = current_heading_end_token
            content_end_token = len(doc)

            sections_list.append({
                'heading': 'Unidentified (Footer)', # Label for content after last heading
                'start_token': content_start_token,
                'end_token': content_end_token
            })

        # If no headings were found at all, treat the whole document as Unidentified
        if not matches and len(doc) > 0:
             sections_list.append({
                 'heading': 'Unidentified (Full Document)',
                 'start_token': 0,
                 'end_token': len(doc)
             })

        return sections_list

# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Resume_Parser.py directly for testing.")

    # Instantiate the parser with a specific model name
    # You can change 'en_core_web_sm' to 'en_core_web_md' or 'lg' here if downloaded
    parser = Resume_Parser(model_name='en_core_web_sm')

    if parser.nlp is None or parser.matcher is None:
         print("Skipping parsing example due to spaCy model or matcher loading failure.")
         sys.exit(1)

    resume_sample_text = """
    Contact Info

    Summary
    Highly motivated Software Engineer.

    Experience
    Worked on projects.

    Skills
    Python, Java.

    Additional Information.
    """

    parsed_sections_refined = parser.parse_sections(resume_sample_text)

    print("\nParsed Resume Sections (Refined Output):")
    if parsed_sections_refined:
        for section_info in parsed_sections_refined:
            # Get the actual text span for the content using start/end tokens
            # Note: This re-processes the text. In app, you'll use the Doc processed once.
            doc_for_text = parser.nlp(resume_sample_text)
            content_text_span = doc_for_text[section_info['start_token'] : section_info['end_token']]

            print(f"--- {section_info['heading']} ---")
            print(f"Tokens: {section_info['start_token']} to {section_info['end_token']}")
            print(f"Content (Snippet): '{content_text_span.text.strip()[:50]}...'") # Print snippet
            print("-" * (len(section_info['heading']) + 6))
    else:
        print("No sections identified.")