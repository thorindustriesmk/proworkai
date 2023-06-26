FROM continuumio/miniconda3:latest

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies using conda and pip
RUN conda create --name myenv python=3.9 && \
    echo "source activate myenv" > ~/.bashrc && \
    conda install --name myenv --yes --file requirements.txt && \
    conda install --name myenv --yes -c conda-forge pymssql
# Copy the application code
COPY . .

# Set the entrypoint command
ENTRYPOINT ["python", "app.py"]
