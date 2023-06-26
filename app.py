import pymssql
import uuid
from copy import deepcopy
from flask import Flask, jsonify, request
import json
from decimal import Decimal
from datetime import datetime
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


app = Flask(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def connect_to_database(server, database, username, password):
    conn = pymssql.connect(server=server, database=database, user=username, password=password)
    cursor = conn.cursor()
    return conn, cursor


def fetch_data(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    result = cursor.fetchall()
    return result


def print_data(data, limit=10):
    for i, item in enumerate(data):
        if i == limit:
            break
        print(item)


def convert_data(data):
    converted_data = deepcopy(data)
    for item in converted_data:
        # Convert Decimal to float for 'Salary' key
        if 'Salary' in item:
            item['Salary'] = float(item['Salary'])

        if 'DesiredSalary' in item:
            item['DesiredSalary'] = int(item['DesiredSalary'])

        # Convert datetime to string for date keys
        date_keys = ['ScheduledAt', 'ExpiresAt', 'Created', 'Modified', 'CreatedBy']
        for key in date_keys:
            if key in item and item[key] is not None:
                item[key] = item[key].strftime('%Y-%m-%d %H:%M:%S')

    return converted_data

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


######## Populating database with jobs script below
def populate_job_data(conn1, cursor1):
    # Create an UUID for the job
    job_id = uuid.uuid4()

    # Assuming other values for the job post
    title = 'Backend Developer'
    description = 'Develop and maintain backend applications.'
    job_type = 'Part-Time'
    job_location = 'Remote'
    salary = 150000.00
    no_of_vocation = '1'
    required_skills = 'Python, Flask, Django'
    education_level = 'Bachelor in Computer Science'
    experience = '5 years'
    scheduled_at = '2023-07-01 09:00:00'
    expires_at = '2023-09-01 00:00:00'
    created_by = 'HR'
    created = '2023-06-25 10:00:00'
    modified_by = 'HR'
    modified = '2023-06-25 10:00:00'
    deleted = 0

    try:
        conn1.autocommit(True)
        cursor1.execute("""
            INSERT INTO JobPosts
            (Id, Title, Description, JobType, JobLocation, Salary, NoOfVocation, RequiredSkills, EducationLevel, Experience, ScheduledAt, ExpiresAt, CreatedBy, Created, ModifiedBy, Modified, Deleted)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            job_id, title, description, job_type, job_location, salary, no_of_vocation, required_skills,
            education_level,
            experience, scheduled_at, expires_at, created_by, created, modified_by, modified, deleted))
    except Exception as e:
        print("Error" + str(e))

    print("Data is inserted successfully at table JobPost")


def insert_individual_data(cursor):
    # Example usage
    gender = 1
    date_of_birth = '1946-06-14 00:00:00.0000000'
    resume = ''
    desired_salary = 180000
    job_preferences = 'Senior Frontend Developer'
    created_by = ''
    created = '2023-06-14 08:32:36.0000000'
    modified_by = ''
    modified = '2023-06-14 08:32:36.0000000'
    deleted = False

    individual_id = uuid.uuid4()

    try:
        cursor.execute("""
            INSERT INTO vefacom_ProWorkSocial.Individuals
            (Id, Gender, DateOfBirth, Resume, DesiredSalary, JobPreferences, CreatedBy, Created, ModifiedBy, Modified, Deleted)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (individual_id, gender, date_of_birth, resume, desired_salary, job_preferences, created_by, created,
              modified_by, modified, deleted))
        print("Data is inserted successfully at table Individuals!")
    except Exception as e:
        print("Error: " + str(e))


def fetch_individual_data(cursor, person_id):
    cursor.execute("""
        SELECT Id, Gender, DateOfBirth, Resume, DesiredSalary, JobPreferences
        FROM vefacom_ProWorkSocial.Individuals
        WHERE Id = %s
    """, (person_id,))
    result = cursor.fetchone()
    return result


def fetch_individual_skills_data(cursor, person_id):
    cursor.execute("""
        SELECT i.Id, i.Gender, i.DateOfBirth, i.Resume, i.DesiredSalary, i.JobPreferences, s.Description AS SkillDescription
        FROM vefacom_ProWorkSocial.Individuals AS i
        LEFT JOIN vefacom_ProWorkSocial.Skills AS s ON i.Id = s.IndividualId
        WHERE i.Id = %s
    """, (person_id,))
    result = cursor.fetchall()
    return result


@app.route('/recommend_jobs/<user_id>', methods=['GET'])
def recommend_jobs(user_id):
    # Connect to ProWork Social database
    server = '168.119.151.119\\MSSQLSERVER2016'
    database = 'ProWork-Social'
    username = 'vefacom_ProWorkSocial'
    password = 'K1~jvc204'
    conn, cursor = connect_to_database(server, database, username, password)

    # Connect to ProWork Jobs database
    server_jobs = '168.119.151.119\\MSSQLSERVER2016'
    database_jobs = 'ProWork-Jobs'
    username_jobs = 'vefacom_prowork'
    password_jobs = 'I95t$27le'
    conn1, cursor1 = connect_to_database(server_jobs, database_jobs, username_jobs, password_jobs)

    individuals_data = fetch_data(cursor, 'Individuals')

    query_result = fetch_individual_skills_data(cursor, user_id)
    skills = []
    for s in query_result:
        skills.append(s[6])


    ###skills set vs job posts

    # Fetch data from JobPosts table
    job_posts_data = fetch_data(cursor1, 'JobPosts')
    converted_job_posts_data = convert_data(job_posts_data)
    column_names = [
        'Id', 'Title', 'Description', 'JobType', 'JobLocation', 'Salary', 'NoOfVocation',
        'RequiredSkills', 'EducationLevel', 'Experience', 'ScheduledAt', 'ExpiresAt',
        'CreatedBy', 'Created', 'ModifiedBy', 'Modified', 'Deleted'
    ]

    # Create a list of dictionaries
    jobs_list = [dict(zip(column_names, row)) for row in converted_job_posts_data]

    # Compute cosine similarity for each job
    similarities = []
    for job in jobs_list:
        required_skills = job['RequiredSkills']
        required_skills_list = required_skills.split(', ')
        # Compute similarity between job skills and individual skills
        job_skills_vector = np.zeros(len(skills))
        individual_skills_vector = np.zeros(len(skills))
        for i, skill in enumerate(skills):
            if skill in required_skills_list:
                job_skills_vector[i] = 1
            individual_skills_vector[i] = 1
        similarity = cosine_similarity([job_skills_vector], [individual_skills_vector])[0][0]
        similarities.append(similarity)

    # Sort jobs based on similarity in descending order
    jobs_sorted = [job for _, job in sorted(zip(similarities, jobs_list), key=lambda x: x[0], reverse=True)]
    # Get the top 3 jobs with highest similarity
    top_jobs = jobs_sorted[:3]

    # Convert the result to JSON
    json_response = json.dumps(top_jobs, indent=4, cls=CustomJSONEncoder)

    # Print the JSON response
    print(json_response)
    return str(json_response)


def fetch_job_post(cursor, job_id):
    cursor.execute("""
        SELECT * FROM JobPosts WHERE Id = %s
    """, (job_id,))
    result = cursor.fetchone()
    return result


def fetch_candidates(cursor):
    cursor.execute("""
        SELECT i.Id, i.Gender, i.DateOfBirth, i.Resume, i.DesiredSalary, i.JobPreferences, s.Description AS SkillDescription
        FROM Individuals AS i
        LEFT JOIN Skills AS s ON i.Id = s.IndividualId
    """)
    result = cursor.fetchall()
    return result


@app.route('/recommend_candidates/<job_id>', methods=['GET'])
def recommend_candidates(job_id):
    # Connect to the database
    server = '168.119.151.119\\MSSQLSERVER2016'
    database = 'ProWork-Social'
    username = 'vefacom_ProWorkSocial'
    password = 'K1~jvc204'
    conn, cursor = connect_to_database(server, database, username, password)

    # Connect to ProWork Jobs database
    server_jobs = '168.119.151.119\\MSSQLSERVER2016'
    database_jobs = 'ProWork-Jobs'
    username_jobs = 'vefacom_prowork'
    password_jobs = 'I95t$27le'
    conn1, cursor1 = connect_to_database(server_jobs, database_jobs, username_jobs, password_jobs)

    # Fetch the job post
    job_post = fetch_job_post(cursor1, job_id)
    if not job_post:
        return jsonify({'error': 'Job post not found'}), 404

    # Fetch all candidates
    candidates = fetch_candidates(cursor)
    matched_candidates = []
    for candidate in candidates:
        skills = candidate[6]  # Assuming the skills are at index 6 in the candidate tuple
        # Assuming the required skills are at index 7 in the job_post tuple
        matched_candidates.append(candidate)

    # Sort candidates based on desired salary
    matched_candidates = sorted(matched_candidates, key=lambda x: x[4],
                                reverse=True)  # Assuming DesiredSalary is at index 4

    # Match candidates based on skills
    # matched_candidates = []
    # for candidate in candidates:
    #     skills = candidate['SkillDescription']
    #     if skills and job_post['RequiredSkills'] in skills:
    #         matched_candidates.append(candidate)
    #
    # # Sort candidates based on desired salary
    #
    # # Get the top 3 candidates
    top_candidates = matched_candidates[:3]
    #
    # # Convert candidates to JSON
    json_response = json.dumps(top_candidates, indent=4, default=str)
    #
    # # Close the database connection
    cursor.close()
    conn.close()
    cursor1.close()
    conn1.close()
    #
    return json_response

# Close database connections

if __name__ == '__main__':
    ##running the app
    app.run(debug=True)

    # cursor.close()
    # conn.close()
    # cursor1.close()
    # conn1.close()
