FROM python:3.12-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure data and song_cache directories exist
RUN mkdir -p data song_cache

# Expose the application port
EXPOSE 499

# Run the application
CMD ["python", "app.py"]
