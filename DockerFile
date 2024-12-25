# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install build tools and necessary system dependencies
RUN apk update && \
    apk add --no-cache curl  # Optional: Remove if not needed

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r <(grep -v "^flask==" requirements.txt | grep -v "^werkzeug==") && \
    pip install --no-cache-dir flask werkzeug

# Create directory and set permissions (assuming user 1000 runs the container)
RUN mkdir -p /app && chown -R 1000:1000 /app

# Expose port 5001 to the outside world
EXPOSE 5001

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run flask when the container launches
CMD ["python", "app.py"]
