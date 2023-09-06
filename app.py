import pymssql
import uuid
from flask import Flask, jsonify, request
import json
from decimal import Decimal
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from copy import deepcopy
from gensim.models import KeyedVectors
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)

# Configuration
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
    # Connect to ProWork Social database
    conn_social, cursor_social = connect_to_database(
        app.config['DB_SOCIAL'],
        app.config['DB_USERNAME_SOCIAL'], app.config['DB_PASSWORD_SOCIAL']
    )

    # Connect to ProWork Jobs database
    conn_jobs, cursor_jobs = connect_to_database(
        app.config['DB_JOBS'],
        app.config['DB_USERNAME_JOBS'], app.config['DB_PASSWORD_JOBS']
    )

    # Fetch individual's skills
    individual_data = fetch_individual_data(cursor_social, user_id)
    print("These are the individual data:" + str(individual_data))

    if individual_data:
        skills = fetch_individual_skills(cursor_social, user_id)
        if len(skills):
            print("The individual has not provided data about skills!")
        only_skills = [s['description'] for s in skills]
        work_experiences = fetch_individual_work_experiences(cursor_social, user_id)
        educations = fetch_individual_educations(cursor_social, user_id)
    else:
        return "There are no data for this individual!"
    # Fetch data from JobPosts table

    print("Individuals" + str(individual_data))
    print("skills" + str(skills))
    print("work_experiences" + str(work_experiences))
    print("educations" + str(educations))

    job_posts_data = fetch_data(cursor_jobs, 'JobPosts')
    converted_job_posts_data = convert_data(job_posts_data)
    print(type(converted_job_posts_data))
    # print("All jobs converted are" + str(converted_job_posts_data))
    exclude_keys = ['Id', 'Created', 'ModifiedBy', 'Modified', 'Deleted', 'PostStatus', 'CompanyId', 'ScheduledAt',
                    'ExpiresAt', 'CreatedBy']
    # Parse the data to exclude the specified keys
    all_job_data = [{k: v for k, v in item.items() if k not in exclude_keys} for item in converted_job_posts_data]
    # print("Data new:" + str(all_job_data))

    # Fetch individual's job preferences and work experiences
    job_preferences = individual_data['JobPreferences'] if individual_data['JobPreferences'] else ""
    job_titles = [exp['job_title'] for exp in work_experiences if exp['job_title']]
    print("job_preferences " + str(job_preferences))
    print("job_titles " + str(job_titles))
    combined_strings = [job_preferences] + job_titles
    print("combined_strings " + str(combined_strings))
    combined_strings = [str(s).lower() for s in combined_strings if s and s.strip()]
    if len(combined_strings) == 0:
        return "The value of combined string is 0!"

    filtered_job_posts = [job for job in converted_job_posts_data if job.get('Title') and job.get('RequiredSkills')]

    filtered_job_titles = [job['Title'] for job in filtered_job_posts]
    filtered_job_skills = [job['RequiredSkills'] for job in filtered_job_posts]

    # Compute cosine similarity for job titles/preferences
    cosine_similarities_titles = compute_cosine_similarity([combined_strings[0]], filtered_job_titles)

    # Compute cosine similarity for skills
    individual_skills_string = ' '.join(only_skills)
    cosine_similarities_skills = compute_cosine_similarity([individual_skills_string], filtered_job_skills)

    ##design the weighted sum
    alpha = 0.5  # You can adjust this value based on how much weight you want to give to titles vs skills
    weighted_similarities = alpha * cosine_similarities_titles + (1 - alpha) * cosine_similarities_skills

    # Sort jobs based on similarity in descending order
    # jobs_sorted = [job_title_to_data[job_title] for _, job_title in sorted(zip(cosine_similarities_titles, job_titles_for_vectorizer), key=lambda x: x[0], reverse=True)]
    jobs_sorted = [job for _, job in sorted(zip(weighted_similarities, filtered_job_posts), key=lambda x: x[0], reverse=True)]

    top_jobs = jobs_sorted[:5]

    # Append company information to the JSON response
    for job in top_jobs:
        company_id = job.get('CompanyId')  # Use get() method to safely retrieve the value
        print("Company id is:" + str(company_id))
        if company_id:
            company_data = fetch_company_data(cursor_social, company_id)
            job['Company'] = company_data

    # Convert the result to JSON
    json_response = json.dumps(top_jobs, indent=4, cls=CustomJSONEncoder)

    # Close the database connections
    cursor_social.close()
    conn_social.close()
    cursor_jobs.close()
    conn_jobs.close()

    return json_response


