# Dockerfile
FROM python:3.10-slim

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential ffmpeg libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy project (assumes you will build from a context that contains ComfyUI folder)
COPY . /app

# Install Python requirements for ComfyUI (the project has requirements.txt)
RUN pip install --upgrade pip
RUN if [ -f /app/ComfyUI/requirements.txt ]; then pip install -r /app/ComfyUI/requirements.txt; fi

# Install runpod worker SDK only if needed (not required if using raw rp_handler convention)
# RUN pip install runpod

ENV PYTHONUNBUFFERED=1
ENV COMFYUI_ROOT=/app/ComfyUI

# Ensure models path used in your ComfyUI is where the network volume will be mounted.
# We'll rely on Runpod to mount the network volume into /workspace/runpod-slim/ComfyUI/models

# Expose nothing in particular. Entrypoint runs the rp_handler expected by Runpod template.
# The runpod worker runtime will call rp_handler.handler; if you use another entrypoint,
# adapt the Runpod worker settings.
CMD ["python", "/app/rp_handler.py"]
