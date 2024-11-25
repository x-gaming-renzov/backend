# Use an official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ src/
COPY main.py main.py
COPY temp/ temp/
COPY gcreds.json gcreds.json
COPY workflow.png workflow.png

# Ensure dotenv is installed
RUN pip install python-dotenv

# Set environment variables dynamically at runtime
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "main.py"]
