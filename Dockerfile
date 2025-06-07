# Use Python 3.10.16 slim image to match your local version
FROM python:3.10.16-slim

# Set working directory inside container
WORKDIR /app

# Set Python environment variables (from search results best practices)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# Copy requirements file first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy your entire search engine application code
COPY . .

# Create data directory for SQLite database and cache files
RUN mkdir -p /app/data

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run your FastAPI search engine
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
