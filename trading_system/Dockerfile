FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with verbose output
RUN pip install --no-cache-dir --verbose -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for persistent database storage
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Start the application
CMD ["python", "start_api.py"]