@app.route('/recommend_candidates/<job_id>', methods=['GET'])
def recommend_candidates(job_id):
    conn_social, cursor_social = connect_to_database(app.config['DB_SOCIAL'], app.config['DB_USERNAME_SOCIAL'],
                                                     app.config['DB_PASSWORD_SOCIAL'])
    conn_jobs, cursor_jobs = connect_to_database(app.config['DB_JOBS'], app.config['DB_USERNAME_JOBS'],
                                                 app.config['DB_PASSWORD_JOBS'])

    try:
        # 1. Fetch the specific job post based on job_id
        job_post = fetch_job_post(cursor_jobs, job_id)

        # 2. Extract the required skills from the job post
        required_skills_string = job_post['RequiredSkills']
        print("The required skills for the job are:" + str(required_skills_string))
        # 3. Fetch all candidates' data and their skills
        candidates = fetch_all_candidates(cursor_social)
        candidates_skills = []
        valid_candidates = []  # List to store candidates with valid skills

        for candidate in candidates:
            candidate_id = candidate['Id']
            print("Candidate it" + str(candidate_id))

            candidate_skills = [skill['description'] for skill in fetch_individual_skills(cursor_social, candidate_id)]
            if candidate_skills:  # This will be False for an empty list
                candidates_skills.append(' '.join(candidate_skills))
                valid_candidates.append(candidate)

        # 4. Compute TF-IDF vectors for the required skills and the skills of each candidate
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix_required_skills = tfidf_vectorizer.fit_transform([required_skills_string])
        tfidf_matrix_candidates = tfidf_vectorizer.transform(candidates_skills)

        # 5. Compute cosine similarity scores for each candidate based on the TF-IDF vectors
        cosine_similarities = cosine_similarity(tfidf_matrix_required_skills, tfidf_matrix_candidates).flatten()

        # 6. Sort candidates based on their similarity scores and return the top ones
        recommended_candidates = [candidate for _, candidate in
                                  sorted(zip(cosine_similarities, valid_candidates), key=lambda pair: pair[0],
                                         reverse=True)]

        # Enhance the data for each recommended candidate
        for candidate in recommended_candidates:
            individual_id = candidate['Id']
            candidate['Skills'] = fetch_individual_skills(cursor_social, individual_id)
            candidate['WorkExperience'] = fetch_individual_work_experiences(cursor_social, individual_id)
            candidate['Education'] = fetch_individual_educations(cursor_social, individual_id)

        return jsonify(recommended_candidates)

        return jsonify(recommended_candidates[:10])  # Return the top 10 candidates

    finally:
        cursor_social.close()
        conn_social.close()
        cursor_jobs.close()
        conn_jobs.close()


def get_average_word2vec(tokens_list, vector, generate_missing=False, k=300):
    """Get average word2vec for a list of tokens."""
    if len(tokens_list) < 1:
        return np.zeros(k)
    if generate_missing:
        vectorized = [vector[word] if word in vector else np.random.rand(k) for word in tokens_list]
    else:
        vectorized = [vector[word] if word in vector else np.zeros(k) for word in tokens_list]
    length = len(vectorized)
    summed = np.sum(vectorized, axis=0)
    averaged = np.divide(summed, length)
    return averaged



def is_irrelevant_job(job):
    """Check if a job post is irrelevant based on its title or description."""
    irrelevant_patterns = ["asdasdasdasd", "test test"]
    title = job.get("Title", "").lower()
    description = job.get("Description", "").lower()
    return any(pattern in title or pattern in description for pattern in irrelevant_patterns)


def compute_cosine_similarity(strings_individual, strings_jobs):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix_individual = tfidf_vectorizer.fit_transform(strings_individual)
    tfidf_matrix_jobs = tfidf_vectorizer.transform(strings_jobs)
    return cosine_similarity(tfidf_matrix_individual, tfidf_matrix_jobs).flatten()


