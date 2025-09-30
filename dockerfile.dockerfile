# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose default port (adjust if your app uses a different port)
EXPOSE 5000

# Command to run your app (adjust filename if needed)
CMD ["python", "app.py"]
