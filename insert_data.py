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
