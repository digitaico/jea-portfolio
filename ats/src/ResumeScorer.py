"""
Methods to estimate similarity between lists of keywords: one list from job description, second list from applicant's resume.
"""
import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys # to check if a module is run deirectly

# Download NLTK data: stop words and tokenizer.
def download_nktk_data(resource):
    resource_name = resource.split('/')[-1]
    try:
        nltk.data.find(resource)
        print(f"'{resource_name}' Data found")
    except LookupError:
        if __name__ == "__main__":
            print(f"'{resource_name}' Data NOT found... Attemting download...")
        try:
            nltk.download(resource_name, quiet=True)
            if __name__ == "__main__":
                print(f"'{resource_name}' download complete.")
        except Exception as e:
            if __name__ == "__main__":
                print(f"Error downloading '{resource_name}' data {e}")
                print(f"Try downloading '{resource_name}' manually in Python interpreter: nltk.download('{resource_name}')")

# run check for required data
download_nktk_data('tokenizers/punkt')
download_nktk_data('corpora/stopwords')

class TextProcessor:
    """
    Class methods to perfom text cleaning
    """
    def __init__(self, language='english'):
        """
        Initialize the class with stop words for a given language.
        """
        self.stop_words_lang = 'english' # default fallback
        try:
            stopwords.words(language)
            self.stop_words_lang = language
            print(f"Using '{self.stop_words_lang}' stop words.")
        except OSError:
            if __name__ == "__main__":
                print(f"Error: NLTK  stop words for '{language}' not found. Fallback to 'english'")
            try:
                stopwords.words(self.stop_words_lang)
                print(f"Using fallback '{self.stop_words_lang}' stop words.")
            except OSError:
                if __name__ == "__main__":
                    print(f"Error: NLTK  stop words for '{language}' not found even for Fallback. No stop words will be used.")
                self.stop_words_lang = None # no stop words loaded

    def clean_and_tokenize(self, text: str) -> list[str]:
        """
        Cleans input text.
        1. Lowercase the text.
        2. Removes puntuation
        Extract keywords form input text using tokenization, cleansing and removing stop words.
        @params: text: str
        @returns: list<str> of extracted words.
        """
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        tokens = word_tokenize(text)
        cleaned_tokens = [word for word in tokens if word not in self.stop_words and word.isalpha()]
        return cleaned_tokens

    def clean_text(self, text: str) -> str:
        """
        Cleans input text.
        1. Lowercase the text.
        2. Removes puntuation
        @params: text: str
        @returns: str # cleansed text
        """
        if not isinstance(text, str):
            return ""

        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

class ResumeScorer:
    """
    Methods to calculate afinity score between a job description and a resume using TF-IDF and Cosine Similarity
    """
    def __init__(self, text_processor: TextProcessor, language='english'):
        """
        Initializes the scorer with text processor dependency injection.
        """
        self.text_processor = text_processor
        self.scoring_language = text_processor.stop_words_lang if text_processor.stop_words_lang else language

    def calculate_score(self, jd_text: str, resume_text: str) -> float:
        """
        Estimate score using TF-IDF and Cosine Similarity
        @params: jd_text: str
        @params: resume_text: str
        @returns: float between 0.0 and 1.0 cosine similarity of two vectors
        """
        cleaned_resume_text = self.text_processor.clean_text(resume_text)
        cleaned_jd_text = self.text_processor.clean_text(jd_text)

        # if any cleaned text is empt similarity is 0.0
        if not cleaned_jd_text or not cleaned_resume_text:
            return 0.0

        # Create a TfifdVectorizer
        vectorizer = TfidfVectorizer(stop_words='english')

        try:
            # fit and transform documents: build vocabulary included on both documents
            tfidf_matrix = vectorizer.fit_transform([cleaned_jd_text, cleaned_resume_text])

            # Check if features were extracted - vaocabulary is no empty
            if tfidf_matrix.shape[1] == 0:
                return 0.0

            # estimate cosine similarity
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(cosine_sim)
        except ValueError as e:
            # If texts are very short or contain no terms after cleaning
            print(f"ValueError during TF-IDF processing: {e}")
            return 0.0
        except Exception as e:
            print(f"An error occurred during score calculation: {e}")
            return 0.0

# --- // usage // ----
if __name__ == "__main__":
    print("Running ResumeScorer.py directly for testing.")
    job_description_text = """
    We are looking for a highly motivated Software Engineer with 3+ years of experience
    in Python development. Experience with web frameworks like Flask or FastAPI is
    required. Knowledge of databases, SQL, and cloud platforms (AWS, Azure, or GCP)
    is a strong plus. Must have experience with unit testing and version control
    (Git). Excellent communication and problem-solving skills are essential.
    """
    resume_text = """
    John Doe
    ...
    Highly motivated Software Engineer with 4 years of experience in developing
    web applications using Python and Flask. Proficient in SQL database design
    and management. Experienced with AWS services and Git version control.
    Strong problem-solving skills and a proven ability to work in a team.
    ...
    Skills:
    Programming Languages: Python, JavaScript
    Web Frameworks: Flask, Django (basic)
    Databases: SQL, PostgreSQL, MongoDB (basic)
    Cloud Platforms: AWS
    Tools: Git, Docker
    """

    # 1 . Instantiate text processor
    text_processor = TextProcessor(language = 'english')
    
    # 2. Instantiate ResumeScorrer, injecting Textprocessor dependency
    scorer = ResumeScorer(text_processor=text_processor)

    # 3. Calculate the score
    similarity_score = scorer.calculate_score(job_description_text, resume_text)

    # Print the score
    print(f"Dear! Your resume compatibility Score (TF-IDF + Cosine Similarity) is {similarity_score * 100:.2f}%")



