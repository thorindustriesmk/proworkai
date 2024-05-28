FROM python:3.9

# Install freetds-dev package
RUN apt-get update && apt-get install -y freetds-dev

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies using pip
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set the entrypoint command
#ENTRYPOINT FLASK_APP=/app/app.py flask run --host=0.0.0.0

# Specify the command to run on container start
CMD ["flask", "run", "--host=0.0.0.0"]
