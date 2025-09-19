FROM python:3.9-slim-bullseye

WORKDIR /app

# System deps
RUN apt-get update -y \
    && apt-get install -y \
       netcat \
       libgdal-dev \
       python3-gdal \
       libgl1 \
       libglib2.0-0 \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
