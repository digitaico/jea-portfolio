# Resume_Parser.py
# ya

import spacy
import re
import sys # Import sys to check execution context


class Resume_Parser:
    """
    A class to parse resume text and identify sections based on common headings.
    Uses a spaCy model for tokenization and potentially other linguistic features.
    """
    def __init__(self, model_name: str = 'en_core_web_sm'):
        """
        Initializes the Resume_Parser by loading a spaCy model.

        Args:
            model_name (str): The name of the spaCy model to load.
        """
        self.model_name = model_name
        self.nlp = None
        self._default_headings = self._define_default_headings() # Define default headings

        try:
            print(f"\n--- Resume_Parser Initialization ({self.model_name}) ---")
            print(f"Attempting to load spaCy model: {model_name}")
            # Use the same check as in Skill_Extractor for Flask reloader
            if '__main__' in sys.modules or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
                 # In debug mode reloader, spaCy might already be loaded in the parent process.
                 # Checking if it's already loaded might prevent issues,
                 # but simple load is often fine. Explicitly load here.
                 pass # Proceed to load below

            self.nlp = spacy.load(model_name)
            print(f"SpaCy model '{model_name}' loaded successfully for Resume_Parser.")

        except OSError:
            print(f"\nERROR: spaCy model '{model_name}' not found for Resume_Parser.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # Handle model loading failure
            print("Resume_Parser initialized without a functional spaCy model.")
        except Exception as e:
             print(f"\nAn unexpected error occurred during Resume_Parser initialization: {e}")
             import traceback
             traceback.print_exc()
             self.nlp = None

        print("---------------------------------------------")


    def _define_default_headings(self) -> list:
        """Defines a list of common resume section headings."""
        # This list should be comprehensive based on typical resume structures
        return [
            "Summary", "Objective", "Experience", "Work Experience", "Employment History",
            "Education", "Skills", "Technical Skills", "Professional Skills",
            "Projects", "Portfolio", "Awards", "Certifications", "Licenses",
            "Publications", "Presentations", "Volunteer Experience", "Interests",
            "References", "Contact", "About", "Profile", "Languages"
        ]

    def parse_sections(self, text: str) -> list:
        """
        Parses resume text to identify sections based on predefined headings.

        Args:
            text (str): The raw text of the resume.

        Returns:
            list: A list of dictionaries, where each dict contains 'heading',
                  'start_token', and 'end_token' for identified sections *content*.
                  Returns an empty list if nlp model is not loaded or parsing fails.
        """
        if not isinstance(text, str) or not text.strip():
             print("Warning: Input text for Resume_Parser is empty or not a string.")
             return [] # Return empty list for invalid input

        if self.nlp is None:
             print("Warning: spaCy model not loaded in Resume_Parser. Cannot parse sections.")
             return [] # Return empty list if NLP model is not functional

        # Process the text with spaCy
        # Using try-except for robustness in case of unexpected text content
        try:
            doc = self.nlp(text)
        except Exception as e:
            print(f"Error processing text with spaCy in Resume_Parser: {e}")
            import traceback
            traceback.print_exc()
            return [] # Return empty list on spaCy processing error

        # If doc is empty after processing (e.g., text was weird characters), return empty
        if not doc:
             print("Warning: spaCy doc is empty after processing text in Resume_Parser. Cannot parse sections.")
             return []


        # Regex to potentially identify headings.
        # Looks for line starting with common heading, optionally followed by punctuation or newline
        # Handles optional leading/trailing whitespace around heading text
        # Using a case-insensitive match and handling potential symbols around headings
        # Example: "^\\s*(SUMMARY|EDUCATION|SKILLS)\\s*[^a-zA-Z0-9\\n]*$\\n"
        # Building the regex dynamically from the default headings
        heading_pattern = re.compile(
             r"^\s*(" + "|".join(re.escape(h) for h in self._default_headings) + r")\s*[^a-zA-Z0-9\n]*$",
             re.IGNORECASE | re.MULTILINE # Case-insensitive and multiline mode
        )


        # Iterate through the document's text to find potential section headings using regex on lines.
        lines = text.splitlines()
        line_start_char_indices = [0] # Start index of the first line is 0
        for line in lines[:-1]:
             line_start_char_indices.append(line_start_char_indices[-1] + len(line) + 1) # +1 for the newline character

        # List to store potential heading matches as (heading_text_raw, start_char_index, end_char_index_of_line)
        potential_heading_matches = []

        for i, line in enumerate(lines):
             match = heading_pattern.match(line)
             if match:
                  # Store the start char index of the *line* where the heading was found, and the end char of the line
                  # We will map this line's span to tokens later.
                  potential_heading_matches.append({
                      'heading_line_text': line.strip(), # Store the stripped line text
                      'start_char_of_line': line_start_char_indices[i],
                      'end_char_of_line': line_start_char_indices[i] + len(line) # End is exclusive
                  })


        # Map the character spans of heading lines to token spans
        heading_token_spans = [] # List to store (heading_line_text, start_token_index, end_token_index)

        if potential_heading_matches: # Only proceed if potential headings were found
             # Sort matches by their character start index just in case
             potential_heading_matches.sort(key=lambda x: x['start_char_of_line'])

             # Iterate through spaCy doc to find tokens that correspond to heading line spans
             current_heading_match_index = 0
             for token in doc:
                  if current_heading_match_index < len(potential_heading_matches):
                       current_match = potential_heading_matches[current_heading_match_index]

                       # Check if the token's start character index falls within the current heading line's character span
                       # Using <= end_char_of_line because token.idx is the start char of the token
                       if current_match['start_char_of_line'] <= token.idx < current_match['end_char_of_line']:
                            # This token is part of a heading line.
                            # Find the start token of this heading line span
                            heading_line_start_token = token.i
                            # Find the end token of this heading line span by looking ahead or checking the next token's start index
                            heading_line_end_token = heading_line_start_token + 1 # Start assuming it's just this token

                            # Find all tokens belonging to this same heading line
                            for j in range(heading_line_start_token + 1, len(doc)):
                                 next_token = doc[j]
                                 # Check if the next token's start char index is still within the current heading line's char span
                                 if next_match['start_char_of_line'] <= next_token.idx < next_match['end_char_of_line']:
                                      heading_line_end_token = next_token.i + 1 # Extend the end token span
                                 else:
                                      break # Next token is outside this heading line


                            # We've found the token span for the heading line.
                            # Now, identify the canonical heading from the text within this token span.
                            heading_span_tokens = doc[heading_line_start_token : heading_line_end_token]
                            heading_text = heading_span_tokens.text.strip() # Get text of the token span

                            # Normalize heading text for matching against default headings
                            normalized_heading = re.sub(r'[^a-z0-9]', '', heading_text.lower())

                            # Find the canonical heading from our default list based on normalized text
                            canonical_heading = next(
                                 (h for h in self._default_headings if re.sub(r'[^a-z0-9]', '', h.lower()) == normalized_heading),
                                 heading_text # Fallback to the original stripped text if normalization doesn't match a default
                            )

                            heading_token_spans.append({
                                 'heading': canonical_heading,
                                 'start_token': heading_line_start_token,
                                 'end_token': heading_line_end_token # This span covers the heading tokens
                            })

                            # Move to check for the next potential heading match from the original list
                            current_heading_match_index += 1
                            # Continue iterating tokens from where this heading span ended
                            # Adjust token loop index? No, the outer loop advances the token.
                            # The current_heading_match_index ensures we look at the right potential match next time.


        # Sort identified token spans for headings by their start token index
        heading_token_spans.sort(key=lambda x: x['start_token'])

        # --- Define Section Spans for CONTENT ---
        # A section's content goes from the END_TOKEN of its heading to the START_TOKEN of the next heading,
        # or the end of the document if it's the last section.

        content_sections = []
        # Add a dummy heading span at the very beginning (token 0) to capture content before the first real heading
        # And a dummy heading span at the very end to simplify loop logic
        sections_boundaries = [{'end_token': 0}] + heading_token_spans + [{'start_token': len(doc)}]


        for i in range(len(sections_boundaries) - 1):
             content_start_token = sections_boundaries[i]['end_token']
             content_end_token = sections_boundaries[i+1]['start_token']

             # Determine the heading label for this content section
             # If i == 0, this is content BEFORE the first real heading. Label as 'Unidentified (Header)'.
             # Otherwise, the label is the heading *after* the content_start_token.
             if i == 0:
                  section_label = "Unidentified (Header)"
             else:
                  section_label = sections_boundaries[i]['heading']


             # Ensure the content span is valid (start token < end token)
             if content_start_token < content_end_token:
                  content_sections.append({
                      'heading': section_label, # Use the determined label
                      'start_token': content_start_token, # Start of content
                      'end_token': content_end_token # End of content (exclusive)
                  })
             # No warning for empty sections between headings, it's common.


        # Handle the case where no headings were found at all (the heading_token_spans list was empty)
        # In this case, the sections_boundaries would be [{'end_token': 0}, {'start_token': len(doc)}]
        # The loop would add one 'Unidentified (Header)' section from 0 to len(doc). This is correct.
        # Ensure if doc is empty, we still return empty.
        if not content_sections and len(doc) > 0:
             # This case should theoretically be handled by the loop if doc > 0, but as a fallback
             # This print might indicate an issue with the heading finding logic if doc is not empty but no sections are formed.
             print("Warning: Document contains tokens, but no content sections were formed after parsing headings.")
             # The loop with dummy boundaries should cover this, resulting in 'Unidentified (Header)'


        # --- Debugging Prints ---
        print("\nResume Parser - Identified Content Sections:")
        if content_sections:
             for section in content_sections:
                  # Get the span of tokens for the section content
                  section_span = doc[section['start_token']:section['end_token']]
                  # Limit text sample length to prevent excessive output
                  text_sample = str(section_span.text).replace('\n', ' ').replace('\r', '')[:100] # Get text, remove newlines for print, limit length
                  print(f"  - Heading: '{section['heading']}', Tokens: {section['start_token']}-{section['end_token']}, Text Sample: '{text_sample}...'")
        else:
             print("  No content sections identified or document was empty.")
        print("---------------------------------------------")


        return content_sections


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Resume_Parser.py directly for testing.")

    # Use a smaller model for direct testing if md/lg is slow
    example_model_name = 'en_core_web_sm'

    # Instantiate Resume_Parser with config
    parser = Resume_Parser(model_name=example_model_name)

    # Define example resume text
    example_resume_text = """
    John Doe
    123 Main St | johndoe@email.com

    Summary
    Highly motivated individual with experience in Python.

    Experience
    Software Engineer | Tech Company A | 2020-Present
    Worked on backend systems using Flask.

    Skills
    Python, SQL, AWS.

    Education
    Bachelor's Degree in Computer Science | University ABC | 2016-2020

    Projects
    Built a web application using React.

    Awards & Recognition
    Employee of the Year 2022.

    References
    Available upon request.
    """

    # Check if the parser is functional before proceeding with parsing
    if parser.nlp is None:
         print("\nSkipping parsing example due to non-functional parser.")
         # Exit or return if not functional
         # sys.exit("Parser not functional for example.") # Uncomment if you want it to exit


    # Parse sections if parser is functional
    print("\nParsing Example Resume:")
    sections = parser.parse_sections(example_resume_text)

    # The parse_sections method now includes debug prints,
    # so simply calling it will show the output.
    # You can add additional prints here if needed, e.g.,
    # print("\nParsed Sections (Returned Value):")
    # print(sections)

    # Example with text having no clear headings
    print("\nParsing Example Resume with No Clear Headings:")
    example_no_headings_text = """
    This is just a block of text. It doesn't have any standard resume headings.
    It might be a simple profile summary or just raw skills listed.
    Python, Java, SQL.
    """
    sections_no_headings = parser.parse_sections(example_no_headings_text)
    # Prints are inside the method