# Utility functions for fetching data and computing similarity scores
def fetch_job_post(cursor, job_id):
    # Fetch the specific job post based on job_id
    cursor.execute("SELECT * FROM JobPosts WHERE Id = %s", (job_id,))
    return cursor.fetchone()


def fetch_data(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    result = cursor.fetchall()
    return result


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
            if key in item and item[key] is not None and isinstance(item[key], datetime):
                item[key] = item[key].strftime('%Y-%m-%d %H:%M:%S')

    return converted_data


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
        print("Column names", column_names)

        # Since result is already a dictionary, you can directly return it
        return result
    else:
        return None


def fetch_individual_data(cursor, user_id):
    # Fetch individual data based on user_id
    cursor.execute("SELECT * FROM Individuals WHERE Id = %s", (user_id,))
    return cursor.fetchone()


def fetch_individual_skills(cursor, individual_id):
    """Fetch skills of the individual based on individual_id along with proficiency level."""
    #print(f"Fetching skills for individual_id: {individual_id}")  # Debugging line
    cursor.execute("""
        SELECT s.Description, se.ProficiencyLevel 
        FROM vefacom_ProWorkSocial.SkillEvaluations se
        JOIN vefacom_ProWorkSocial.Skills s ON se.SkillId = s.Id
        WHERE se.IndividualId = %s
    """, (individual_id,))

    skills = [{"description": row['Description'], "proficiency_level": row['ProficiencyLevel']} for row in
              cursor.fetchall()]
    sorted_skills = sorted(skills, key=lambda x: x['proficiency_level'], reverse=True)

    print(f"Fetched skills: {sorted_skills}")  # Debugging line
    if len(sorted_skills) == 0:
        return []
    return sorted_skills


def fetch_individual_work_experiences(cursor, individual_id):
    """Fetch work experiences of the individual based on individual_id."""
    cursor.execute("""
        SELECT CompanyName, JobTitle, JobDescription, StartDate, EndDate 
        FROM vefacom_ProWorkSocial.WorkExperiences
        WHERE IndividualId = %s
    """, (individual_id,))

    work_experiences = cursor.fetchall()

    parsed_work_experiences = []
    for experience in work_experiences:
        job_title = experience['JobTitle']
        job_description = experience['JobDescription']

        # Calculate the time difference between EndDate and StartDate
        start_date = experience['StartDate']
        end_date = experience['EndDate']
        time_duration = (end_date - start_date).days  # This will give the difference in days

        parsed_work_experiences.append({
            "job_title": job_title,
            "job_description": job_description,
            "time_duration_days": time_duration
        })

    return parsed_work_experiences


def fetch_individual_educations(cursor, individual_id):
    """Fetch education details of the individual based on individual_id."""
    cursor.execute("""
        SELECT SchoolName, DegreeLevel, GPA 
        FROM vefacom_ProWorkSocial.Educations
        WHERE IndividualId = %s
    """, (individual_id,))

    educations = cursor.fetchall()

    parsed_educations = []
    for education in educations:
        school_name = education['SchoolName']
        degree_level = education['DegreeLevel']
        gpa = education['GPA']

        parsed_educations.append({
            "school_name": school_name,
            "degree_level": degree_level,
            "gpa": gpa
        })

    return parsed_educations


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


def compute_similarity_scores_for_candidates(cursor, job_post, candidates):
    # Compute similarity scores for candidates based on job post criteria
    # Placeholder logic
    required_skills = job_post['RequiredSkills'].split(', ')
    scores = []
    for candidate in candidates:
        candidate_skills = fetch_individual_skills(cursor, candidate['Id'])
        if candidate_skills != "No skills":
            matching_skills = set(candidate_skills).intersection(set(required_skills))
            scores.append(len(matching_skills))
    return scores


def sort_and_filter_candidates(candidates, scores):
    # Sort candidates based on scores and return the top ones
    sorted_candidates = [candidate for _, candidate in
                         sorted(zip(scores, candidates), key=lambda pair: pair[0], reverse=True)]
    return sorted_candidates[:10]


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("The app has started running!!!!")
