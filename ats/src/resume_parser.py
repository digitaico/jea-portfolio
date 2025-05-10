# ya
# /mnt/disc2/local-code/jea-portfolio/ats/src/resume_parser.py

import logging # Ensure logging is imported here

logger = logging.getLogger(__name__) # Get logger instance for this module

class ResumeParser:
    """
    Parses resume text into sections based on spaCy Matcher headings.
    Revised logic for content extraction. Now accepts pre-loaded nlp model and matcher via dependency injection.
    """
    # CORRECTED __init__ signature: now correctly accepts nlp, matcher, and section_weights
    def __init__(self, nlp, matcher, section_weights):
        """
        Initializes the ResumeParser with injected spaCy model and Matcher.
        Args:
            nlp: The pre-loaded spaCy Language model instance.
            matcher: The pre-configured spaCy Matcher instance with heading patterns.
            section_weights (dict): Weights for different sections.
        """
        logger.info("\n--- ResumeParser Initialization (Injected Dependencies) ---")

        self.nlp = nlp        # Use injected nlp model
        self.matcher = matcher # Use injected matcher
        self.section_weights = section_weights # Keep section_weights for internal use or potential future methods

        # All spaCy model loading, downloading, and matcher setup logic is removed from here.
        # It's now handled by app.py's get_or_create_nlp_components.

        logger.info("ResumeParser initialized with injected spaCy model and Matcher.")
        logger.info("-----------------------------")


    def parse_sections(self, text: str) -> list:
        """
        Parses the resume text into sections based on predefined headings using spaCy Matcher.
        Args:
            text (str): The raw text of the resume.
        Returns:
            list: A list of dictionaries, each representing a section with 'heading' and 'content' text.
                  Returns empty list on failure or if no sections are found by the Matcher.
        """
        logger.info("\n--- Running ResumeParser ---")
        # Ensure nlp model and matcher are loaded (they should be if initialized correctly)
        if self.nlp is None or self.matcher is None:
            logger.error("Error: spaCy model or Matcher not loaded for ResumeParser. Cannot parse sections.")
            return [] # Return empty list if model or matcher is not ready

        if not isinstance(text, str):
            logger.error(f"Error: Input text for ResumeParser is not a string, got {type(text)}.")
            return []

        try:
            # Process the text with the injected spaCy model
            doc = self.nlp(text)
            logger.debug(f"ResumeParser DEBUG: Created spaCy Doc with {len(doc)} tokens.")
            logger.debug("ResumeParser DEBUG: First 100 tokens and attributes:")
            for i, token in enumerate(doc[:min(100, len(doc))]):
                 token_text_escaped = token.text.replace('\n', '\\n')
                 logger.debug(f"  Token {i}: '{token_text_escaped}' | is_space={token.is_space} | is_punct={token.is_punct} | is_title={token.is_title} | is_upper={token.is_upper} | is_sent_start={token.is_sent_start} | pos={token.pos_}")

            # Run the injected Matcher on the document to find potential heading matches
            logger.debug("\nResumeParser DEBUG: Running Matcher to find heading matches...")
            matches = self.matcher(doc)
            logger.debug(f"ResumeParser DEBUG: Matcher found {len(matches)} potential heading matches.")

            matches = sorted(matches, key=lambda x: x[1])
            logger.debug(f"ResumeParser DEBUG: Sorted matches by start token index: {matches}")
            logger.debug("ResumeParser DEBUG: Details of found matches:")
            for match_id, start, end in matches:
                 span = doc[start:end]
                 label = self.nlp.vocab.strings[match_id]
                 span_text_escaped = span.text.replace('\n', '\\n')
                 logger.debug(f"  Match: '{span_text_escaped}' | Label: {label} | Tokens: {start}-{end}")


            # --- Process matches to define sections and extract content ---
            parsed_sections = []
            current_content_start = 0

            # Handle content before the first heading match
            if matches:
                 first_heading_start = matches[0][1]
                 if first_heading_start > 0:
                     header_content_span = doc[0 : first_heading_start]
                     header_text = header_content_span.text.strip()
                     if header_text:
                          parsed_sections.append({
                               'heading': 'Unidentified (Header)',
                               'content': header_text
                          })
                          logger.debug(f"ResumeParser DEBUG: Added 'Unidentified (Header)' section (tokens 0 to {first_heading_start}).")
                     current_content_start = first_heading_start # Update where the next content block starts


            # Iterate through the matches to define each section and its content
            for i, (match_id, start, end) in enumerate(matches):
                 # Get the heading text for the current match
                 heading_span = doc[start:end]
                 heading_text = heading_span.text.strip()

                 # Determine the end token index for the content of *this* heading's section.
                 content_end_pos = len(doc)
                 if i + 1 < len(matches):
                      content_end_pos = matches[i+1][1] # Content ends at the start of the next match


                 # Get the content span for *this* heading
                 content_span = doc[end : content_end_pos]
                 content_text = content_span.text.strip()

                 # Add the section {heading: text, content: text} structure
                 if heading_text: # Only add if the heading text is not empty
                      parsed_sections.append({
                          'heading': heading_text,
                          'content': content_text
                      })
                      heading_text_escaped = heading_text.replace('\n', '\\n')
                      logger.debug(f"ResumeParser DEBUG: Added Section: Heading='{heading_text_escaped}' (Content Length: {len(content_text)} (Tokens {start}-{content_end_pos}).")


            # --- Handle the case where no matches were found ---
            if not parsed_sections and len(doc) > 0:
                 full_text = doc.text.strip()
                 if full_text:
                      parsed_sections.append({
                           'heading': 'Unidentified (Full Document)',
                           'content': full_text
                      })
                      logger.debug("ResumeParser DEBUG: No sections parsed, adding entire document as 'Unidentified (Full Document)'.")

            final_cleaned_sections = [s for s in parsed_sections if s.get('heading', '').strip()]

            logger.debug(f"ResumeParser DEBUG: Final cleaned sections count (non-empty headings): {len(final_cleaned_sections)}")

            return final_cleaned_sections

        except Exception as e:
            logger.exception(f"Error during ResumeParser execution: {e}") # Use logger.exception for full traceback
            return []
        finally:
             logger.info("-----------------------------")