## Applicant Tracking System

This app is intended to be used only by job applicants, not hiring companies.
Hence, its purpose is just to compare a given job listing with a parsed resume and deliver an assessment of job seeker cv.
No search, no filtering. 


#### Functionality

- Extract data from documents -resumes which comes in formats like `pdf` and `docx`. Use python libraries to read docs and 
pdf-
- Compare extracted keywords from applicant cv with job description keywords.  Use `distance` algos to estimate similarity.
- Rank. Based on keyword similarity, assess an score.
- UI. A UI is required to allow applicants to upload cv and to parse or paste job listing URL.
Here consider that not all job listings can be read -scrapped.  For version 1 consider allowing applicant to copy and paste 
job description.
- If allowed pasting text, consider security, that is escaping text.


#### Workflow

Input Job description .-> Data Extraction -> keyword Matching -> Score
                      |
Upload CV document ---'

#### Stack

- Python
- NLTK
- Scikit-Learn
- Flask to expose python API
- Nodejs to run UI
- `TF-IDF` to convert text to vector
- `Cosine Similarity` to score similarity between two vectors

#### Parameters and return
@param Job Description: str # Copy Job description from job listing
@param language: str # Language of resume and job description
@param Resume: Document # a PDF or DOCX document to be read
@returns Similarity Score: number # a 0 - 100 score that assess resume similarity with job description. 

### Changelog

#### v1.0.0 
- Score based on word frequency and similarity.
- Score is calculated by comparing and estimating similarity between two vectors.  TF-IDF and Cosine Similarity.
- Primitive HTML, CSS User interface.

#### v2.0.0
- Score based on `understanding` the meaning of certain terms as skills.
- App named JEMATS.
- Use of NLP.
    By using Skill and Entity Extraction we can pull named entities like `Skills`, `Technologies`, `Qualifications`, `Job 
    Titles`, `Companies`, among others. Hence we can prioritize matches by customizing weights.

#### v3.0.0
- Use spaCy advanced Matcher to find patterns that indicate required skills, experience levels or qualifications.
- Represent nature of job description requirements - optional, -required.
- Score will penalize the absence of required skills and experience.
