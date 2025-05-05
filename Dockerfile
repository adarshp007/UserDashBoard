FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=userdashboard.settings

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Create directories for temporary files and media uploads
RUN mkdir -p /app/tmp /app/media/uploads
RUN chmod -R 777 /app/tmp /app/media /app/scripts

# Make entrypoint script executable
RUN chmod +x /app/scripts/entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Run the command to start uWSGI
CMD ["gunicorn", "userdashboard.wsgi:application", "--bind", "0.0.0.0:8000"]
