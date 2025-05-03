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
from Skill_Extractor import SkillExtractor


# Download NLTK data: stop words and tokenizer.
def download_nktk_data(resource):
    resource_name = resource.split('/')[-1]
    try:
        nltk.data.find(resource)
        print(f"'{resource_name}' Data found")
    except LookupError:
        if __name__ == "__main__":
            print(f"'{resource_name}' Data NOT found... Attempting download...")
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
    Methods to calculate afinity score between a job description and a resume using TF-IDF and Cosine Similarity and NLP 
    : scaPy Skill and entity extraction
    """
    def __init__(self, text_processor: TextProcessor, skill_extractor: SkillExtractor, language='english', tfidf_weight=0.6, skill_weight=0.4):
        """
        Initializes the scorer with text processor dependency injection and scoring weights.
        """
        self.text_processor = text_processor
        self.skill_extractor = skill_extractor
        self.scoring_language = text_processor.stop_words_lang if text_processor.stop_words_lang else language
        self.tfidf_weight= tfidf_weight
        self.skill_weight = skill_weight

        # weights validation
        if self.tfidf_weight + self.skill_weight > 1.0:
            print("Warning: TF-IDF weight and Skill weight Sum exceeds 1.0. Normalizing weights")
            total_weight = self.tfidf_weight + self.skill_weight
            self.tfidf_weight /= total_weight
            self.skill_weight /= total_weight
            
    def calculate_scores(self, jd_text: str, resume_text: str) -> dict:
        """
        Estimate score using TF-IDF and Cosine Similarity, Skill Match score and a Combined Score
        @params: jd_text: str
        @params: resume_text: str
        @returns: a dict containing three scores `tfidf_score`, `skill_score` and `combined_score`
                    Scores are floats between 0.0 and 1.0
        """
        # -- TF-IDF score.
        cleaned_resume_text = self.text_processor.clean_text(resume_text)
        cleaned_jd_text = self.text_processor.clean_text(jd_text)

        tfidf_score = 0.0

        if cleaned_jd_text and cleaned_resume_text:
            # Create a TfifdVectorizer
            vectorizer = TfidfVectorizer(stop_words=self.scoring_language)
            try:
                # fit and transform documents: build vocabulary included on both documents
                tfidf_matrix = vectorizer.fit_transform([cleaned_jd_text, cleaned_resume_text])
                # Check if features were extracted - vaocabulary is no empty
                if tfidf_matrix.shape[1] > 0:
                    tfidf_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            except ValueError as e:
                # If texts are very short or contain no terms after cleaning
                print(f"ValueError during TF-IDF processing: {e}")
            except Exception as e:
                print(f"An error occurred during TF-IDF score calculation: {e}")

        # -- Skill Match score.
        jd_skills = self.skill_extractor.extract_skills(jd_text)
        resume_skills = self.skill_extractor.extract_skills(resume_text)

        skill_score = 0.0
        common_skills= []

        if jd_skills: # avoid division by ZERO
            # use sets for comparison
            jd_skills_set = set(jd_skills)
            resume_skills_set = set(resume_skills)
            
            # find common skills
            common_skills = list(jd_skills_set.intersection(resume_skills_set))
            # estimate skill score: Number of common skills / total Unique Jd skills
            skill_score = len(common_skills) / len(jd_skills_set)

        # -- Estimate combined score
        # make sure weights do not exceed 1.0 and distribute remanining weight if required.
        combined_score = (self.tfidf_weight * tfidf_score) + (self.skill_weight * skill_score)
            
        # return all scores and common skills
        return {
            "tfidf_score":float(tfidf_score),
            "skill_score":float(skill_score),
            "combined_score":float(combined_score),
            "common_skills": common_skills 
        }

