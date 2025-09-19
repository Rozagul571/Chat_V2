FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt

RUN apt-get update -y \
    && apt-get install -y \
       netcat \
       libgdal-dev \
       python3-gdal \
       libgl1 \
       libglib2.0-0 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*


COPY . /app/