import PyPDF2
import spacy
from spacy.matcher import Matcher

# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file_path):
    # Open the PDF file in binary mode
    with open(file_path, "rb") as file:
        # Initialize a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        # Extract the text from each page of the PDF
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def parse_resume(resume_text):
    # Create a spaCy Doc object by applying the spaCy model to the resume text
    doc = nlp(resume_text)

    # Initialize the Matcher
    matcher = Matcher(nlp.vocab)

    # Define pattern for matching phone numbers
    phone_pattern = [{"ORTH": {"REGEX": r"\d{3}"}}, {"ORTH": "-"}, {"ORTH": {"REGEX": r"\d{3}"}}, {"ORTH": "-"}, {"ORTH": {"REGEX": r"\d{4}"}}]

    # Define pattern for matching URLs
    url_pattern = [{"LIKE_URL": True}]

    # Add the patterns to the Matcher
    matcher.add("PHONE_PATTERN", None, phone_pattern)
    matcher.add("URL_PATTERN", None, url_pattern)

    # Extract candidate's name
    candidate_name = None
    for entity in doc.ents:
        if entity.label_ == "PERSON":
            candidate_name = entity.text
            break

    # Extract candidate's email
    candidate_email = None
    for token in doc:
        if token.like_email:
            candidate_email = token.text
            break

    # Extract candidate's phone number
    candidate_phone = None
    matches = matcher(doc)
    for match_id, start, end in matches:
        if nlp.vocab.strings[match_id] == "PHONE_PATTERN":
            candidate_phone = doc[start:end].text
            break

    # Extract candidate's skills
    candidate_skills = []
    for chunk in doc.noun_chunks:
        if "skill" in chunk.text.lower():
            candidate_skills.append(chunk.text)

    # Extract candidate's education
    candidate_education = []
    for ent in doc.ents:
        if ent.label_ == "EDUCATION":
            candidate_education.append(ent.text)

    # Extract candidate's work experience
    candidate_experience = []
    for ent in doc.ents:
        if ent.label_ == "WORK":
            candidate_experience.append(ent.text)

    # Extract candidate's projects
    candidate_projects = []
    for ent in doc.ents:
        if ent.label_ == "PROJECT":
            candidate_projects.append(ent.text)

    # Extract candidate's certifications
    candidate_certifications = []
    for ent in doc.ents:
        if ent.label_ == "CERTIFICATION":
            candidate_certifications.append(ent.text)

    # Extract candidate's languages
    candidate_languages = []
    for ent in doc.ents:
        if ent.label_ == "LANGUAGE":
            candidate_languages.append(ent.text)

    # Extract candidate's interests
    candidate_interests = []
    for ent in doc.ents:
        if ent.label_ == "INTEREST":
            candidate_interests.append(ent.text)

    # Return the extracted information
    return {
        "name": candidate_name,
        "email": candidate_email,
        "phone": candidate_phone,
        "skills": candidate_skills,
        "education": candidate_education,
        "experience": candidate_experience,
        "projects": candidate_projects,
        "certifications": candidate_certifications,
        "languages": candidate_languages,
        "interests": candidate_interests
    }

# Specify the path to your PDF resume
pdf_path = "test.pdf"

# Extract text from the PDF
resume_text = extract_text_from_pdf(pdf_path)

# Parse the resume
parsed_data = parse_resume(resume_text)

# Print the extracted information
print("Candidate Name:", parsed_data["name"])
print("Candidate Email:", parsed_data["email"])
print("Candidate Phone:", parsed_data["phone"])
print("Candidate Skills:", parsed_data["skills"])
print("Candidate Education:", parsed_data["education"])
print("Candidate Experience:", parsed_data["experience"])
print("Candidate Projects:", parsed_data["projects"])
print("Candidate Certifications:", parsed_data["certifications"])
print("Candidate Languages:", parsed_data["languages"])
print("Candidate Interests:", parsed_data["interests"])
