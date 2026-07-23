FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for certificates
RUN mkdir -p /certs

# Generate self-signed certificate with explicit paths
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /certs/server.key \
    -out /certs/server.crt \
    -subj "/C=SG/ST=Singapore/L=Singapore/O=SIT/CN=127.0.0.1" \
    -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

# Verify certificates were created
RUN ls -la /certs/

# Copy application code
COPY app/ .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80 443

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]