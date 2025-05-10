# ScoreAggregator.py

from collections import defaultdict # Still useful for result formatting

class ScoreAggregator:
    """
    Aggregates raw TF-IDF and skill comparison results, applies weights,
    calculates the combined score, and formats the final output.
    """
    def __init__(self, tfidf_weight: float, skill_match_weight: float):
        """
        Initializes the ScoreAggregator with the scoring weights.

        Args:
            tfidf_weight (float): The weight for the TF-IDF similarity score (0.0 to 1.0).
            skill_match_weight (float): The weight for the prioritized skill match score (0.0 to 1.0).
                                         The aggregator will normalize these if their sum is not 1.0.
        """
        print("\n--- ScoreAggregator Initialized ---")
        # Validate and store weights
        # Ensure weights are non-negative and sum up to at most 1.0 initially.
        # Then normalize them to sum up to 1.0 if their original sum > 0.
        total_input_weight = tfidf_weight + skill_match_weight
        if not (0.0 <= tfidf_weight <= 1.0 and 0.0 <= skill_match_weight <= 1.0):
             print("Warning: Initial scoring weights are invalid (must be 0-1). Using default weights (0.5 TFIDF, 0.5 Skill Match).")
             self.tfidf_weight = 0.5
             self.skill_match_weight = 0.5
             total_input_weight = 1.0 # Set total for normalization

        else:
             self.tfidf_weight = tfidf_weight
             self.skill_match_weight = skill_match_weight


        # Normalize weights to sum to 1.0 IF their positive sum is > 0
        # This ensures combined score is a weighted average out of 100
        if total_input_weight > 0:
             normalization_factor = 1.0 / total_input_weight
             self.tfidf_weight *= normalization_factor
             self.skill_match_weight *= normalization_factor
             # Print warning if weights were normalized due to sum != 1
             if abs(total_input_weight - 1.0) > 1e-6: # Check if sum was not close to 1.0
                  print(f"Warning: Initial scoring weights sum ({total_input_weight:.2f}) was not 1.0. Normalizing.")
                  print(f"  Adjusted weights: TFIDF={self.tfidf_weight:.2f}, Skill Match={self.skill_match_weight:.2f}")
        else: # Both weights were 0 or negative
             self.tfidf_weight = 0.0
             self.skill_match_weight = 0.0
             print("Warning: Both TFIDF and Skill Match weights are 0 or negative. Combined score will always be 0.")


        print("---------------------------------")


    def aggregate_and_format_scores(self, tfidf_raw_score: float, achieved_weighted_skill_score: float, total_possible_weighted_skill_score: float, matched_items: dict, missing_items: dict) -> dict:
        """
        Takes raw scores and item lists, calculates final scores using weights,
        and formats the output dictionary.

        Args:
            tfidf_raw_score (float): The raw TF-IDF similarity score (0.0 to 1.0).
            achieved_weighted_skill_score (float): Sum of weighted scores for matched skill items.
            total_possible_weighted_skill_score (float): Sum of base weights for all extracted JD items.
            matched_items (dict): Dictionary of matched items by label with details (from SkillComparer).
            missing_items (dict): Dictionary of missing item texts by label (from SkillComparer).

        Returns:
            dict: The final results dictionary including raw, weighted, and combined scores,
                  plus the filtered matched and missing items lists.
        """
        print("\n--- Aggregating and Formatting Scores ---")

        # --- Calculate Raw Skill Match Score ---
        skill_match_raw_score = 0.0
        if total_possible_weighted_skill_score > 0:
             skill_match_raw_score = achieved_weighted_skill_score / total_possible_weighted_skill_score
             # Clamp raw skill_match_score between 0 and 1
             skill_match_raw_score = max(0.0, min(1.0, skill_match_raw_score))
             print(f"Skill Match Raw Score: {achieved_weighted_skill_score:.4f} (Achieved) / {total_possible_weighted_skill_score:.4f} (Possible) = {skill_match_raw_score:.4f}")
        else: # If total possible is 0 (no weighted items in JD) or negative
             print("Warning: Total possible weighted skill score is 0 or negative. Raw skill match score is 0.")
             skill_match_raw_score = 0.0 # Ensure it's 0

        # Ensure TF-IDF raw score is also clamped 0-1 in case of unexpected inputs
        tfidf_raw_score = max(0.0, min(1.0, tfidf_raw_score))
        print(f"TF-IDF Score (raw): {tfidf_raw_score:.4f}")
        print(f"Skill Match Score (raw): {skill_match_raw_score:.4f}")


        # --- Apply Weights to Calculate Weighted Scores ---
        weighted_tfidf_score = tfidf_raw_score * self.tfidf_weight
        weighted_skill_match_score = skill_match_raw_score * self.skill_match_weight

        print(f"TF-IDF Score (weighted): {weighted_tfidf_score:.4f} ({self.tfidf_weight:.2f} weight)")
        print(f"Skill Match Score (weighted): {weighted_skill_match_score:.4f} ({self.skill_match_weight:.2f} weight)")


        # --- Calculate Combined Score ---
        combined_score = weighted_tfidf_score + weighted_skill_match_score
        # Clamp combined score between 0 and 1 (should be due to normalization, but defensive)
        combined_score = max(0.0, min(1.0, combined_score))
        print(f"Combined Score: {combined_score:.4f}")


        # --- Filter Matched and Missing Items (Remove empty categories) ---
        final_matched_items_filtered = {k: v for k, v in matched_items.items() if v}
        final_missing_items_filtered = {k: v for k, v in missing_items.items() if v}


        print("-------------------------------------------")

        # --- Prepare Final Results Dictionary ---
        return {
            # Return raw scores as well as weighted and combined
            "tfidf_score": float(tfidf_raw_score), # Raw TF-IDF
            "prioritized_skill_score": float(skill_match_raw_score), # Raw skill match
            "weighted_tfidf_score": float(weighted_tfidf_score), # Weighted TF-IDF
            "weighted_prioritized_skill_score": float(weighted_skill_match_score), # Weighted skill match
            "combined_score": float(combined_score), # Combined weighted score
            "matched_items": final_matched_items_filtered, # Filtered matched items
            "missing_items": final_missing_items_filtered # Filtered missing items
        }


# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":
    print("Running ScoreAggregator.py directly for testing.")

    # Define example weights for instantiation
    example_tfidf_weight = 0.3
    example_skill_weight = 0.7

    # Instantiate ScoreAggregator
    aggregator = ScoreAggregator(
        tfidf_weight=example_tfidf_weight,
        skill_match_weight=example_skill_weight
    )

    # Define example inputs (simulate outputs from TfidfScorer and SkillComparer)
    # These are example raw scores and item lists, not calculated here
    example_tfidf_raw_score = 0.55 # Example raw TF-IDF score
    example_achieved_weighted_skill_score = 10.5 # Example sum of weighted scores from SkillComparer
    example_total_possible_weighted_skill_score = 15.0 # Example total possible weighted score from SkillComparer

    # Example matched and missing items dictionary structure (from SkillComparer)
    example_matched_items = {
        "REQUIRED_SKILL_PHRASE": [
            {"text": "Required skill Python", "matched_in_sections": ["Skills", "Experience"], "achieved_weight": 1.5 * 1.5} # Base 1.5 * Section 1.5
        ],
        "CORE_SKILL": [
            {"text": "Flask", "matched_in_sections": ["Skills"], "achieved_weight": 1.0 * 1.0}, # Base 1.0 * Section 1.0
            {"text": "SQL", "matched_in_sections": ["Experience"], "achieved_weight": 1.0 * 1.5} # Base 1.0 * Section 1.5
        ]
    }

    example_missing_items = {
        "YEARS_EXPERIENCE": ["5 years of experience"],
        "REQUIRED_SKILL_PHRASE": ["Must have Java"]
    }


    # Aggregate and format the scores using the example inputs
    final_results = aggregator.aggregate_and_format_scores(
        tfidf_raw_score=example_tfidf_raw_score,
        achieved_weighted_skill_score=example_achieved_weighted_skill_score,
        total_possible_weighted_skill_score=example_total_possible_weighted_skill_score,
        matched_items=example_matched_items,
        missing_items=example_missing_items
    )

    # Print the final results dictionary
    print("\n--- Final Aggregated Results (Example) ---")
    import json
    print(json.dumps(final_results, indent=4))
    print("------------------------------------------")

    # Example with zero total possible weighted score for skill match
    print("\n--- Example with Zero Total Possible Weighted Score ---")
    final_results_zero_skill = aggregator.aggregate_and_format_scores(
        tfidf_raw_score=0.6, # Still have TF-IDF
        achieved_weighted_skill_score=0.0,
        total_possible_weighted_skill_score=0.0, # Zero possible
        matched_items={},
        missing_items={}
    )
    print(json.dumps(final_results_zero_skill, indent=4))
    print("-----------------------------------------------------")