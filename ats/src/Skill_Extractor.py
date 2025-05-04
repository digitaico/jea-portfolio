"""
Skill Extractor: Class and methods to extract skills.
Uses NLP librart spaCy to perform NER Named Entity Recognition
"""
import spacy
from spacy.matcher import Matcher
#from spacy.matcher import PhraseMatcher 

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
            # Initialize Matcher with spaCy vocab
            self.matcher = Matcher(self.nlp.vocab)
            self._add_requirement_patterns()
        except OSError:
            print(f"spaCy model '{model_name}' not found.")
            print(f"Please download it using: python -m spacy download {model_name}")
            self.nlp = None # I model loading fails
            self.matcher = None

    def _add_requirement_patterns(self):
        """
        adds patterns to the Matcher to identify requirements, experience ...
        these patterns are examples and should be expanded, refined.
        """
        # Pattern for "required" [skill/experience/qualification]
        pattern_required_skill = [{"LOWER": "required"}, {"POS":{"IN": ["NOUN", "PROPN"]}, "OP":"+"}]
        # Pattern for "must have" [skill/experience/qualification]
        pattern_must_have = [{"LOWER": "must"}, {"LOWER": "have"},{"POS":{"IN": ["NOUN", "PROPN"]}, "OP":"+"}]
        # Pattern for "X+ years of experience in [skill/field]"
        pattern_years_experience = [{"POS":"NUM", "OP":"+"}, {"LOWER": "+", "OP":"?"}, {"LOWER": "years"}, {"LOWER": "of"}, 
                                    {"LOWER": "experience"}, {"LOWER": "in"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}]
        # Pattern for "knowledge of [skill/technology]"
        pattern_knowledge_of = [{"LOWER": "knowledge"}, {"LOWER": "of"}, {"POS": {"IN": ["NOUN", "PROPN", "ADJ"]}, "OP": "+"}] # e.g., "knowledge of AWS", "knowledge of Machine Learning"
            
        # Pattern for Bachelor's/Master's degree
        pattern_degree = [{"POS": "NOUN", "REGEX": "[Bb]achelor's|[Mm]aster's"}, {"LOWER": "degree"}, {"LOWER": "in", "OP": "?"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}] # e.g., "Bachelor's degree in Computer Science"

        # Add patterns to the matcher with labels
        self.matcher.add("REQUIRED_SKILL_PHRASE", [pattern_required_skill, pattern_must_have])
        self.matcher.add("YEARS_EXPERIENCE", [pattern_years_experience])
        self.matcher.add("KNOWLEDGE_OF", [pattern_knowledge_of])
        self.matcher.add("QUALIFICATION_DEGREE", [pattern_degree])

        """ PhraseMatcher
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
        """
    
    def extract_requirements_and_skills(self, text: str) -> dict:
        """
        Process text and extracts requirements and potencial skills using Matcher patterns.
        @params text:str # input text: job description or resume_text
        @returns dict # dictionary contains extracted items categorized by pattern label.
        e.g: {"REQUIRED_SKILL_PHRASE": ["must have Python", ....], "SKILL_PYTHON": ["python", ...]}
        """
        if self.nlp is None or self.matcher is None:
            print("spaCy model or matcher not loaded. Cannot extract requirements.")
            return{}

        doc = self.nlp(text)

        # use PhraseMatcher to find predefined skills --
        matches = self.matcher(doc)

        extracted_items = {}

        for match_id, start, end in matches:
            span = doc[start:end] # matched span of text
            label = self.nlp.vocab.strings[match_id]  # get string label for match_id

            if label not in extracted_items:
                extracted_items[label] = []

            extracted_items[label].append(span.text)

        # - clean and deduplicate --
        cleaned_categorized_items = {}
        for label, items in extracted_items.items():
            cleaned_items = [item.lower().strip() for item in items]
            unique_items = list(set(cleaned_items))
            cleaned_categorized_items[label] = unique_items

        return cleaned_categorized_items
    