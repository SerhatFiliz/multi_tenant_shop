# Dockerfile

# Use an official Python runtime as a parent image
# 'slim-buster' is a lightweight version of the image, which is good practice.
FROM python:3.10-slim-buster

# Set environment variables to prevent Python from writing .pyc files
# and to run Python in unbuffered mode, which is better for container logs.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir makes the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project's code into the container at /app
COPY . .