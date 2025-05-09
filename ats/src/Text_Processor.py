# Text_Processor.py
# ya

import re
import string
import nltk
import sys # Import sys to check execution context
import os # Import os to check environment variables


# --- NLTK Downloads ---
# Download necessary NLTK data. Check if already downloaded to avoid repeating.
# Use a flag to ensure downloads happen only once globally or per relevant process.

# Global flag to track download status
_nltk_downloads_completed = False

def _perform_nltk_downloads():
    """Downloads necessary NLTK data if not already downloaded."""
    global _nltk_downloads_completed
    if not _nltk_downloads_completed:
        # Print informative message before attempting downloads
        print("Attempting to perform NLTK data downloads (punkt, stopwords)...")
        try:
            # Check if data is already present without trying to download
            punkt_downloaded = False
            try:
                nltk.data.find('tokenizers/punkt')
                punkt_downloaded = True
                print("NLTK punkt tokenizer data found locally.")
            except nltk.downloader.DownloadError:
                pass # Not found, need to download
            except LookupError:
                 pass # Not found, need to download


            stopwords_downloaded = False
            try:
                nltk.data.find('corpora/stopwords')
                stopwords_downloaded = True
                print("NLTK stopwords data found locally.")
            except nltk.downloader.DownloadError:
                pass # Not found, need to download
            except LookupError:
                 pass # Not found, need to download


            # Only download if necessary
            if not punkt_downloaded:
                print("Downloading NLTK punkt tokenizer data...")
                # Use quiet=True to reduce console spam unless error occurs
                nltk.download('punkt', quiet=True, raise_on_error=True)
                print("NLTK punkt download complete.")

            if not stopwords_downloaded:
                 print("Downloading NLTK stopwords data...")
                 nltk.download('stopwords', quiet=True, raise_on_error=True)
                 print("NLTK stopwords download complete.")

            _nltk_downloads_completed = True # Set flag on successful downloads (or if already found)
            print("NLTK data download check/completion successful.")

        except Exception as e:
            print(f"Error during NLTK data download: {e}")
            print("Warning: NLTK text processing features (like tokenization, stopwords) may be limited.")
            # Flag remains False if download fails


