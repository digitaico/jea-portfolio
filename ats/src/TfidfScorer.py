# TfidfScorer.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys # Import sys for debugging


class TfidfScorer:
    """
    Calculates the TF-IDF similarity score between two processed text documents.
    Requires Text_Processor dependency.
    """
    def __init__(self, text_processor):
        """
        Initializes the TfidfScorer with a Text_Processor instance.

        Args:
            text_processor: An instance of Text_Processor.
        """
        self.text_processor = text_processor
        print("\n--- TfidfScorer Initialized ---")
        # Check if text_processor is a valid instance (optional but good practice)
        if not hasattr(self.text_processor, 'process_text'):
             print("Warning: Text_Processor instance provided to TfidfScorer may be invalid or missing essential methods.")
        print("-------------------------------")


    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculates the cosine similarity between two processed text strings using TF-IDF.

        Args:
            text1 (str): The first processed text string.
            text2 (str): The second processed text string.

        Returns:
            float: The cosine similarity score (0.0 to 1.0), or 0.0 if calculation fails or texts are empty.
        """
        if not isinstance(text1, str) or not isinstance(text2, str):
             print("Error: Input texts for TfidfScorer are not strings.")
             return 0.0

        # TfidfVectorizer works best on pre-processed, tokenized text joined by spaces
        # Assumes input texts are already processed by Text_Processor
        if not text1.strip() or not text2.strip():
            print("Warning: One or both input texts for TF-IDF are empty after processing. Returning 0.0 similarity.")
            return 0.0 # Cannot calculate similarity with empty strings


        print("--- Calculating TF-IDF Similarity ---")
        try:
            # TfidfVectorizer expects a list of documents
            documents = [text1, text2]
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(documents)

            # Calculate cosine similarity between the two documents
            # similarity_matrix is a 2x2 matrix, we need the non-identity similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            tfidf_score = similarity_matrix[0, 1] # Similarity between doc 0 and doc 1
            print(f"TF-IDF Similarity Score: {tfidf_score:.4f}")
            return float(tfidf_score) # Return as float
        except Exception as e:
            print(f"Error calculating TF-IDF similarity: {e}")
            import traceback
            traceback.print_exc()
            return 0.0 # Return 0.0 on error
        finally:
             print("-------------------------------------")


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running TfidfScorer.py directly for testing.")

    # Need a dummy Text_Processor for the example
    class DummyTextProcessor:
         def process_text(self, text):
              # Simple cleaning and joining for example
              if not isinstance(text, str): return ""
              text = re.sub(r'[^a-zA-Z\s]', '', text) # Simple clean
              text = text.lower().strip()
              return " ".join(text.split()) # Join tokens with spaces

    # Instantiate dummy Text_Processor
    dummy_processor = DummyTextProcessor()


    # Instantiate TfidfScorer with the dummy processor
    tfidf_calculator = TfidfScorer(text_processor=dummy_processor)

    # Example texts (simulate processed texts)
    processed_text_a = dummy_processor.process_text("This is the first document about data science and python.")
    processed_text_b = dummy_processor.process_text("This document is about python and machine learning.")
    processed_text_c = dummy_processor.process_text("This is a completely unrelated document.")
    processed_text_empty = dummy_processor.process_text("")


    # Calculate similarities
    print("\n--- Example Similarity Calculations ---")
    score_ab = tfidf_calculator.calculate_similarity(processed_text_a, processed_text_b)
    print(f"Similarity between A and B: {score_ab:.4f}")

    score_ac = tfidf_calculator.calculate_similarity(processed_text_a, processed_text_c)
    print(f"Similarity between A and C: {score_ac:.4f}")

    score_a_empty = tfidf_calculator.calculate_similarity(processed_text_a, processed_text_empty)
    print(f"Similarity between A and Empty: {score_a_empty:.4f}")

    score_empty_empty = tfidf_calculator.calculate_similarity(processed_text_empty, processed_text_empty)
    print(f"Similarity between Empty and Empty: {score_empty_empty:.4f}")

    print("--- Example Calculations Complete ---")