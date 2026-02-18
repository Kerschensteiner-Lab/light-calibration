# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (includes gunicorn from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application with gunicorn
CMD exec gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
