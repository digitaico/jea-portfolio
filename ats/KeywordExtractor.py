import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data: stop words and tokenizer.
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')

class KeywordExtractor:
    """
    Methods to extract keywords from parsed text.
    """
    def __init__(self, language='english'):
        """
        Initialize the class with stop words for a given language.
        """
        try:
            self.stop_words = set(stopwords.words(language))
        except OSError:
            print(f"Error: NLTK  stop words for '{language}' not found.")
            self.stop_words = set() # empty set to avoid errors

    def _clean_text(self, text: str) -> str:
        """
        Cleans input text.
        1. Lowercase the text.
        2. Removes puntuation
        @params: text: str
        @returns: str # cleansed text
        """
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

    def extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords form input text using tokenization, cleansing and removing stop words.
        @params: text: str
        @returns: list<str> of extracted words.
        """
        cleaned_text = self._clean_text(text)
        tokens = word_tokenize(cleaned_text)
        keywords = [word for word in tokens if word not in self.stop_words and word.isalpha()]
        return keywords

# --// Usage
if __name__ == "__main__":
    job_text = """

    """
    resume_text = """

    """
    # Instantiate the class: to download if not exists stopwords and punkt
    extractor = KeywordExtractor(language='english')

    job_description_keywords = extractor.extract_keywords(job_text)
    resume_keywords = extractor.extract_keywords(resume_text)

    # print keywords as visual reference while script runs.
    print("Job description list of Keywords:")
    print(job_description_keywords)

    print("resume list of Keywords:")
    print(resume_keywords)
