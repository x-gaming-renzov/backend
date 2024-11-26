# Use an official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ src/
COPY main.py main.py
COPY temp/ temp/
COPY gcreds.json gcreds.json
COPY workflow.png workflow.png
COPY streamlit_app.py streamlit_app.py
COPY .env .env

# Ensure dotenv is installed
RUN pip install python-dotenv

# Set environment variables dynamically at runtime
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

# Command to run the application
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
