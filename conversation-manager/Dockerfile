#
# Dependencies image
#
FROM python:3.11 AS image-dependencies
WORKDIR /dependencies
RUN apt update
RUN apt install -y --no-install-recommends \
    build-essential \
    gcc

# Create the Python venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Download the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



#
# Production image
#
FROM python:3.11
WORKDIR /face-animator
EXPOSE 5000
ENV DEBUG False
ENV PYTHONUNBUFFERED=0

# Install the venv
COPY --from=image-dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the app
COPY app.py .
COPY gunicorn_config.py .
COPY faces .
COPY faces/*.png faces/

# Run the app
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]