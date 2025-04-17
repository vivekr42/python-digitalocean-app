# Use official Python image as a base
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (like ffmpeg for pydub)
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files to the container
COPY . .

# Expose the port for the application (should match the port in your script)
EXPOSE 80

# Set environment variable for Google API key (adjust based on how you pass it)
ENV GOOGLE_API_KEY=<your-google-api-key-here>

# Run the application
CMD ["python", "main.py"]
