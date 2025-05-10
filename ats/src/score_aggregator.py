# /mnt/disc2/local-code/jea-portfolio/ats/src/score_aggregator.py

import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class ScoreAggregator:
    def __init__(self, tfidf_weight: float = 0.5, skill_match_weight: float = 0.5):
        logger.info("\n--- ScoreAggregator Initialization ---")
        # Ensure weights are floats if read from a config or passed as strings
        self.tfidf_weight = float(tfidf_weight)
        self.skill_match_weight = float(skill_match_weight)
        logger.info(f"ScoreAggregator initialized with TF-IDF Weight: {self.tfidf_weight}, Skill Match Weight: {self.skill_match_weight}")
        logger.info("------------------------------------")

    def _calculate_tfidf_score(self, jd_text: str, resume_text: str) -> float:
        """Calculates TF-IDF cosine similarity score between JD and Resume."""
        documents = [jd_text, resume_text]
        if not jd_text or not resume_text:
            logger.warning("TF-IDF calculation skipped due to empty JD or Resume text. Returning 0.0.")
            return 0.0

        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(documents)
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]).flatten()[0]
            logger.debug(f"TF-IDF Cosine Similarity: {cosine_sim:.4f}")
            return float(cosine_sim) # Ensure return type is float
        except Exception as e:
            logger.error(f"Error during TF-IDF calculation: {e}")
            return 0.0

    def aggregate_and_format_scores(self, 
                                    achieved_weighted_skill_score, # Type hint removed for now to allow casting
                                    total_possible_weighted_skill_score, # Type hint removed for now to allow casting
                                    jd_text: str, 
                                    resume_text: str,
                                    missing_items: list) -> tuple:
        """
        Aggregates scores from different components and formats them into a final percentage.
        Explicitly casts all numeric inputs to floats to prevent TypeErrors.
        """
        logger.info("ScoreAggregator: Aggregating and formatting scores...")

        # Explicitly cast incoming scores to float to prevent TypeError
        achieved_weighted_skill_score = float(achieved_weighted_skill_score)
        total_possible_weighted_skill_score = float(total_possible_weighted_skill_score)

        # Calculate TF-IDF score
        tfidf_score = self._calculate_tfidf_score(jd_text, resume_text)
        
        # Calculate skill match score (percentage)
        skill_match_percentage = 0.0
        if total_possible_weighted_skill_score > 0: # This is the line that caused the TypeError if not float
            skill_match_percentage = (achieved_weighted_skill_score / total_possible_weighted_skill_score) * 100.0
        logger.info(f"Skill Match Percentage: {skill_match_percentage:.2f}% (Achieved: {achieved_weighted_skill_score:.2f}, Total Possible: {total_possible_weighted_skill_score:.2f})")

        # Combine scores using weights
        final_score = (self.tfidf_weight * tfidf_score * 100) + (self.skill_match_weight * skill_match_percentage)
        
        # Normalize final score if weights don't sum to 1.0 or if it exceeds 100 due to scaling
        total_weight = self.tfidf_weight + self.skill_match_weight
        if total_weight > 0:
            final_score = final_score / total_weight
        
        logger.info(f"Final Score: {final_score:.2f}%")

        return float(final_score), float(tfidf_score), float(skill_match_percentage) # Ensure all return values are floats