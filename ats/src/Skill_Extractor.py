"""
Skill Extractor: Class and methods to extract skills.
Uses NLP librart spaCy to perform NER Named Entity Recognition
"""
import spacy
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher 

class SkillExtractor:

    def __init__(self, model_name: str = 'en_core_web_md'):
        """
        Initializes the skillextractor class by loading a spaCy model.
        @params model_name: str
        """
        try:
            # load the model
            self.nlp = spacy.load(model_name)
            print(f"spaCy model '{model_name}' loaded successfully.")
            # Initialize PhraseMatcher with spaCy vocab
            self.matcher = PhraseMatcher(self.nlp.vocab)
            self._add_skill_patterns()
        except OSError:
            print(f"spaCy model '{model_name}' not found.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # I model loading fails
            self.matcher = None

    def _add_skill_patterns(self):
        """
        adds common technical and soft skill phrases to PhraseMatcher.
        can be extended
        """
        skills_list = [
            "Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "Swift", "Kotlin","ES6"
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis","MsSQL", "cassandra", "Aurora", "Dynamo",
            "Flask", "Django", "FastAPI", "React", "Angular", "Vue.js", "Node.js", "Express.js",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Terraform",
            "Agile", "Scrum", "Kanban", "CI/CD", "Unit Testing", "Integration Testing",
            "Machine Learning", "Data Science", "Computer Vision", "NLP","ML","Deep Learning","CNN", "Neural Network",
            "OpenCV",
            "Problem Solving", "Communication Skills", "Teamwork", "Leadership", "Focus", "Discipline"
        ]
        # convert list of strings to sapCy Doc objects
        patterns = [self.nlp.make_doc(skill) for skill in skills_list]
        # Add patterns to the matcher
        self.matcher.add("SKILL", patterns)
    
    def extract_skills(self, text: str) -> list[str]:
        """
        Process text using spaCy to extract potential skill entities.
        extracts named entities (NER) and significant nouns/proper nouns.
        @params text:str # input text: job description or resume_text
        @returns list<str> # list of extracted entities that represent skills.
        """
        if self.nlp is None or self.matcher is None:
            print("spaCy model ior matcher not loaded. Cannot extract skills.")
            return[]

        doc = self.nlp(text)

        # use PhraseMatcher to find predefined skills --
        matches = self.matcher(doc)
        matched_skills = [doc[start:end].text for match_id, start, end in matches]
        
        # - clean and deduplicate --
        all_extracted = matched_skills
        # convert to lowercase and remove lead/trail whitespaces.
        cleaned_items = [item.lower().strip() for item in all_extracted]
        # Remove duplicates by converting to a SET and then back to LIST
        unique_skills = list(set(cleaned_items))

        return unique_skills

# --- Example Usage (Optional, for testing the module directly) ---
if __name__ == "__main__":        
    print("Running skill_extractor.py directly for testing.")

    # Instantiate the extractor
    # Make sure you have downloaded the 'en_core_web_sm' model
    skill_extractor = SkillExtractor(model_name='en_core_web_md')

    job_description_text = """
    We are looking for a highly motivated Software Engineer with 3+ years of experience
    in Python development. Experience with web frameworks like Flask or FastAPI is
    required. Knowledge of databases, SQL, and cloud platforms (AWS, Azure, or GCP)
    is a strong plus. Must have experience with unit testing and version control
    (Git). Excellent communication and problem-solving skills are essential.
    """

    resume_text = """
    Highly motivated Software Engineer with 4 years of experience in developing
    web applications using Python and Flask. Proficient in SQL database design
    and management. Experienced with AWS services and Git version control.
    Strong problem-solving skills. Skills: Python, JavaScript, Flask, SQL, AWS, Git, Docker.
    """

    # Extract skills
    jd_skills = skill_extractor.extract_skills(job_description_text)
    resume_skills = skill_extractor.extract_skills(resume_text)

    print("\nExtracted JD Skills/Entities:")
    print(jd_skills)

    print("\nExtracted Resume Skills/Entities:")
    print(resume_skills)