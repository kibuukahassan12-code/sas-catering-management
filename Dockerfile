FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (build-essential for compiling Python packages, sqlite3 for database)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 10000

# Start application directly with Python (no gunicorn, no Python version guessing)
CMD ["python", "sas_management/app.py"]

