import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


nltk.download('punkt')
nltk.download('stopwords')


job_ads = pd.read_csv('job_ads.csv')
resumes = pd.read_csv('resumes.csv')


def preprocess_text(text):
    # Check if the input is a string
    if not isinstance(text, str):
        return ""

    # Lowercase the text
    text = text.lower()

    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Tokenize the text
    words = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # Join words back into a single string
    preprocessed_text = " ".join(words)

    return preprocessed_text


def compute_similarity(job_ads, resume_text):
    tfidf_vectorizer = TfidfVectorizer()

    # Combine job ad and resume texts
    combined_texts = job_ads['preprocessed_description'].tolist() + [resume_text]

    # Compute the TF-IDF matrix
    tfidf_matrix = tfidf_vectorizer.fit_transform(combined_texts)

    # Compute cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    return similarity_matrix


job_ads['preprocessed_description'] = job_ads['description'].apply(preprocess_text)
resumes['preprocessed_resume'] = resumes['resume'].apply(preprocess_text)

st.title('Thor Job Recommender System')

# Allow the user to upload their resume
uploaded_file = st.file_uploader('Upload your resume (in .txt format):', type=['txt'])

if uploaded_file is not None:
    resume_text = uploaded_file.read().decode('utf-8')

    # Preprocess the uploaded resume text
    preprocessed_resume_text = preprocess_text(resume_text)
    st.warning("With the following resume:")
    st.write(resume_text)
    # Compute similarity
    similarity_matrix = compute_similarity(job_ads, preprocessed_resume_text)

    # Get the similarity scores for the uploaded resume
    resume_similarity_scores = similarity_matrix[-1][:-1]

    # Rank the job ads based on similarity scores
    job_ads['similarity_score'] = resume_similarity_scores
    job_ads_sorted = job_ads.sort_values(by='similarity_score', ascending=False)

    # Display the top job recommendations
    st.success('Top Job Recommendations:')
    st.write(job_ads_sorted[['job_title', 'similarity_score']].head(10))
