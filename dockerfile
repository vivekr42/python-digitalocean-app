# Set the working directory
WORKDIR /app

# Install dependencies (if any)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app files
COPY . .

# Run the Python app
CMD ["python3", "app.py"]
