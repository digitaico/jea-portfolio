# /mnt/disc2/local-code/jea-portfolio/ats/src/skill_comparer.py

import logging
import spacy
from spacy.matcher import Matcher

logger = logging.getLogger(__name__)

class SkillComparer:
    def __init__(self, skill_extractor, resume_parser, requirement_weights, section_weights):
        logger.info("\n--- SkillComparer Initialization ---")
        self.skill_extractor = skill_extractor
        self.resume_parser = resume_parser # Retain if needed for future methods or for consistency
        # Ensure weights are floats when loaded from config
        self.requirement_weights = {k: float(v) for k, v in requirement_weights.items()} if requirement_weights else {} 
        self.section_weights = {k: float(v) for k, v in section_weights.items()} if section_weights else {} 
        logger.info("SkillComparer initialized.")
        logger.info("------------------------------------")

    def compare_skills(self, jd_text: str, resume_text: str):
        logger.info("SkillComparer: Starting skill comparison...")

        # 1. Extract skills from JD
        logger.info("SkillComparer: Extracting skills from Job Description...")
        jd_extracted_items = self.skill_extractor.extract_skills(jd_text, is_jd=True)
        logger.info(f"SkillComparer: Extracted {len(jd_extracted_items)} items from JD.")

        # 2. Extract skills from Resume
        logger.info("SkillComparer: Extracting skills from Resume...")
        resume_extracted_items = self.skill_extractor.extract_skills(resume_text, is_jd=False)
        logger.info(f"SkillComparer: Extracted {len(resume_extracted_items)} items from Resume.")

        # Convert resume extracted items to a set for efficient lookup
        # Use the 'cleaned_text' for comparison as this is what's likely normalized
        flattened_resume_items_set = {item['cleaned_text'] for item in resume_extracted_items if item.get('cleaned_text')}
        logger.debug(f"SkillComparer DEBUG: Flattened Resume Items (Text Only Set): {flattened_resume_items_set}")

        matched_items = []
        missing_items = []
        achieved_weighted_score = 0.0
        total_possible_weighted_score = 0.0
        skill_match_raw_score = 0 # Initialize as int, will be converted to float upon return

        logger.info("SkillComparer: Comparing JD extracted items to Resume extracted items for scoring...")
        for jd_item in jd_extracted_items:
            label = jd_item['label']
            cleaned_jd_text = jd_item['cleaned_text']
            original_jd_text = jd_item['text']

            # Retrieve the base weight for the skill label (e.g., REQUIRED_SKILL_PHRASE, YEARS_EXPERIENCE)
            # Ensure these weights are numeric (float) as they are stored as such in __init__
            base_weight = self.requirement_weights.get(label, 1.0) 

            # Add to total possible score for this item, weighted by its requirement type
            total_possible_weighted_score += base_weight 

            logger.debug(f"SkillComparer DEBUG: Checking JD item '{original_jd_text}' (Label: {label}, Cleaned: '{cleaned_jd_text}')...")
            logger.debug(f"SkillComparer DEBUG:   - Added base weight {base_weight:.2f} to total possible score. Total Possible: {total_possible_weighted_score:.2f}")

            if cleaned_jd_text in flattened_resume_items_set:
                logger.debug(f"SkillComparer DEBUG:   -> '{cleaned_jd_text}' FOUND in flattened Resume set.")
                matched_items.append({
                    'label': label,
                    'original_jd_text': original_jd_text,
                    'cleaned_jd_text': cleaned_jd_text,
                    'weight': base_weight
                })
                # Add to achieved score, weighted
                achieved_weighted_score += base_weight
                skill_match_raw_score += 1 # Increment raw score
            else:
                logger.debug(f"SkillComparer DEBUG:   -> '{cleaned_jd_text}' NOT found in flattened Resume set.")
                missing_items.append({
                    'label': label,
                    'original_jd_text': original_jd_text,
                    'cleaned_jd_text': cleaned_jd_text,
                    'weight': base_weight # Include weight for potential use in missing items analysis
                })
            logger.debug("--------------------")

        logger.info("SkillComparer: Skill comparison completed.")
        logger.info(f"SkillComparer: Achieved Weighted Score: {achieved_weighted_score:.4f}")
        logger.info(f"SkillComparer: Total Possible Weighted Score: {total_possible_weighted_score:.4f}")
        logger.info(f"SkillComparer: Matched Items Count: {len(matched_items)}")
        logger.info(f"SkillComparer: Missing Items Count: {len(missing_items)}")

        # Explicitly ensure all scores are floats before returning
        return (
            float(skill_match_raw_score),
            float(achieved_weighted_score),
            float(total_possible_weighted_score),
            matched_items,
            missing_items
        )