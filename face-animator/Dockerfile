#
# AI model image
#
FROM continuumio/miniconda3 AS image-model
WORKDIR /model
RUN apt update
RUN apt install -y --no-install-recommends \
    wget \
    git

# Set environment variable to prevent Conda from changing the prompt
ENV CONDA_CHANGEPS1=false
SHELL ["/bin/bash", "-c"]

# Repository
RUN git clone https://github.com/OpenTalker/SadTalker.git && \
    cd SadTalker && \
    rm -rf .git && \
    conda init bash && \
    . ~/.bashrc && \
    conda create -n sadtalker python=3.8 && \
    conda init bash && \
    conda activate sadtalker && \
    pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113 && \
    conda install ffmpeg && \
    pip install -r requirements.txt

# Model data
RUN mkdir -p ./checkpoints ./gfpgan/weights && \
    wget -nc https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar -O ./checkpoints/mapping_00109-model.pth.tar && \
    wget -nc https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar -O ./checkpoints/mapping_00229-model.pth.tar && \
    wget -nc https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors -O ./checkpoints/SadTalker_V0.0.2_256.safetensors && \
    wget -nc https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors -O ./checkpoints/SadTalker_V0.0.2_512.safetensors && \
    wget -nc https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth -O ./gfpgan/weights/alignment_WFLW_4HG.pth && \
    wget -nc https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth -O ./gfpgan/weights/detection_Resnet50_Final.pth && \
    wget -nc https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth -O ./gfpgan/weights/GFPGANv1.4.pth && \
    wget -nc https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth -O ./gfpgan/weights/parsing_parsenet.pth



#
# Dependencies image
#
FROM python:3.8 AS image-dependencies
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
FROM python:3.8
WORKDIR /face-animator
EXPOSE 5000
ENV DEBUG False
ENV PYTHONUNBUFFERED=0

# Install the model
COPY --from=image-model /model/SadTalker ./SadTalker

# Install the venv
COPY --from=image-dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install conda
COPY --from=image-model /opt/conda /opt/conda
ENV PATH="/opt/conda/bin:$PATH"

# Install the app
COPY app.py .
COPY gunicorn_config.py .
COPY faces .
COPY faces/*.png faces/

# Run the app
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]