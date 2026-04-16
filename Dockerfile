# -------------------------
# Base image
# -------------------------
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -------------------------
# System dependencies
# -------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    unzip \
    libcairo2 \
    libcairo-gobject2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    libfribidi0 \
    libjpeg62-turbo \
    libopenjp2-7 \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-freefont-ttf \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# -------------------------
# Copy project code
# -------------------------
COPY . .

# -------------------------
# Download models
# -------------------------
# RUN mkdir -p /app/models && \
#     wget https://github.com/chaindmhl/EXIM/releases/download/v1.0/model1.zip -O /tmp/model1.zip && \
#     unzip /tmp/model1.zip -d /app/models && \
#     wget https://github.com/chaindmhl/EXIM/releases/download/v1.0/model2.zip -O /tmp/model2.zip && \
#     unzip /tmp/model2.zip -d /app/models && \
#     rm -rf /tmp/model1.zip /tmp/model2.zip



# -------------------------
# Entrypoint
# -------------------------
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh


ENTRYPOINT ["/app/entrypoint.sh"]
