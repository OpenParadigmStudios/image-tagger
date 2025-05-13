FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Expose the default port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Command to run the application
# Note: Using 0.0.0.0 to bind to all interfaces in the container
ENTRYPOINT ["python", "main.py"]
CMD ["--host", "0.0.0.0"]
