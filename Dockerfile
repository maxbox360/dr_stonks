# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container
COPY . /code

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
