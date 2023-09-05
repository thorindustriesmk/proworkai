import pymssql
import uuid
from flask import Flask, jsonify, request
import json
from decimal import Decimal
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

app.config['DB_SERVER'] = '168.119.151.119\\MSSQLSERVER2016'

# ProWork Social database configurations
app.config['DB_USERNAME_SOCIAL'] = 'vefacom_ProWorkSocial'
app.config['DB_PASSWORD_SOCIAL'] = 'K1~jvc204'
app.config['DB_SOCIAL'] = 'ProWork-Social'

# ProWork Jobs database configurations
app.config['DB_USERNAME_JOBS'] = 'vefacom_prowork'
app.config['DB_PASSWORD_JOBS'] = 'I95t$27le'
app.config['DB_JOBS'] = 'ProWork-Jobs'

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def connect_to_database(database, username, password):
    conn = pymssql.connect(server=app.config['DB_SERVER'], database=database,
                           user=username, password=password)
    cursor = conn.cursor(as_dict=True)  # Return results as dictionary
    return conn, cursor


@app.route('/recommend_jobs/<user_id>', methods=['GET'])
def recommend_jobs(user_id):
    conn_social, cursor_social = connect_to_database(app.config['DB_SOCIAL'], app.config['DB_USERNAME_SOCIAL'], app.config['DB_PASSWORD_SOCIAL'])
    conn_jobs, cursor_jobs = connect_to_database(app.config['DB_JOBS'], app.config['DB_USERNAME_JOBS'], app.config['DB_PASSWORD_JOBS'])

    try:
        # Fetch individual's data, skills, work experiences, and education
        individual_data = fetch_individual_data(cursor_social, user_id)
        individual_skills = fetch_individual_skills(cursor_social, user_id)
        individual_work_experiences = fetch_individual_work_experiences(cursor_social, user_id)
        individual_educations = fetch_individual_educations(cursor_social, user_id)

        # Fetch all job posts
        job_posts = fetch_all_job_posts(cursor_jobs)

        # Compute similarity scores based on skills, work experiences, and education
        scores = compute_similarity_scores(individual_skills, job_posts)

        # Sort job posts based on scores and return the top ones
        recommended_jobs = sort_and_filter_jobs(job_posts, scores)

        return jsonify(recommended_jobs)

    finally:
        cursor_social.close()
        conn_social.close()
        cursor_jobs.close()
        conn_jobs.close()


@app.route('/recommend_candidates/<job_id>', methods=['GET'])
def recommend_candidates(job_id):
    conn_social, cursor_social = connect_to_database(app.config['DB_SOCIAL'], app.config['DB_USERNAME_SOCIAL'], app.config['DB_PASSWORD_SOCIAL'])
    conn_jobs, cursor_jobs = connect_to_database(app.config['DB_JOBS'], app.config['DB_USERNAME_JOBS'], app.config['DB_PASSWORD_JOBS'])

    try:
        # Fetch job post data, required skills, and other criteria
        job_post = fetch_job_post(cursor_jobs, job_id)

        # Fetch all candidates' data, skills, work experiences, and education
        candidates = fetch_all_candidates(cursor_social)

        # Compute similarity scores based on skills, work experiences, and education
        scores = compute_similarity_scores_for_candidates(job_post, candidates)

        # Sort candidates based on scores and return the top ones
        recommended_candidates = sort_and_filter_candidates(candidates, scores)

        return jsonify(recommended_candidates)

    finally:
        cursor_social.close()
        conn_social.close()
        cursor_jobs.close()
        conn_jobs.close()


# Utility functions for fetching data and computing similarity scores

def fetch_individual_data(cursor, user_id):
    # Fetch individual data based on user_id
    cursor.execute("SELECT * FROM Individuals WHERE Id = %s", (user_id,))
    return cursor.fetchone()


def fetch_individual_skills(cursor, user_id):
    # Fetch skills of the individual based on user_id
    cursor.execute("SELECT SkillId FROM SkillEvaluations WHERE IndividualId = %s", (user_id,))
    return [row['SkillId'] for row in cursor.fetchall()]


def fetch_individual_work_experiences(cursor, user_id):
    # Fetch work experiences of the individual based on user_id
    cursor.execute("SELECT * FROM WorkExperiences WHERE IndividualId = %s", (user_id,))
    return cursor.fetchall()


def fetch_individual_educations(cursor, user_id):
    # Fetch education details of the individual based on user_id
    cursor.execute("SELECT * FROM Educations WHERE IndividualId = %s", (user_id,))
    return cursor.fetchall()


def fetch_all_job_posts(cursor):
    # Fetch all job posts
    cursor.execute("SELECT * FROM JobPosts")
    return cursor.fetchall()


def compute_similarity_scores(individual_skills, job_posts):
    # Compute similarity scores based on skills and other criteria
    # Placeholder logic
    scores = []
    for job in job_posts:
        required_skills = job['RequiredSkills'].split(', ')
        matching_skills = set(individual_skills).intersection(set(required_skills))
        scores.append(len(matching_skills))
    return scores


def sort_and_filter_jobs(job_posts, scores):
    # Sort job posts based on scores and return the top ones
    sorted_jobs = [job for _, job in sorted(zip(scores, job_posts), key=lambda pair: pair[0], reverse=True)]
    return sorted_jobs[:5]


def fetch_all_candidates(cursor):
    # Fetch all candidates' data, skills, work experiences, and education
    cursor.execute("SELECT * FROM Individuals")
    return cursor.fetchall()


def compute_similarity_scores_for_candidates(job_post, candidates):
    # Compute similarity scores for candidates based on job post criteria
    # Placeholder logic
    required_skills = job_post['RequiredSkills'].split(', ')
    scores = []
    for candidate in candidates:
        candidate_skills = fetch_individual_skills(cursor, candidate['Id'])
        matching_skills = set(candidate_skills).intersection(set(required_skills))
        scores.append(len(matching_skills))
    return scores


def sort_and_filter_candidates(candidates, scores):
    # Sort candidates based on scores and return the top ones
    sorted_candidates = [candidate for _, candidate in sorted(zip(scores, candidates), key=lambda pair: pair[0], reverse=True)]
    return sorted_candidates[:10]


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
