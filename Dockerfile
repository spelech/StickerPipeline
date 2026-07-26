FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for OpenCV, rembg, reportlab, and image rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY pyproject.toml /app/
COPY README.md /app/

EXPOSE 8460

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8460"]
