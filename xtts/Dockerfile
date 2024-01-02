#
# AI model image
#
FROM python:3.11 AS image-model
RUN apt update
RUN apt install -y --no-install-recommends \
    git \
    git-lfs
RUN git lfs install
RUN git clone https://huggingface.co/coqui/XTTS-v2

#
# Python deps image
#
FROM python:3.11 AS image-build

RUN apt update
RUN apt install -y --no-install-recommends \
    build-essential \
    gcc \
    lame
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Download the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#
# Production image
#
FROM python:3.11

# App settings
ENV DEBUG False
WORKDIR /app
EXPOSE 5000
ENV COQUI_TOS_AGREED=1
ENV PYTHONUNBUFFERED=1

# Install dependencies from the build image venv
COPY --from=image-model /XTTS-v2/ /root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/
COPY --from=image-build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the app
COPY app.py .
COPY gunicorn_config.py .
COPY voices/*.wav .

# Run the app
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]