FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
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



# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

RUN mkdir -p /models/model1 /models/model2 && \
    wget https://github.com/chaindmhl/EXIM/releases/download/v1.0/model1.zip \
        -O /models/model1.zip && \
    unzip /models/model1.zip -d /models/model1 && \
    rm /models/model1.zip && \
    wget https://github.com/chaindmhl/EXIM/releases/download/v1.0/model2.zip \
        -O /models/model2.zip && \
    unzip /models/model2.zip -d /models/model2 && \
    rm /models/model2.zip

# Entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
