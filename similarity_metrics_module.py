import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords


def preprocess_text(text):
    # Preprocess text by removing stopwords and converting to lowercase
    stop_words = set(stopwords.words('english'))
    text = ' '.join([word.lower() for word in text.split() if word.lower() not in stop_words])
    return text


def calculate_similarity(job_skills, candidate_skills):
    # Preprocess job skills and candidate skills
    job_skills_processed = preprocess_text(job_skills)
    candidate_skills_processed = preprocess_text(candidate_skills)

    # Compute similarity metrics
    cosine_sim = cosine_similarity([job_skills_processed], [candidate_skills_processed])[0][0]

    # Enhancements for similarity metrics
    jaccard_sim = calculate_jaccard_similarity(job_skills_processed, candidate_skills_processed)
    dice_sim = calculate_dice_similarity(job_skills_processed, candidate_skills_processed)
    overlap_sim = calculate_overlap_similarity(job_skills_processed, candidate_skills_processed)
    tfidf_sim = calculate_tfidf_similarity(job_skills_processed, candidate_skills_processed)

    # Combine similarity scores
    similarity_scores = {
        'Cosine Similarity': cosine_sim,
        'Jaccard Similarity': jaccard_sim,
        'Dice Similarity': dice_sim,
        'Overlap Similarity': overlap_sim,
        'TF-IDF Similarity': tfidf_sim
    }

    return similarity_scores


def calculate_jaccard_similarity(text1, text2):
    # Calculate Jaccard similarity between two texts
    set1 = set(text1.split())
    set2 = set(text2.split())
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    jaccard_sim = intersection / union
    return jaccard_sim


def calculate_dice_similarity(text1, text2):
    # Calculate Dice similarity between two texts
    set1 = set(text1.split())
    set2 = set(text2.split())
    intersection = len(set1.intersection(set2))
    dice_sim = (2 * intersection) / (len(set1) + len(set2))
    return dice_sim


def calculate_overlap_similarity(text1, text2):
    # Calculate overlap similarity between two texts
    set1 = set(text1.split())
    set2 = set(text2.split())
    intersection = len(set1.intersection(set2))
    overlap_sim = intersection / min(len(set1), len(set2))
    return overlap_sim


def calculate_tfidf_similarity(text1, text2):
    # Calculate TF-IDF similarity between two texts
    corpus = [text1, text2]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    tfidf_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return tfidf_sim


# Example usage
job_skills = "Python, Flask, Django"
candidate_skills = "Python, Django, SQL, HTML, CSS"

similarity_scores = calculate_similarity(job_skills, candidate_skills)

for metric, score in similarity_scores.items():
    print(f"{metric}: {score}")
