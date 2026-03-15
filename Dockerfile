FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        git \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd for web-based terminal access
RUN wget -qO /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.$(dpkg --print-architecture) && \
    chmod +x /usr/local/bin/ttyd

WORKDIR /app

# Copy dependency files first for better layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package itself
RUN pip install --no-cache-dir -e .

# Railway provides PORT env var; default to 8080
ENV PORT=8080

# Run ttyd serving the CLI
# --writable allows user input
# -t fontSize=16 sets readable font size
# -t theme='{"background":"#1a1b26"}' dark theme
CMD ttyd \
    --port ${PORT} \
    --writable \
    -t fontSize=16 \
    -t 'theme={"background":"#1a1b26","foreground":"#c0caf5"}' \
    python -m cli.main
