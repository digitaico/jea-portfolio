"""
Methods to estimate similarity between categorized skills and prioritized requiements
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
    Methods to calculate compatibility scores using TF-IDF and Prioritized Skill Matching
    """
    def __init__(self, text_processor: TextProcessor, skill_extractor: SkillExtractor, language='english', tfidf_weight=0.4, skill_match_weight=0.6):
        """
        Initializes the scorer with text processor dependency injection and scoring weights.
        """
        self.text_processor = text_processor
        self.skill_extractor = skill_extractor
        self.scoring_language = text_processor.stop_words_lang if text_processor.stop_words_lang else language
        self.tfidf_weight= tfidf_weight
        self.skill_match_weight = skill_match_weight

        # define weights for different categories of extracted requirements from Job Description
        self.requirement_weights = {
            "REQUIRED_SKILL_PHRASE": 1.5,
            "YEARS_EXPERIENCE":1.2,
            "QUALIFICATION_DEGREE": 1.0,
            "KNOWLEDGE_OF": 0.8
        }

        # validation for main weights
        if self.tfidf_weight + self.skill_match_weight > 1.0:
            print("Warning: main scoring weights sum exceeds 1.0. Normalizing weights")
            total_weight = self.tfidf_weight + self.skill_match_weight
            self.tfidf_weight /= total_weight
            self.skill_match_weight /= total_weight
            
    def calculate_scores(self, jd_text: str, resume_text: str) -> dict:
        """
        Estimate scores  using TF-IDF and Cosine Similarity, Prioritized Skill Match score and a Combined Score
        @params: jd_text: str
        @params: resume_text: str
        @returns: a dict containing three scores `tfidf_score`, `skill_score` and `combined_score`
                    Scores are floats between 0.0 and 1.0
        """
        # --- 1. TF-IDF score.
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

        # --- 2. Estimate Prioritized Skill Match Score.
        # Extract categorized requirements from JD and capabilities from Resume
        jd_extracted = self.skill_extractor.extract_requirements_and_skills(jd_text)
        resume_extracted = self.skill_extractor.extract_requirements_and_skills(resume_text)

        total_possible_weighted_score = 0.0
        achieved_weighted_score = 0.0
        matched_items = {}

        # Callect ALL unique extracters items from resume for lookup.
        all_resume_extracted_flat = set()
        for label, items in resume_extracted.items():
            all_resume_extracted_flat.update([item.lower().strip() for item in items ])
        # identify missing items during scoring loop
        missing_items = {} # store items that are in JD but not in resume.

        for jd_label, jd_items in jd_extracted.items():
            # Get the weight for this category from predefined weights, default to 0 if not found.
            item_weight = self.requirement_weights.get(jd_label, 0.5) # default weight fot not mapped categories
            
            for jd_item_raw in jd_items:
                jd_item = jd_item_raw.lower().strip() # JD item for comparison
                total_possible_weighted_score += item_weight # summ / add  weight for each item in JD

                # check if this cleaned JD item or similar variation exists in flattened set of resume extracted data.
                if jd_item in all_resume_extracted_flat:
                    achieved_weighted_score += item_weight
                    if jd_label not in matched_items:
                        matched_items[jd_label] = []
                    matched_items[jd_label].append(jd_item_raw)
                else:
                    # item is missing
                    if jd_label not in missing_items:
                        missing_items[jd_label] = []
                    missing_items[jd_label].append(jd_item_raw)

        # Calculate the skill match score based on weighted matches
        skill_match_score = 0.0
        if total_possible_weighted_score > 0:
            skill_match_score = achieved_weighted_score / total_possible_weighted_score

        # --- 3.  Calculate combined Score ---
        # validate that sum of weights don't exceed 1 and redistribute weights if required.
        combined_score = (self.tfidf_weight * tfidf_score) + (self.skill_match_weight * skill_match_score)

        # --- 4. Return all scores and list of matched items.
        return {
            "tfidf_score":float(tfidf_score),
            "skill_score":float(skill_match_score),
            "combined_score": float(combined_score),
            "matched_items": matched_items, # items from JD matched by resume
            "missing_items": missing_items
        }