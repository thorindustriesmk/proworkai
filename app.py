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




def fetch_individual_data(cursor, person_id):
    cursor.execute("""
        SELECT Id, Gender, DateOfBirth, Resume, DesiredSalary, JobPreferences, CoverPicture
        FROM vefacom_ProWorkSocial.Individuals
        WHERE Id = %s
    """, (person_id,))
    result = cursor.fetchone()
    return result


def fetch_employee_data(cursor, employee_id):
    cursor.execute("""
        SELECT Id, FullName, Position, Department, Experience, Language, StartDate, EndDate, Salary, AvailableTempWork, Note
        FROM vefacom_ProWorkSocial.Employees
        WHERE Id = %s
    """, (employee_id,))
    result = cursor.fetchone()
    return result


def fetch_individual_skills_data(cursor, person_id):
    cursor.execute("""
        SELECT i.Id, i.Gender, i.DateOfBirth, i.Resume, i.DesiredSalary, i.JobPreferences, p.CoverPicture
        FROM vefacom_ProWorkSocial.Individuals AS i
        LEFT JOIN vefacom_ProWorkSocial.Profiles AS p ON i.Id = p.IndividualId
        WHERE i.Id = %s
    """, (person_id,))
    result = cursor.fetchall()
    return result


def fetch_profiles(cursor):
    cursor.execute("""
        SELECT Individuals.Id, Individuals.Gender, Individuals.DateOfBirth, Individuals.Resume, Individuals.DesiredSalary,
            Individuals.JobPreferences, Profiles.About, Profiles.WebsiteUrl,
            Profiles.ContactEmail, Profiles.ContactPhone, Profiles.SocialProfile
        FROM Individuals
        FULL JOIN Profiles ON Individuals.Id = Profiles.IndividualId
    """)
    candidates = cursor.fetchall()
    return candidates


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

    employee_data = fetch_employee_data(cursor, user_id)
    if employee_data:
        experience = employee_data['Experience']
        language = employee_data['Language']

    query_result = fetch_individual_skills_data(cursor, user_id)
    skills = []
    for s in query_result:
        skills.append(s[6])

    # Fetch data from JobPosts table
    job_posts_data = fetch_data(cursor1, 'JobPosts')
    converted_job_posts_data = convert_data(job_posts_data)
    column_names = [
        'Id', 'Title', 'Description', 'JobType', 'JobLocation', 'Salary', 'NoOfVocation',
        'RequiredSkills', 'EducationLevel', 'Experience', 'ScheduledAt', 'ExpiresAt',
        'CreatedBy', 'Created', 'ModifiedBy', 'Modified', 'Deleted', 'PostStatus'
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
        # Add more conditions here to consider experience, language, etc.
        similarities.append(similarity)

    # Sort jobs based on similarity in descending order
    jobs_sorted = [job for _, job in sorted(zip(similarities, jobs_list), key=lambda x: x[0], reverse=True)]
    # Get the top 3 jobs with highest similarity
    top_jobs = jobs_sorted[:5]

    # Append company information to the JSON response
    for job in top_jobs:
        company_id = job.get('CompanyId')  # Use get() method to safely retrieve the value
        if company_id:
            company_data = fetch_company_data(cursor, company_id)
            job['Company'] = company_data

    # Convert the result to JSON
    json_response = json.dumps(top_jobs, indent=4, cls=CustomJSONEncoder)

    # Convert the result to JSONd

    # Print the JSON response
    print(json_response)
    return str(json_response)


def fetch_company_data(cursor, company_id):
    cursor.execute("""
        SELECT *
        FROM vefacom_ProWorkSocial.Companies
        WHERE Id = %s
    """, (company_id,))
    result = cursor.fetchone()

    if result:
        # Extract the column names from the cursor description
        column_names = [desc[0] for desc in cursor.description]

        # Create a dictionary with column names as keys and corresponding values from the result
        company_data = dict(zip(column_names, result))

        return company_data
    else:
        return None


def fetch_job_post(cursor, job_id):
    cursor.execute("""
        SELECT * FROM JobPosts WHERE Id = %s
    """, (job_id,))
    result = cursor.fetchone()
    return result


def fetch_candidates(cursor):
    candidates = fetch_profiles(cursor)
    return candidates


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
    print(len(candidates[0]))
    matched_candidates = []
    for candidate in candidates:
        # Extract the desired columns from the candidate tuple
        individual_id = candidate[0]
        skills = candidate[3]
        profile_data = {
            'About': candidate[6],
            'WebsiteUrl': candidate[7],
            'ContactEmail': candidate[8],
            'ContactPhone': candidate[9],
            'SocialProfile': candidate[10]
        }
        desired_salary = candidate[4]

        # Create a candidate dictionary with the extracted data
        candidate_data = {
            'IndividualId': individual_id,
            'Skills': skills,
            'ProfileData': profile_data,
            'DesiredSalary': desired_salary
        }

        matched_candidates.append(candidate_data)

    # matched_candidates = sorted(matched_candidates, key=lambda x: x['DesiredSalary'], reverse=True)

    # Match candidates based on skills
    final_candidates = []
    for candidate in matched_candidates:
        skills = candidate['Skills']
        print(skills)
        print(str(candidate))
        if skills != None:
            final_candidates.append(candidate)
    # Sort candidates based on desired salary

    # Get the top 3 candidates
    top_candidates = final_candidates[:10]
    #
    # # Convert candidates to JSON
    json_response = json.dumps(matched_candidates, indent=4, default=str)
    #
    # # Close the database connection
    cursor.close()
    conn.close()
    cursor1.close()
    conn1.close()
    #
    return json_response


# Close database connections
@app.route('/', methods=['GET'])
def hello():
    return "Hello world"


if __name__ == '__main__':
    ##running the app
    print("The app has started")
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run(debug=True)
    print("App run function is invoked!")
    # cursor.close()
    # conn.close()
    # cursor1.close()
    # conn1.close()