class Text_Processor:
    """
    A class for cleaning and processing text data using NLTK.
    Supports different languages for stopwords.
    """
    def __init__(self, language: str = 'english'):
        """
        Initializes the Text_Processor with a specified language for stopwords.

        Args:
            language (str): The language code for stopwords (e.g., 'english').
        """
        self.language = language.lower()
        self.stopwords = set()

        # Perform downloads when the class is initialized.
        # Check if running as the main script or in a reloader context to potentially limit redundant downloads.
        # The os.environ.get('WERKZEUG_RUN_MAIN') check is for Flask debug mode reloader.
        # The '__main__' in sys.modules check is for running the script directly.
        # A more robust solution for production might manage downloads outside the class init.
        # For development/debugging, performing it here is often practical.
        if '__main__' in sys.modules or os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.environ.get('JEMATS_FORCE_NLTK_DOWNLOAD') == 'true':
             _perform_nltk_downloads()


        # Load stopwords if downloads were successful and language is supported
        if _nltk_downloads_completed:
            try:
                self.stopwords = set(nltk.corpus.stopwords.words(self.language))
                # print(f"Loaded {len(self.stopwords)} stopwords for '{self.language}'.") # Keep this print for confirmation
            except OSError:
                 print(f"Warning: Stopwords not available for language '{self.language}'. Text will not be filtered for stopwords.")
                 self.stopwords = set() # Ensure stopwords is an empty set
            except Exception as e:
                 print(f"Error loading stopwords for '{self.language}': {e}")
                 self.stopwords = set() # Ensure stopwords is an empty set
        else:
             print("Warning: NLTK downloads failed. Stopwords not loaded.")


    def clean_text(self, text: str) -> str:
        """
        Cleans the input text by removing special characters, numbers,
        converting to lowercase, and handling whitespace.

        Args:
            text (str): The raw input text.

        Returns:
            str: The cleaned text.
        """
        if not isinstance(text, str):
             return "" # Return empty string for non-string input

        # Remove special characters and numbers (keep basic punctuation for now)
        # Keep letters, spaces, basic punctuation '.', ',', '!', '?'
        # Remove everything that is NOT a letter, space, or basic punctuation
        # Added semicolon ':' and hyphen '-' as they can be part of terms
        text = re.sub(r'[^a-zA-Z\s.,!?;:_-]', '', text)

        # Convert to lowercase
        text = text.lower()

        # Replace multiple whitespaces with a single space
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def tokenize_and_filter(self, text: str) -> list:
        """
        Tokenizes cleaned text and filters out punctuation and stopwords.

        Args:
            text (str): The cleaned input text.

        Returns:
            list: A list of tokens (words) after filtering.
        """
        if not isinstance(text, str):
             return [] # Return empty list for non-string input

        # Tokenize the text using NLTK's word_tokenize
        # Ensure punkt is downloaded, fallback to simple split if not functional
        if _nltk_downloads_completed:
             try:
                 tokens = nltk.word_tokenize(text)
             except LookupError:
                  print("Warning: NLTK punkt tokenizer not found. Falling back to simple split.")
                  tokens = text.split() # Fallback
             except Exception as e:
                   print(f"Error during NLTK tokenization: {e}. Falling back to simple split.")
                   tokens = text.split() # Fallback
        else:
             print("Warning: NLTK downloads not completed. Falling back to simple split for tokenization.")
             tokens = text.split() # Fallback if downloads failed


        # Remove punctuation and stopwords
        # Punctuation is defined in string.punctuation
        # Stopwords are loaded in __init__
        # Ensure self.stopwords is a set before checking containment
        stopwords_set = self.stopwords if isinstance(self.stopwords, set) else set()

        filtered_tokens = [
            token for token in tokens
            if token not in string.punctuation and token not in stopwords_set # Use the set of stopwords
        ]

        return filtered_tokens

    def process_text(self, text: str) -> str:
        """
        Applies cleaning and tokenization/filtering, then joins tokens back into a string.
        This output format is suitable for TF-IDF vectorization.

        Args:
            text (str): The raw input text.

        Returns:
            str: The processed text as a single string of filtered tokens, separated by spaces.
        """
        cleaned_text = self.clean_text(text)
        tokens = self.tokenize_and_filter(cleaned_text)
        # Join tokens back into a space-separated string for TF-IDF
        return " ".join(tokens)

    # You might add other processing methods here later, e.g., stemming, lemmatization


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running Text_Processor.py directly for testing.")

    # Example text
    raw_text_en = "This is an example sentence with some punctuation! And numbers like 123. It also has stopwords like the, is, and an."
    raw_text_es = "Este es un ejemplo de frase con algo de puntuación! Y números como 123. También tiene palabras vacías como este, es, un."
    raw_text_mixed = "Hello World! This is a test - with a hyphen. 123."

    # Instantiate Text_Processor for English
    processor_en = Text_Processor(language='english')
    processed_en = processor_en.process_text(raw_text_en)
    print(f"\nOriginal English Text: {raw_text_en}")
    print(f"Processed English Text: {processed_en}")

    processed_mixed_en = processor_en.process_text(raw_text_mixed)
    print(f"\nOriginal Mixed Text: {raw_text_mixed}")
    print(f"Processed Mixed Text (English): {processed_mixed_en}")


    # Instantiate Text_Processor for Spanish (requires spanish stopwords)
    processor_es = Text_Processor(language='spanish')
    processed_es = processor_es.process_text(raw_text_es)
    print(f"\nOriginal Spanish Text: {raw_text_es}")
    print(f"Processed Spanish Text: {processed_es}")

    # Test with a non-string input
    processed_invalid = processor_en.process_text(None)
    print(f"\nProcessed invalid input (None): '{processed_invalid}'")

    # Test with empty string
    processed_empty = processor_en.process_text("")
    print(f"\nProcessed empty string: '{processed_empty}'")