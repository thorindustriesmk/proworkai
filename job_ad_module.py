import spacy
from spacy.matcher import Matcher
import PyPDF2

# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file_path):
    # Open the PDF file in read binary mode
    with open(file_path, "rb") as file:
        # Initialize a PDF file reader object
        pdf_reader = PyPDF2.PdfFileReader(file)
        # Extract text from each page of the PDF
        text = ""
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            text += page.extractText()
    return text

def parse_job_ad(job_ad_text):
    # Create a spaCy Doc object by applying the spaCy model to the job ad text
    doc = nlp(job_ad_text)

    # Initialize the Matcher
    matcher = Matcher(nlp.vocab)

    # Define patterns for matching job titles, required skills, and qualifications
    job_title_pattern = [{"POS": "NOUN"}, {"POS": "NOUN", "OP": "*"}]
    required_skills_pattern = [{"LOWER": {"IN": ["experience", "skills", "knowledge", "requirements"]}}, {"OP": "*"}, {"POS": "NOUN"}, {"POS": "NOUN", "OP": "*"}]
    qualifications_pattern = [{"LOWER": {"IN": ["qualification", "degree", "education", "certification", "experience"]}}, {"OP": "*"}, {"POS": "NOUN"}, {"POS": "NOUN", "OP": "*"}]

    # Add the patterns to the Matcher
    matcher.add("JOB_TITLE_PATTERN", None, job_title_pattern)
    matcher.add("REQUIRED_SKILLS_PATTERN", None, required_skills_pattern)
    matcher.add("QUALIFICATIONS_PATTERN", None, qualifications_pattern)

    # Extract job title
    job_title = None
    matches = matcher(doc)
    for match_id, start, end in matches:
        if nlp.vocab.strings[match_id] == "JOB_TITLE_PATTERN":
            job_title = doc[start:end].text
            break

    # Extract required skills
    required_skills = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        if nlp.vocab.strings[match_id] == "REQUIRED_SKILLS_PATTERN":
            required_skills.append(doc[start:end].text)

    # Extract qualifications
    qualifications = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        if nlp.vocab.strings[match_id] == "QUALIFICATIONS_PATTERN":
            qualifications.append(doc[start:end].text)

    # Return the extracted information
    return {
        "job_title": job_title,
        "required_skills": required_skills,
        "qualifications": qualifications
    }

# PDF file path
file_path = "test_job_ad.pdf"

# Extract text from the PDF file
job_ad_text = extract_text_from_pdf(file_path)

# Parse the job advertisement
parsed_data = parse_job_ad(job_ad_text)

# Print the extracted information
print("Job Title:", parsed_data["job_title"])
print("Required Skills:", parsed_data["required_skills"])
print("Qualifications:", parsed_data["qualifications"])
