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
